# FwdMD — a fact-checker for health WhatsApp forwards

**Live:** fwdmd-brown.vercel.app · **Code:** github.com/dhairyamittal8/fwdmd · DSH Hacks V2 (AI x Healthcare)

## Problem
Health misinformation in India spreads mainly through WhatsApp family groups, in English, Hindi, Bengali and Hinglish. India accounted for the largest share (15.94%) of 9,657 fact-checked COVID-19 misinformation items across 138 countries (Al-Zaman 2022, *IFLA Journal*). About 19% of re-circulating, already-debunked claims in the IFCN database related to India (Singh et al.). India has 53 crore (530M) WhatsApp users (Govt. of India, IT Rules release, 2021), and users over 65 were the most vulnerable to misinformation (Bapaye & Bapaye 2021, *JMIR Public Health & Surveillance*, n=1,137). Fact-checks exist, but rarely in the language and tone that would let someone reply to an uncle in the family group.

## What FwdMD does
1. **Paste or screenshot** a forward in English, Hindi, Bengali or Hinglish.
2. Claude **extracts 1–4 checkable medical claims** and gives each a verdict: TRUE / FALSE / MISLEADING / UNVERIFIED.
3. Verdicts are **grounded only in a curated evidence pack** of 42 common Indian health myths, mapped to WHO / ICMR / MoHFW / PIB Fact Check sources. If the pack doesn't cover a claim, it **abstains (UNVERIFIED)** instead of guessing.
4. A **red-flag banner** appears if the forward urges stopping medicine or delaying care.
5. It writes a **kind reply in the forward's own language**, with Copy and *Share on WhatsApp* buttons.

## Safety design
- **Server-side grounding:** evidence IDs the model invents are dropped, and any verdict left without a real source is downgraded to UNVERIFIED (unit-tested).
- **Structured output:** responses are validated with zod, retried once, and fail with a friendly message.
- **Single fixed model**, with no fallback. No data is stored, and there's no account. A persistent "not medical advice" disclaimer is shown.

## Evaluation (PUBHEALTH, 200-claim stratified test sample, seed 42)
| System | Accuracy | Macro-F1 |
|---|---|---|
| **FwdMD model, direct label** | **81.0** | **67.7** |
| FwdMD extract-and-weigh pipeline | 78.5 | 61.2 |
| GPT-4 zero-shot (Zarharan et al. 2024) | 67.5 | 53.2 |
| SciBERT, fine-tuned (Kotonya & Toni 2020) | 69.7 | 70.5 |
| Mistral-7B, PEFT fine-tuned | 82.3 | 72.0 |
| Majority class | 48.6 | — |

**Findings:** zero-shot, it beats published zero-shot GPT-4 by about 14 macro-F1 points and approaches fine-tuned systems. "Unproven" is the hardest class (F1 0.36). Our multi-step pipeline did *not* beat direct labelling, and it abstained on only 1/200 claims, so abstention needs calibration. **Caveats:** a 200-claim sample; splits differ across papers, so the comparison is indicative only; one run, no significance test; an English-only benchmark of public-health claims, not WhatsApp forwards; possible training-data overlap.

## Limitations & next steps
There has been no clinician validation yet. The evidence pack is small and hand-curated (all source links checked live; 3 cite an organisation homepage rather than a specific page). Indian-language accuracy hasn't been measured. **Next:** clinician review of the evidence pack, a labelled benchmark of real Indian-language forwards, calibrated abstention, a WhatsApp Business bot so people can forward directly, and expanding the pack with PIB Fact Check data.

*Built solo by Dhairya Mittal (Davidson College) with Next.js, Tailwind, shadcn/ui, the Anthropic API (Claude) and Vercel.*
