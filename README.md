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
