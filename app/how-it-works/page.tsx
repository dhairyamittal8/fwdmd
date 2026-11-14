export const metadata = { title: "How it works · FwdMD" };

export default function HowItWorks() {
  return (
    <article className="space-y-6">
      <h1 className="text-2xl font-bold">How FwdMD works</h1>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">The pipeline</h2>
        <ol className="list-decimal space-y-1 pl-5">
          <li>You paste a forward or upload a screenshot. If it&apos;s an image, Claude reads the text from it.</li>
          <li>Claude detects the language (English, Hindi, Bengali or Hinglish) and picks out 1–4 checkable health claims.</li>
          <li>
            Each claim is compared only against our evidence pack: about 40 common Indian health myths, each tied to a
            WHO, ICMR, MoHFW, NCDC or PIB Fact Check source.
          </li>
          <li>The answer is checked against a strict schema. If it doesn&apos;t fit, we retry once, then show an error.</li>
          <li>You get a verdict per claim with sources, plus a kind reply in the same language to send back.</li>
        </ol>
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Safety design</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <strong>Evidence-only grounding.</strong> Verdicts come only from the evidence pack, not from the
            model&apos;s general knowledge. Any source the model cites that isn&apos;t in the pack is removed on our server.
          </li>
          <li>
            <strong>Abstention.</strong> If no entry covers a claim, it&apos;s marked UNVERIFIED. A claim rated TRUE, FALSE
            or MISLEADING without a valid source is automatically downgraded to UNVERIFIED.
          </li>
          <li>
            <strong>Red flags.</strong> If a forward urges stopping medicine, skipping the doctor or delaying care, a red
            warning appears at the top.
          </li>
          <li>
            <strong>No data stored.</strong> There&apos;s no database and no login. Your forward is sent to Claude to be
            checked and is not saved by FwdMD.
          </li>
        </ul>
      </section>

      <p className="text-sm text-muted-foreground">
        FwdMD is a hackathon prototype. It is not medical advice. In an emergency, see a doctor.
      </p>
    </article>
  );
}
