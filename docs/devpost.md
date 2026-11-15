# FwdMD — Devpost write-up

**Tagline:** Paste a health WhatsApp forward in English, Hindi, Bengali or Hinglish. Get evidence-backed verdicts and a kind reply you can send back to the family group.

**Try it:** https://fwdmd-brown.vercel.app · **Code:** https://github.com/dhairyamittal8/fwdmd

## Inspiration
I grew up in Kolkata and Guwahati, where family WhatsApp groups are where health advice gets shared, from "lemon water cures dengue" to "stop your BP tablets and try this instead." Before college I worked in business development at Factifi, a misinformation platform, and saw that fact-checks exist but rarely reach people in the language, format and tone they'd actually use. The scale is real. India accounted for the largest share (15.94%) of 9,657 fact-checked COVID-19 misinformation items across 138 countries (Al-Zaman 2022). Roughly 19% of re-circulating debunked claims in the IFCN database relate to India (Singh et al.). India has about 530M WhatsApp users, and users over 65 are the most vulnerable (Bapaye & Bapaye 2021, JMIR).

## What it does
- Paste text or upload a screenshot of a forward (English, Hindi, Bengali, Hinglish).
- It extracts 1–4 checkable medical claims and labels each **TRUE / FALSE / MISLEADING / UNVERIFIED**, citing WHO / ICMR / MoHFW / PIB sources from a curated evidence pack of 42 common Indian health myths.
- It **abstains** (UNVERIFIED) when the evidence pack doesn't cover a claim, rather than guessing.
- A **red-flag banner** appears when a forward urges stopping medicine or delaying care.
- It writes a **kind, non-preachy reply in the same language and script**, with Copy and *Share on WhatsApp* buttons.
- *How it works* and *Evaluation* pages explain the pipeline and show benchmark results.

## How we built it
- **Next.js (App Router) + Tailwind + shadcn/ui**, deployed on **Vercel**. One API route, `/api/check`.
- **Claude (Anthropic API)** returns structured JSON validated with **zod**, with one retry on schema failure.
- **Server-side grounding guard:** evidence IDs the model invents are stripped, and a verdict left without a real source is downgraded to UNVERIFIED. This is covered by unit tests.
- Screenshot input uses Claude's vision to read the forward.
- **Evaluation harness (Python):** 200 stratified claims from the PUBHEALTH test set (seed 42), two conditions (direct label vs. an extract-assertion / weigh-evidence / abstain pipeline), cached API calls, and accuracy, macro-F1, confusion matrices and a coverage-vs-accuracy curve. It uses the same model as the live app.

## Results
| System | Acc | Macro-F1 |
|---|---|---|
| **FwdMD model, direct** | **81.0** | **67.7** |
| FwdMD pipeline | 78.5 | 61.2 |
| GPT-4 zero-shot (Zarharan et al. 2024) | 67.5 | 53.2 |
| SciBERT fine-tuned (Kotonya & Toni 2020) | 69.7 | 70.5 |
| Mistral-7B PEFT fine-tuned | 82.3 | 72.0 |
| Majority class | 48.6 | — |

Zero-shot, it beats published zero-shot GPT-4 by about 14 macro-F1 points and approaches fine-tuned models. Results are indicative only: a 200-claim sample, splits that differ across papers, and a single run.

## Challenges we ran into
- **Hallucinated citations:** an LLM will confidently cite a source that doesn't exist. We moved the trust boundary server-side, so a verdict has to point to a real evidence-pack entry or it becomes UNVERIFIED.
- **Language and script:** replies had to match the forward (Hinglish in Latin script, Hindi in Devanagari) while the UI stayed readable.
- **A negative result:** our more elaborate extract-and-weigh pipeline did *not* beat simple direct labelling, and it barely abstained (1/200). We report this rather than hide it.
- Shipping solo against the clock, including a last-minute Next.js security patch to get past Vercel's deploy check.

## Accomplishments that we're proud of
- An end-to-end, live, multilingual tool with a safety-first design (abstention, red flags, a grounding guard).
- A reproducible benchmark comparison against published baselines, built and run in a weekend.

## What we learned
- Grounding and abstention matter more than raw model accuracy in health. "I don't know" is a feature.
- "Unproven" claims are the hardest category for models, and they're also the most common kind of WhatsApp health rumour.
- Simple prompting can beat elaborate pipelines. Measure before you add complexity.

## What's next for FwdMD
- Clinician review of the evidence pack, and expanding it with PIB Fact Check data.
- A labelled benchmark of real Indian-language forwards (the current benchmark is English-only).
- Calibrated abstention using the confidence scores.
- A WhatsApp Business bot, so people can forward a message directly instead of opening a website.

## Limitations (honest)
There has been no clinician validation, and the evidence pack is small and hand-curated, with 3 entries citing an organisation homepage rather than a specific page. Accuracy on Indian languages hasn't been measured. PUBHEALTH fact-checks public-health claims with article context; it isn't a set of WhatsApp forwards. FwdMD is not medical advice.

**Built with:** nextjs, typescript, tailwindcss, shadcn-ui, anthropic, claude, zod, vercel, python, hugging-face-datasets
