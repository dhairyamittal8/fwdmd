#!/usr/bin/env python3
"""PUBHEALTH veracity evaluation: DIRECT vs PIPELINE prompting on a 200-claim test sample.

Usage:
    export ANTHROPIC_API_KEY=...            # or any credential the anthropic SDK resolves
    export CLAUDE_MODEL=claude-opus-5-5     # optional; this is the default
    python run_pubhealth.py --n 10          # smoke test (subset of the 200-claim sample)
    python run_pubhealth.py                 # full 200

Every API response is appended to eval/cache.jsonl, so reruns cost nothing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CACHE_PATH = HERE / "cache.jsonl"
SAMPLE_PATH = HERE / "sample_ids.json"

LABELS = ["false", "mixture", "true", "unproven"]  # index == PUBHEALTH label id
SEED = 42
SAMPLE_N = 200
MAX_WORDS = 1500
PROMPT_VERSION = "v1"
DEFAULT_MODEL = "claude-opus-5-5"

# USD per million tokens (input, output). First-party API list prices, Nov 2026.
PRICES = {
    "claude-fable-5-2": (8.0, 40.0),
    "claude-fable-5-1": (10.0, 50.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-5-5": (0.1, 0.5),
    "claude-haiku-4-5": (1.0, 5.0),
}

BASELINES = [
    # (system, source, macro-F1, accuracy)
    ("Majority class", "Kotonya & Toni 2020 test split", None, 48.6),
    ("SciBERT (fine-tuned)", "Kotonya & Toni 2020", 70.52, 69.73),
    ("GPT-3.5-turbo zero-shot", "Zarharan et al. 2024", 51.4, None),
    ("GPT-4 zero-shot", "Zarharan et al. 2024", 53.2, 67.5),
    ("Mistral-7B PEFT (fine-tuned)", "Zarharan et al. 2024", 72.0, 82.3),
]

LABEL_GUIDE = """Labels (PUBHEALTH scheme):
- true: the claim is accurate and supported by the evidence.
- false: the claim is inaccurate or contradicted by the evidence.
- mixture: the claim is partly accurate and partly inaccurate, or accurate but misleading or missing important context.
- unproven: there is not enough evidence to establish whether the claim is accurate."""

DIRECT_PROMPT = """You are fact-checking a public-health claim against the article text below.

{guide}

Claim: {claim}

Article text:
<article>
{text}
</article>

Classify the claim. Respond with JSON only: {{"label": "<true|false|mixture|unproven>"}}"""

PIPELINE_PROMPT = """You are fact-checking a public-health claim against the article text below. Work through the steps in order, then give your verdict.

{guide}

Claim: {claim}

Article text:
<article>
{text}
</article>

Steps:
1. key_assertion: restate the single checkable assertion the claim makes.
2. evidence_for: the strongest evidence in the article supporting the assertion (or "none").
3. evidence_against: the strongest evidence in the article contradicting or qualifying it (or "none").
4. evidence_assessment: weigh the two and say how well the article settles the assertion.
5. abstain: true if the article's evidence is insufficient for you to commit to a label, otherwise false. Abstaining is separate from the "unproven" label: "unproven" is a verdict that the claim itself lacks evidence; abstain means you cannot tell which label applies.
6. best_guess_label: your single best label, required even if you abstain.
7. confidence: probability from 0 to 1 that best_guess_label is correct.

Respond with JSON only, with exactly these keys in this order: key_assertion, evidence_for, evidence_against, evidence_assessment, abstain, best_guess_label, confidence."""

DIRECT_SCHEMA = {
    "type": "object",
    "properties": {"label": {"type": "string", "enum": LABELS}},
    "required": ["label"],
    "additionalProperties": False,
}
PIPELINE_SCHEMA = {
    "type": "object",
    "properties": {
        "key_assertion": {"type": "string"},
        "evidence_for": {"type": "string"},
        "evidence_against": {"type": "string"},
        "evidence_assessment": {"type": "string"},
        "abstain": {"type": "boolean"},
        "best_guess_label": {"type": "string", "enum": LABELS},
        "confidence": {"type": "number"},
    },
    "required": ["key_assertion", "evidence_for", "evidence_against", "evidence_assessment",
                 "abstain", "best_guess_label", "confidence"],
    "additionalProperties": False,
}
CONDITIONS = {
    "direct": (DIRECT_PROMPT, DIRECT_SCHEMA),
    "pipeline": (PIPELINE_PROMPT, PIPELINE_SCHEMA),
}


# ----------------------------------------------------------------------------- data

def load_test_split() -> tuple[pd.DataFrame, str]:
    """Return the PUBHEALTH test split and a note describing how it was obtained."""
    try:
        from datasets import load_dataset
        ds = load_dataset("ImperialCollegeLondon/health_fact", split="test", trust_remote_code=True)
        df = ds.to_pandas()
        note = "Hugging Face ImperialCollegeLondon/health_fact (loading script, trust_remote_code=True)"
    except Exception as e:  # noqa: BLE001 - any loader failure triggers the documented fallback
        print(f"[data] Hugging Face load failed ({type(e).__name__}: {str(e)[:200]}); "
              "falling back to the authors' TSV archive", file=sys.stderr)
        df = _load_from_authors_archive()
        note = ("Fallback: PUBHEALTH.zip linked from github.com/neemakot/Health-Fact-Checking "
                f"(Google Drive), test.tsv. HF load error: {type(e).__name__}")
    df = df[df["label"] != -1].copy()
    df["claim_id"] = df["claim_id"].astype(str)
    df["label"] = df["label"].astype(int)
    return df.reset_index(drop=True), note


def _load_from_authors_archive() -> pd.DataFrame:
    """The authors' GitHub repo holds no data files; its README and download_data.sh point to
    this Google Drive archive (PUBHEALTH.zip with train/dev/test.tsv)."""
    import io
    import urllib.request
    import zipfile
    file_id = "1eTtRs5cUlBP5dXsx-FTAlmXuB6JQi2qj"
    url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    raw = urllib.request.urlopen(url, timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = next(n for n in z.namelist() if n.endswith("test.tsv"))
        df = pd.read_csv(z.open(name), sep="\t", dtype=str, keep_default_na=False)
    df["label"] = df["label"].map({l: i for i, l in enumerate(LABELS)}).fillna(-1).astype(int)
    return df


def get_sample(df: pd.DataFrame) -> pd.DataFrame:
    """Stratified 200-claim sample, seed 42. sample_ids.json is the source of truth once written."""
    if SAMPLE_PATH.exists():
        ids = json.loads(SAMPLE_PATH.read_text())["claim_ids"]
    else:
        picked, _ = train_test_split(df, train_size=SAMPLE_N, stratify=df["label"], random_state=SEED)
        ids = sorted(picked["claim_id"].tolist())
        SAMPLE_PATH.write_text(json.dumps({
            "dataset": "ImperialCollegeLondon/health_fact", "split": "test", "seed": SEED,
            "n": len(ids), "method": "sklearn train_test_split(stratify=label, random_state=42)",
            "claim_ids": ids}, indent=1) + "\n")
    by_id = df.drop_duplicates("claim_id").set_index("claim_id")
    missing = [i for i in ids if i not in by_id.index]
    if missing:
        sys.exit(f"sample_ids.json has {len(missing)} ids not in the test split, e.g. {missing[:3]}")
    return by_id.loc[ids].reset_index()


def smoke_subset(sample: pd.DataFrame, n: int) -> pd.DataFrame:
    """Stratified subset of the fixed sample, so smoke-test calls are reused by the full run."""
    if n >= len(sample):
        return sample
    try:
        sub, _ = train_test_split(sample, train_size=n, stratify=sample["label"], random_state=SEED)
    except ValueError:  # n too small to stratify
        sub = sample.sample(n=n, random_state=SEED)
    return sub.sort_values("claim_id").reset_index(drop=True)


def truncate(text: str) -> str:
    return " ".join(str(text).split()[:MAX_WORDS])


# ----------------------------------------------------------------------------- API + cache

class Runner:
    def __init__(self, model: str, dry_run: bool = False):
        self.model = model
        self.dry_run = dry_run
        self.lock = threading.Lock()
        self.cache: dict[str, dict] = {}
        self.dropped_params: set[str] = set()   # request params this model rejects
        self.new_cost = 0.0
        self.cached_cost = 0.0
        self.new_calls = 0
        self.cache_hits = 0
        if CACHE_PATH.exists() and not dry_run:
            for line in CACHE_PATH.read_text().splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.cache[rec["key"]] = rec
        if not dry_run:
            import anthropic
            self.anthropic = anthropic
            # Retries are handled below so that waits are visible and honour retry-after.
            self.client = anthropic.Anthropic(max_retries=0, timeout=300.0)

    def cost(self, usage: dict) -> float:
        pin, pout = PRICES.get(self.model, (0.0, 0.0))
        return (usage.get("input_tokens", 0) * pin + usage.get("output_tokens", 0) * pout) / 1e6

    def call(self, condition: str, claim_id: str, prompt: str, schema: dict) -> dict:
        key = hashlib.sha256(
            json.dumps([self.model, condition, PROMPT_VERSION, claim_id, prompt]).encode()).hexdigest()
        with self.lock:
            hit = self.cache.get(key)
            if hit:
                self.cache_hits += 1
                self.cached_cost += self.cost(hit["usage"])
                return hit
        rec = self._fake(condition, claim_id) if self.dry_run else self._request(prompt, schema)
        rec.update(key=key, model=self.model, condition=condition, claim_id=claim_id,
                   prompt_version=PROMPT_VERSION, ts=time.time())
        with self.lock:
            self.cache[key] = rec
            self.new_calls += 1
            self.new_cost += self.cost(rec["usage"])
            if not self.dry_run:
                with CACHE_PATH.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
        return rec

    def _request(self, prompt: str, schema: dict) -> dict:
        a = self.anthropic
        attempt = 0
        while True:
            kwargs: dict = {"model": self.model, "max_tokens": 4096,
                            "messages": [{"role": "user", "content": prompt}]}
            if "output_config" not in self.dropped_params:
                kwargs["output_config"] = {"format": {"type": "json_schema", "schema": schema}}
            try:
                r = self.client.messages.create(**kwargs)
                break
            except a.BadRequestError as e:
                # Current models reject sampling params; older ones may lack structured outputs.
                # Drop the offending optional param once and retry; anything else is fatal.
                msg = str(e).lower()
                culprit = next((p for p in ("temperature", "output_config")
                                if p in kwargs and p in msg), None)
                if culprit is None:
                    raise
                with self.lock:
                    if culprit not in self.dropped_params:
                        print(f"[api] {self.model} rejected `{culprit}`; continuing without it")
                        self.dropped_params.add(culprit)
            except a.RateLimitError as e:
                attempt += 1
                self._backoff(attempt, e.response.headers.get("retry-after"), "rate limited (429)")
            except a.APIStatusError as e:
                if e.status_code < 500 and e.status_code not in (408, 409):
                    raise
                attempt += 1
                self._backoff(attempt, e.response.headers.get("retry-after"), f"HTTP {e.status_code}")
            except a.APIConnectionError:
                attempt += 1
                self._backoff(attempt, None, "connection error")
        text = "".join(b.text for b in r.content if b.type == "text")
        return {"text": text, "stop_reason": r.stop_reason, "served_model": r.model,
                "temperature_sent": "temperature" in kwargs,
                "usage": {"input_tokens": r.usage.input_tokens, "output_tokens": r.usage.output_tokens}}

    @staticmethod
    def _backoff(attempt: int, retry_after: str | None, why: str) -> None:
        if attempt > 8:
            raise RuntimeError(f"giving up after {attempt - 1} retries ({why})")
        try:
            delay = float(retry_after) if retry_after else 0.0
        except ValueError:
            delay = 0.0
        delay = max(delay, min(60.0, 2.0 ** attempt)) + random.uniform(0, 1)
        print(f"[api] {why}; retry {attempt}/8 in {delay:.1f}s")
        time.sleep(delay)

    def _fake(self, condition: str, claim_id: str) -> dict:
        """--dry-run only: deterministic pseudo-random answers to exercise the plumbing."""
        rng = random.Random(f"{condition}:{claim_id}")
        label = rng.choice(LABELS)
        if condition == "direct":
            out = {"label": label}
        else:
            out = {"key_assertion": "x", "evidence_for": "x", "evidence_against": "x",
                   "evidence_assessment": "x", "abstain": rng.random() < 0.15,
                   "best_guess_label": label, "confidence": round(rng.random(), 2)}
        return {"text": json.dumps(out), "stop_reason": "end_turn", "served_model": "dry-run",
                "temperature_sent": False, "usage": {"input_tokens": 0, "output_tokens": 0}}


def parse(condition: str, rec: dict) -> dict:
    """Extract label (+ abstain, confidence). Unparseable or refused outputs get label 'invalid'."""
    out = {"label": "invalid", "abstain": None, "confidence": None}
    m = re.search(r"\{.*\}", rec.get("text") or "", re.S)
    if not m:
        return out
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return out
    label = str(d.get("label" if condition == "direct" else "best_guess_label", "")).strip().lower()
    if label in LABELS:
        out["label"] = label
    if condition == "pipeline":
        out["abstain"] = bool(d.get("abstain", False))
        try:
            out["confidence"] = min(1.0, max(0.0, float(d.get("confidence"))))
        except (TypeError, ValueError):
            out["confidence"] = 0.0
        out["key_assertion"] = d.get("key_assertion")
    return out


# ----------------------------------------------------------------------------- metrics

def classification_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    """Metrics over the four gold classes. 'invalid' predictions count as errors."""
    per_class = f1_score(y_true, y_pred, labels=LABELS, average=None, zero_division=0)
    return {
        "n": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
        "per_class_f1": {l: float(v) for l, v in zip(LABELS, per_class)},
        "confusion_matrix": {
            "labels": LABELS + ["invalid"],
            "note": "rows = gold, columns = predicted",
            "matrix": confusion_matrix(y_true, y_pred, labels=LABELS + ["invalid"])[:4].tolist(),
        },
        "n_invalid": sum(p == "invalid" for p in y_pred),
    }


def coverage_curve(rows: list[dict]) -> dict:
    """Selective prediction for PIPELINE. A claim is answered at threshold t if confidence >= t
    (confidence-only) and additionally abstain is false (confidence + abstain flag)."""
    n = len(rows)
    thresholds = sorted({0.0} | {round(r["confidence"] or 0.0, 4) for r in rows})

    def points(use_flag: bool) -> list[dict]:
        pts = []
        for t in thresholds:
            kept = [r for r in rows if (r["confidence"] or 0.0) >= t and not (use_flag and r["abstain"])]
            if kept:
                pts.append({"threshold": t, "coverage": len(kept) / n, "n_answered": len(kept),
                            "accuracy": sum(r["correct"] for r in kept) / len(kept)})
        return pts

    answered = [r for r in rows if not r["abstain"]]
    abstained = [r for r in rows if r["abstain"]]
    return {
        "confidence_only": points(False),
        "confidence_and_abstain_flag": points(True),
        "abstain_flag_only": {
            "n_abstained": len(abstained),
            "coverage": len(answered) / n if n else 0.0,
            "accuracy_answered": sum(r["correct"] for r in answered) / len(answered) if answered else None,
            "accuracy_abstained_forced_guess":
                sum(r["correct"] for r in abstained) / len(abstained) if abstained else None,
        },
    }


# ----------------------------------------------------------------------------- outputs

def write_charts(results: dict, out_dir: Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    ink, accent, accent2 = "#1f2933", "#2563eb", "#9aa5b1"
    files = []

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), constrained_layout=True)
    for ax, cond in zip(axes, ("direct", "pipeline")):
        m = results["conditions"][cond]
        cm = m["confusion_matrix"]["matrix"]
        cols = m["confusion_matrix"]["labels"] if m["n_invalid"] else LABELS
        data = [row[:len(cols)] for row in cm]
        vmax = max(max(r) for r in data) or 1
        ax.imshow(data, cmap="Blues", vmin=0, vmax=vmax)
        for i, row in enumerate(data):
            for j, v in enumerate(row):
                ax.text(j, i, str(v), ha="center", va="center", fontsize=11,
                        color="white" if v > vmax * 0.55 else ink)
        ax.set_xticks(range(len(cols)), cols)
        ax.set_yticks(range(4), LABELS)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Gold")
        ax.set_title(f"{cond.upper()}  ·  acc {m['accuracy']:.1%}  ·  macro-F1 {m['macro_f1']:.1%}",
                     fontsize=11, color=ink)
    fig.suptitle(f"PUBHEALTH confusion matrices (n={results['n']}, {results['model']})", color=ink)
    fig.savefig(out_dir / "confusion_matrix.png", dpi=160)
    plt.close(fig)
    files.append("confusion_matrix.png")

    cov = results["coverage_curve"]
    fig, ax = plt.subplots(figsize=(7, 4.6), constrained_layout=True)
    for key, label, color, style in (
            ("confidence_only", "Confidence threshold only", accent2, "--"),
            ("confidence_and_abstain_flag", "Confidence threshold + abstain flag", accent, "-")):
        pts = sorted(cov[key], key=lambda p: p["coverage"])
        ax.plot([p["coverage"] for p in pts], [p["accuracy"] for p in pts],
                style, marker="o", ms=3.5, lw=1.8, color=color, label=label)
    ax.axhline(results["conditions"]["direct"]["accuracy"], color=ink, lw=1, ls=":",
               label="DIRECT accuracy (full coverage)")
    ax.set_xlabel("Coverage (share of claims answered)")
    ax.set_ylabel("Accuracy on answered claims")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower left")
    ax.set_title(f"PIPELINE coverage vs accuracy (n={results['n']})", color=ink)
    fig.savefig(out_dir / "coverage_curve.png", dpi=160)
    plt.close(fig)
    files.append("coverage_curve.png")
    return files


def pct(v: float | None) -> str:
    if v is None:
        return "–"
    return f"{v:.1f}" if round(v, 1) == v else f"{v:.2f}"


def write_markdown(results: dict, path: Path) -> None:
    c = results["conditions"]
    n, model = results["n"], results["model"]
    L = [f"# PUBHEALTH veracity evaluation ({n}-claim sample)", "",
         f"Model: `{model}` · sample: {n} test claims, stratified, seed {SEED} "
         f"(`eval/sample_ids.json`) · prompts {PROMPT_VERSION} · generated {results['generated_at']}", "",
         "## Our results next to published baselines", "",
         "| System | Source | Test set | Macro-F1 | Accuracy |", "|---|---|---|---:|---:|"]
    for cond, name in (("direct", "DIRECT (zero-shot, one label)"),
                       ("pipeline", "PIPELINE (extract → weigh → forced label)")):
        L.append(f"| **{name}, {model}** | this repo | {n}-claim sample | "
                 f"**{c[cond]['macro_f1'] * 100:.1f}** | **{c[cond]['accuracy'] * 100:.1f}** |")
    for name, src, f1, acc in BASELINES:
        L.append(f"| {name} | {src} | as reported in the paper | {pct(f1)} | {pct(acc)} |")
    L += ["", "Baseline figures are quoted from the cited papers, not re-run here. "
              "– means the figure was not supplied.", "",
          "## Per-class F1", "", "| Condition | " + " | ".join(LABELS) + " |", "|---|" + "---:|" * 4]
    for cond in ("direct", "pipeline"):
        L.append(f"| {cond.upper()} | " +
                 " | ".join(f"{c[cond]['per_class_f1'][l] * 100:.1f}" for l in LABELS) + " |")
    L += ["", "Gold label counts in the sample: " +
          ", ".join(f"{l} {results['label_counts'][l]}" for l in LABELS) + ".", ""]
    for cond in ("direct", "pipeline"):
        cm = c[cond]["confusion_matrix"]
        L += [f"## Confusion matrix: {cond.upper()}", "", "Rows are gold labels, columns are predictions.", "",
              "| gold \\ pred | " + " | ".join(cm["labels"]) + " |", "|---|" + "---:|" * len(cm["labels"])]
        L += [f"| {LABELS[i]} | " + " | ".join(map(str, row)) + " |" for i, row in enumerate(cm["matrix"])]
        L.append("")
    cov = results["coverage_curve"]
    af = cov["abstain_flag_only"]
    L += ["## PIPELINE: coverage vs accuracy", "",
          f"The model set the abstain flag on {af['n_abstained']} of {n} claims "
          f"(coverage {af['coverage']:.1%}). Accuracy on the claims it answered: "
          f"{'–' if af['accuracy_answered'] is None else format(af['accuracy_answered'], '.1%')}; "
          "accuracy of its forced guesses on the claims it abstained on: "
          f"{'–' if af['accuracy_abstained_forced_guess'] is None else format(af['accuracy_abstained_forced_guess'], '.1%')}.",
          "", "Answered = abstain flag false and confidence ≥ threshold.", "",
          "| Confidence ≥ | Coverage | Answered | Accuracy on answered |", "|---:|---:|---:|---:|"]
    for p in cov["confidence_and_abstain_flag"]:
        L.append(f"| {p['threshold']:.2f} | {p['coverage']:.1%} | {p['n_answered']} | {p['accuracy']:.1%} |")
    L += ["", "Charts: `public/eval/confusion_matrix.png`, `public/eval/coverage_curve.png`.", "",
          "## Caveats: these results are indicative only", "",
          f"- **Small sample.** {n} claims, not the full 1,233-claim labelled test split. The 95% interval "
          f"on an accuracy near 70% at n={n} is roughly ±6 points, and the `unproven` class has only "
          f"{results['label_counts']['unproven']} claims, so its F1 (and therefore macro-F1) is noisy.",
          "- **Different test sets across papers.** Kotonya & Toni report on the full test split; "
          "Zarharan et al. use their own evaluation setup and split sizes. None of the baseline rows "
          "were scored on our 200 claims, so differences of a few points mean nothing.",
          f"- **Different evidence context.** We give the model the fact-check article's full `main_text`, "
          f"truncated to the first {MAX_WORDS:,} words. Published systems variously use selected top-k "
          "evidence sentences or summarised/explanation text. The full article often states the verdict "
          "outright, which makes our setting easier.",
          "- **Zero-shot vs fine-tuned.** SciBERT and Mistral-7B PEFT were trained on PUBHEALTH; our runs "
          "and the GPT rows are zero-shot.",
          "- **Possible training-data exposure.** PUBHEALTH has been public since 2020, so the model may "
          "have seen these claims and their verdicts.",
          f"- **Sampling temperature.** {results['temperature_note']}",
          "- **Single run.** One run per condition, no repeated sampling or significance test between "
          "DIRECT and PIPELINE.", "",
          "## Reproduce", "", "```bash", "cd eval", "uv venv && uv pip install -r requirements.txt",
          "export ANTHROPIC_API_KEY=...  CLAUDE_MODEL=" + model,
          ".venv/bin/python run_pubhealth.py --n 10   # smoke test",
          ".venv/bin/python run_pubhealth.py          # full 200 (cached calls are free)", "```", "",
          f"Data source: {results['data_source']}.", ""]
    path.write_text("\n".join(L))


# ----------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=SAMPLE_N, help="claims to run (subset of the fixed sample)")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true",
                    help="no API calls; random answers; outputs go to eval/dry_run/ only")
    args = ap.parse_args()

    model = os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL)
    full = args.n >= SAMPLE_N and not args.dry_run
    out_dir = HERE if full else HERE / ("dry_run" if args.dry_run else "smoke")
    chart_dir = out_dir  # kept inside eval/; copy to public/eval later
    out_dir.mkdir(exist_ok=True)

    df, data_note = load_test_split()
    sample = get_sample(df)
    run_df = smoke_subset(sample, args.n)
    counts = {LABELS[k]: int(v) for k, v in run_df["label"].value_counts().sort_index().items()}
    print(f"[data] {data_note}\n[data] test split {len(df)} labelled claims; sample {len(sample)}; "
          f"running {len(run_df)} {counts}\n[run] model={model} dry_run={args.dry_run}")
    if model not in PRICES:
        print(f"[cost] no price entry for {model}; cost estimate will read $0")

    runner = Runner(model, dry_run=args.dry_run)
    jobs = []
    for row in run_df.itertuples(index=False):
        text = truncate(row.main_text)
        for cond, (template, schema) in CONDITIONS.items():
            jobs.append((cond, row.claim_id,
                         template.format(guide=LABEL_GUIDE, claim=row.claim, text=text), schema))

    recs: dict[tuple[str, str], dict] = {}
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(runner.call, c, cid, p, s): (c, cid) for c, cid, p, s in jobs}
        for fut in as_completed(futures):
            recs[futures[fut]] = fut.result()
            done += 1
            if done % 10 == 0 or done == len(jobs):
                print(f"[run] {done}/{len(jobs)} calls · {runner.cache_hits} cached · "
                      f"spent this run ${runner.new_cost:.3f} · "
                      f"total incl. cache ${runner.new_cost + runner.cached_cost:.3f}")

    rows = []
    for row in run_df.itertuples(index=False):
        gold = LABELS[row.label]
        d = parse("direct", recs[("direct", row.claim_id)])
        p = parse("pipeline", recs[("pipeline", row.claim_id)])
        rows.append({"claim_id": row.claim_id, "claim": row.claim, "gold": gold,
                     "direct": d["label"], "pipeline": p["label"], "abstain": bool(p["abstain"]),
                     "confidence": p["confidence"] if p["confidence"] is not None else 0.0,
                     "direct_correct": d["label"] == gold, "correct": p["label"] == gold,
                     "key_assertion": p.get("key_assertion")})

    y = [r["gold"] for r in rows]
    temp_sent = all(r.get("temperature_sent") for r in recs.values())
    results = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "model": model,
        "served_models": sorted({r.get("served_model") for r in recs.values()}),
        "dataset": "PUBHEALTH (ImperialCollegeLondon/health_fact), test split",
        "data_source": data_note,
        "seed": SEED, "n": len(rows), "max_words": MAX_WORDS, "prompt_version": PROMPT_VERSION,
        "dry_run": args.dry_run,
        "temperature_note": (
            "temperature=0 was sent on every request." if temp_sent else
            "No temperature parameter was sent (model default sampling); outputs are not guaranteed "
            "deterministic (the cache makes reruns reproducible)."),
        "label_counts": {l: y.count(l) for l in LABELS},
        "conditions": {"direct": classification_metrics(y, [r["direct"] for r in rows]),
                       "pipeline": classification_metrics(y, [r["pipeline"] for r in rows])},
        "coverage_curve": coverage_curve(rows),
        "baselines": [{"system": s, "source": src, "macro_f1": f1, "accuracy": acc}
                      for s, src, f1, acc in BASELINES],
        "cost_usd_estimate": round(runner.new_cost + runner.cached_cost, 4),
        "predictions": rows,
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=1) + "\n")
    write_charts(results, chart_dir)
    write_markdown(results, out_dir / "RESULTS.md")

    print("\n=== Summary ===")
    for cond in ("direct", "pipeline"):
        m = results["conditions"][cond]
        print(f"{cond.upper():9s} acc {m['accuracy']:.3f}  macro-F1 {m['macro_f1']:.3f}  per-class "
              + " ".join(f"{l}={v:.2f}" for l, v in m["per_class_f1"].items())
              + f"  invalid={m['n_invalid']}")
    af = results["coverage_curve"]["abstain_flag_only"]
    print(f"PIPELINE abstained on {af['n_abstained']}/{len(rows)}; "
          f"accuracy on answered: {af['accuracy_answered']}")
    print(f"API calls: {runner.new_calls} new, {runner.cache_hits} cached · "
          f"cost this run ${runner.new_cost:.3f} · total incl. cache ${results['cost_usd_estimate']:.3f}")
    print(f"Wrote {out_dir / 'results.json'}, {out_dir / 'RESULTS.md'}, charts in {chart_dir}")


if __name__ == "__main__":
    main()
