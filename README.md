# FwdMD

Fact-check health WhatsApp forwards (English, Hindi, Bengali, Hinglish; text or screenshot) against a small evidence pack of WHO / ICMR / MoHFW / NCDC / PIB Fact Check sources, and get a kind reply to send back in the same language.

Not medical advice.

## Run

Create `.env.local` with:

```
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-opus-5-5   # optional, this is the default
```

Then:

```bash
npm install
npm run dev                  # http://localhost:3000
```

## How it works

- `POST /api/check` (`app/api/check/route.ts`) sends the forward (and optional screenshot) plus the whole evidence pack (`data/evidence.json`) to Claude with a zod structured-output schema.
- The server drops any cited evidence id that isn't in the pack and downgrades a TRUE/FALSE/MISLEADING claim with no valid evidence to UNVERIFIED (`lib/sanitize.ts`).
- One retry on a schema failure, then a friendly error.
- No database, no auth, nothing stored.

## Checks

```bash
npm run build
node --test tests/sanitize.test.ts
```

Evidence URLs marked `"url_confidence": "check"` are listed in [docs/evidence_to_verify.md](docs/evidence_to_verify.md).

## Deploy

Import the repo in Vercel and set `ANTHROPIC_API_KEY` (and optionally `CLAUDE_MODEL`) in the project's environment variables.

## Live demo, video and docs

- Live app: https://fwdmd-brown.vercel.app
- Demo video: https://youtu.be/bs4H5ZtRZgM
- One-pager: [docs/one_pager.pdf](docs/one_pager.pdf) · Evaluation: [eval/RESULTS.md](eval/RESULTS.md)

## Timeline, credits and AI assistance

- **Built:** solo by Dhairya Mittal. The app code and evidence pack were created on November 14, 2026. The PUBHEALTH evaluation script was prepared in a separate session shortly before and was run on November 14. See the git history for exact dates.
- **AI in the product:** Claude (Anthropic API) extracts claims, assigns verdicts against the evidence pack, and writes the reply. Screenshot reading uses Claude's vision.
- **AI coding assistance:** Claude Code was used to scaffold and write much of the code, the evaluation harness and the docs. I directed the design, specified the safety rules (evidence-only grounding, abstention, red flags), and tested and reviewed the outputs.
- **Third-party libraries:** Next.js, React, Tailwind CSS, shadcn/ui, zod, @anthropic-ai/sdk; Python: datasets, pandas, scikit-learn, matplotlib.
- **Data:** PUBHEALTH (Kotonya & Toni 2020, via Hugging Face `ImperialCollegeLondon/health_fact`) for evaluation only. Evidence-pack facts are paraphrased from public WHO / ICMR / MoHFW / NCDC / PIB pages, which are linked per entry.
- **Demo video narration** is an AI text-to-speech voice (Piper).
