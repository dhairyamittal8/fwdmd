import Image from "next/image";
import results from "@/eval/results.json";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const metadata = { title: "Evaluation · FwdMD" };

const CONDITIONS = [
  { key: "direct", name: "Direct", blurb: "one zero-shot label" },
  { key: "pipeline", name: "Pipeline", blurb: "extract → weigh → forced label, with abstain flag" },
] as const;
const LABELS = ["false", "mixture", "true", "unproven"] as const;

const pct = (v: number | null | undefined, d = 1) => (v == null ? "–" : (v * 100).toFixed(d));
const raw = (v: number | null | undefined) => (v == null ? "–" : v.toFixed(1)); // baselines are already in %

export default function Evaluation() {
  const { direct, pipeline } = results.conditions;
  const byKey = { direct, pipeline };
  const gpt4 = results.baselines.find((b) => b.system.startsWith("GPT-4"));
  const gainOverGpt4 = gpt4?.macro_f1 != null ? direct.macro_f1 * 100 - gpt4.macro_f1 : null;
  const abstain = results.coverage_curve.abstain_flag_only;
  const curve = results.coverage_curve.confidence_and_abstain_flag;
  const keyThresholds = [0, 0.62, 0.8, 0.9].map((t) => curve.find((p) => p.threshold === t)).filter(Boolean) as typeof curve;
  const sample = curve.find((p) => p.threshold === 0.62);
  const unprovenN =results.label_counts.unproven;

  return (
    <article className="space-y-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">Evaluation</h1>
        <p className="text-muted-foreground">
          We tested Claude ({results.model}) on {results.n} claims from PUBHEALTH, a public-health fact-checking
          benchmark with four labels: true, false, mixture and unproven. These numbers come from a stratified sample
          (seed {results.seed}) and are indicative, not a leaderboard result.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3" aria-label="Headline results">
        {CONDITIONS.map((c) => (
          <Card key={c.key}>
            <CardHeader>
              <CardTitle>{c.name}</CardTitle>
              <CardDescription>{c.blurb}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-1">
              <p className="text-3xl font-bold">{pct(byKey[c.key].accuracy)}%</p>
              <p className="text-sm text-muted-foreground">accuracy</p>
              <p className="pt-2 text-xl font-semibold">{pct(byKey[c.key].macro_f1)}</p>
              <p className="text-sm text-muted-foreground">macro-F1</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Next to published baselines</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-2 pr-3 font-medium">System</th>
                <th className="py-2 pr-3 text-right font-medium">Macro-F1</th>
                <th className="py-2 text-right font-medium">Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {CONDITIONS.map((c) => (
                <tr key={c.key} className="border-b font-semibold">
                  <td className="py-2 pr-3">FwdMD eval: {c.name}, {results.model}</td>
                  <td className="py-2 pr-3 text-right">{pct(byKey[c.key].macro_f1)}</td>
                  <td className="py-2 text-right">{pct(byKey[c.key].accuracy)}</td>
                </tr>
              ))}
              {results.baselines.map((b) => (
                <tr key={b.system} className="border-b">
                  <td className="py-2 pr-3">
                    {b.system}
                    <span className="block text-xs text-muted-foreground">{b.source}</span>
                  </td>
                  <td className="py-2 pr-3 text-right">{raw(b.macro_f1)}</td>
                  <td className="py-2 text-right">{raw(b.accuracy)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted-foreground">
          Baseline figures are quoted from the papers, not re-run, and were scored on different splits. – means the
          figure was not reported.
        </p>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Per-class F1</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-2 pr-3 font-medium">Condition</th>
                {LABELS.map((l) => (
                  <th key={l} className="py-2 pr-3 text-right font-medium capitalize">
                    {l} <span className="font-normal text-muted-foreground">(n={results.label_counts[l]})</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CONDITIONS.map((c) => (
                <tr key={c.key} className="border-b">
                  <td className="py-2 pr-3">{c.name}</td>
                  {LABELS.map((l) => (
                    <td key={l} className="py-2 pr-3 text-right">
                      {pct(byKey[c.key].per_class_f1[l])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Confusion matrices</h2>
        <p className="text-sm text-muted-foreground">Rows are the true label, columns are what Claude predicted.</p>
        {CONDITIONS.map((c) => {
          const cm = byKey[c.key].confusion_matrix;
          const showInvalid = byKey[c.key].n_invalid > 0;
          const cols = showInvalid ? cm.labels : cm.labels.slice(0, 4);
          return (
            <div key={c.key} className="space-y-1">
              <h3 className="text-sm font-medium">{c.name}</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="py-2 pr-3 font-medium">true \ predicted</th>
                      {cols.map((l) => (
                        <th key={l} className="py-2 pr-3 text-right font-medium capitalize">
                          {l}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cm.matrix.map((row, i) => (
                      <tr key={LABELS[i]} className="border-b">
                        <td className="py-2 pr-3 capitalize">{LABELS[i]}</td>
                        {row.slice(0, cols.length).map((v, j) => (
                          <td
                            key={cols[j]}
                            className={`py-2 pr-3 text-right ${i === j ? "font-semibold" : "text-muted-foreground"}`}
                          >
                            {v}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Pipeline: coverage vs accuracy</h2>
        <p className="text-sm text-muted-foreground">
          If the pipeline only answers when its confidence is high enough, accuracy on the answered claims rises and
          coverage falls.
        </p>
        <Image
          src="/eval/coverage_curve.png"
          alt="Line chart of pipeline accuracy against coverage as the confidence threshold rises"
          width={1120}
          height={736}
          className="h-auto w-full rounded-md border"
        />
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="py-2 pr-3 font-medium">Confidence ≥</th>
                <th className="py-2 pr-3 text-right font-medium">Coverage</th>
                <th className="py-2 pr-3 text-right font-medium">Answered</th>
                <th className="py-2 text-right font-medium">Accuracy on answered</th>
              </tr>
            </thead>
            <tbody>
              {keyThresholds.map((p) => (
                <tr key={p.threshold} className="border-b">
                  <td className="py-2 pr-3">{p.threshold.toFixed(2)}</td>
                  <td className="py-2 pr-3 text-right">{pct(p.coverage)}%</td>
                  <td className="py-2 pr-3 text-right">{p.n_answered}</td>
                  <td className="py-2 text-right">{pct(p.accuracy)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Findings</h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong>Beats zero-shot GPT-4 by about {gainOverGpt4?.toFixed(0)} macro-F1 points</strong> (
            {pct(direct.macro_f1)} vs {raw(gpt4?.macro_f1)}), but still trails the fine-tuned systems on macro-F1
            (SciBERT {raw(results.baselines.find((b) => b.system.startsWith("SciBERT"))?.macro_f1)}, Mistral-7B PEFT{" "}
            {raw(results.baselines.find((b) => b.system.startsWith("Mistral"))?.macro_f1)}).
          </li>
          <li>
            <strong>&ldquo;Unproven&rdquo; is the hardest label</strong>: F1 {pct(direct.per_class_f1.unproven, 0)} for
            Direct and {pct(pipeline.per_class_f1.unproven, 0)} for Pipeline, on only {unprovenN} claims. Both
            conditions mostly confuse false and mixture with each other.
          </li>
          <li>
            <strong>The extract-and-weigh pipeline did not beat direct labelling</strong> ({pct(pipeline.accuracy)}% vs{" "}
            {pct(direct.accuracy)}% accuracy, {pct(pipeline.macro_f1)} vs {pct(direct.macro_f1)} macro-F1).
          </li>
          <li>
            <strong>Abstention is not calibrated yet.</strong> The pipeline abstained on {abstain.n_abstained} of{" "}
            {results.n} claims, so its abstain flag does almost nothing.
            {sample && (
              <>
                {" "}
                A confidence threshold does help: at confidence ≥ {sample.threshold.toFixed(2)} it answers{" "}
                {pct(sample.coverage, 0)}% of claims at {pct(sample.accuracy, 0)}% accuracy.
              </>
            )}{" "}
            Calibrating the abstention threshold is future work.
          </li>
        </ul>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Caveats</h2>
        <ul className="list-disc space-y-2 pl-5 text-sm">
          <li>
            A {results.n}-claim stratified sample (seed {results.seed}), not the full test split. Small classes, such
            as unproven with {unprovenN} claims, make macro-F1 noisy.
          </li>
          <li>
            Papers use different splits and evidence settings, so the comparison with baselines is indicative only. We
            also give the model the full fact-check article (first {results.max_words} words), which often states the
            verdict and makes the task easier.
          </li>
          <li>The benchmark is English only, while the app handles Hindi, Bengali and Hinglish. We did not measure those.</li>
          <li>
            PUBHEALTH is a public-health claims benchmark from fact-checking articles, not WhatsApp forwards. The app
            checks claims against a small evidence pack, which is a different task.
          </li>
          <li>
            Temperature could not be set, so outputs are not guaranteed deterministic. One run
            per condition, no significance test. PUBHEALTH has been public since 2020, so the model may have seen it.
          </li>
        </ul>
        <p className="text-xs text-muted-foreground">
          Generated {results.generated_at}. Full tables and method are in <code>eval/RESULTS.md</code>.
        </p>
      </section>
    </article>
  );
}
