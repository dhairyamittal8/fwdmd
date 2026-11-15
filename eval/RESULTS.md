# PUBHEALTH veracity evaluation (200-claim sample)

Model: `claude-opus-5-5` · sample: 200 test claims, stratified, seed 42 (`eval/sample_ids.json`) · prompts v1 · generated 2026-11-14 23:54 UTC

## Our results next to published baselines

| System | Source | Test set | Macro-F1 | Accuracy |
|---|---|---|---:|---:|
| **DIRECT (zero-shot, one label), claude-opus-5-5** | this repo | 200-claim sample | **67.7** | **81.0** |
| **PIPELINE (extract → weigh → forced label), claude-opus-5-5** | this repo | 200-claim sample | **61.2** | **78.5** |
| Majority class | Kotonya & Toni 2020 test split | as reported in the paper | – | 48.6 |
| SciBERT (fine-tuned) | Kotonya & Toni 2020 | as reported in the paper | 70.52 | 69.73 |
| GPT-3.5-turbo zero-shot | Zarharan et al. 2024 | as reported in the paper | 51.4 | – |
| GPT-4 zero-shot | Zarharan et al. 2024 | as reported in the paper | 53.2 | 67.5 |
| Mistral-7B PEFT (fine-tuned) | Zarharan et al. 2024 | as reported in the paper | 72.0 | 82.3 |

Baseline figures are quoted from the cited papers, not re-run here. – means the figure was not supplied.

## Per-class F1

| Condition | false | mixture | true | unproven |
|---|---:|---:|---:|---:|
| DIRECT | 82.4 | 59.5 | 92.5 | 36.4 |
| PIPELINE | 79.3 | 51.2 | 92.2 | 22.2 |

Gold label counts in the sample: false 63, mixture 33, true 97, unproven 7.

## Confusion matrix: DIRECT

Rows are gold labels, columns are predictions.

| gold \ pred | false | mixture | true | unproven | invalid |
|---|---:|---:|---:|---:|---:|
| false | 49 | 12 | 0 | 2 | 0 |
| mixture | 5 | 25 | 3 | 0 | 0 |
| true | 0 | 11 | 86 | 0 | 0 |
| unproven | 2 | 3 | 0 | 2 | 0 |

## Confusion matrix: PIPELINE

Rows are gold labels, columns are predictions.

| gold \ pred | false | mixture | true | unproven | invalid |
|---|---:|---:|---:|---:|---:|
| false | 46 | 16 | 0 | 1 | 0 |
| mixture | 5 | 21 | 7 | 0 | 0 |
| true | 0 | 8 | 89 | 0 | 0 |
| unproven | 2 | 4 | 0 | 1 | 0 |

## PIPELINE: coverage vs accuracy

The model set the abstain flag on 1 of 200 claims (coverage 99.5%). Accuracy on the claims it answered: 78.9%; accuracy of its forced guesses on the claims it abstained on: 0.0%.

Answered = abstain flag false and confidence ≥ threshold.

| Confidence ≥ | Coverage | Answered | Accuracy on answered |
|---:|---:|---:|---:|
| 0.00 | 99.5% | 199 | 78.9% |
| 0.30 | 99.5% | 199 | 78.9% |
| 0.40 | 99.5% | 199 | 78.9% |
| 0.45 | 98.5% | 197 | 79.2% |
| 0.50 | 94.5% | 189 | 81.0% |
| 0.55 | 88.0% | 176 | 83.5% |
| 0.58 | 81.5% | 163 | 87.1% |
| 0.60 | 81.0% | 162 | 87.7% |
| 0.62 | 75.0% | 150 | 90.0% |
| 0.65 | 74.0% | 148 | 89.9% |
| 0.68 | 73.0% | 146 | 89.7% |
| 0.72 | 71.5% | 143 | 89.5% |
| 0.75 | 67.5% | 135 | 89.6% |
| 0.80 | 63.5% | 127 | 91.3% |
| 0.82 | 56.5% | 113 | 93.8% |
| 0.85 | 52.5% | 105 | 94.3% |
| 0.88 | 41.0% | 82 | 95.1% |
| 0.90 | 32.0% | 64 | 98.4% |
| 0.92 | 23.5% | 47 | 97.9% |
| 0.93 | 19.5% | 39 | 97.4% |
| 0.95 | 11.0% | 22 | 100.0% |
| 0.96 | 4.0% | 8 | 100.0% |
| 0.97 | 3.0% | 6 | 100.0% |

Charts: `public/eval/confusion_matrix.png`, `public/eval/coverage_curve.png`.

## Caveats: these results are indicative only

- **Small sample.** 200 claims, not the full 1,233-claim labelled test split. The 95% interval on an accuracy near 70% at n=200 is roughly ±6 points, and the `unproven` class has only 7 claims, so its F1 (and therefore macro-F1) is noisy.
- **Different test sets across papers.** Kotonya & Toni report on the full test split; Zarharan et al. use their own evaluation setup and split sizes. None of the baseline rows were scored on our 200 claims, so differences of a few points mean nothing.
- **Different evidence context.** We give the model the fact-check article's full `main_text`, truncated to the first 1,500 words. Published systems variously use selected top-k evidence sentences or summarised/explanation text. The full article often states the verdict outright, which makes our setting easier.
- **Zero-shot vs fine-tuned.** SciBERT and Mistral-7B PEFT were trained on PUBHEALTH; our runs and the GPT rows are zero-shot.
- **Possible training-data exposure.** PUBHEALTH has been public since 2020, so the model may have seen these claims and their verdicts.
- **Sampling temperature.** No temperature parameter was sent (model default sampling); outputs are not guaranteed deterministic (the cache makes reruns reproducible).
- **Single run.** One run per condition, no repeated sampling or significance test between DIRECT and PIPELINE.

## Reproduce

```bash
cd eval
uv venv && uv pip install -r requirements.txt
export ANTHROPIC_API_KEY=...  CLAUDE_MODEL=claude-opus-5-5
.venv/bin/python run_pubhealth.py --n 10   # smoke test
.venv/bin/python run_pubhealth.py          # full 200 (cached calls are free)
```

Data source: Hugging Face ImperialCollegeLondon/health_fact (loading script, trust_remote_code=True).
