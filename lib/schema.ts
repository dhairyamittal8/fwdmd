import { z } from "zod";

export const VERDICTS = ["TRUE", "FALSE", "MISLEADING", "UNVERIFIED"] as const;

const ClaimSchema = z.object({
  claim: z.string(),
  verdict: z.enum(VERDICTS),
  explanation: z.string(),
  evidence_ids: z.array(z.string()),
});

// Sent to Claude as the output format. No array bounds here: structured outputs only supports minItems 0/1.
export const ModelOutput = z.object({
  detected_language: z.string(),
  claims: z.array(ClaimSchema),
  red_flag: z.object({ triggered: z.boolean(), reason: z.string() }),
  reply: z.string(),
});

// Stricter check run on the parsed output; failing it triggers the one retry.
export const StrictOutput = ModelOutput.extend({
  claims: z.array(ClaimSchema).min(1).max(4),
  reply: z.string().min(1),
});

export type Source = { id: string; source_org: string; source_title: string; source_url: string };

export type CheckResult = {
  detected_language: string;
  claims: { claim: string; verdict: (typeof VERDICTS)[number]; explanation: string; sources: Source[] }[];
  red_flag: { triggered: boolean; reason: string };
  reply: string;
};
