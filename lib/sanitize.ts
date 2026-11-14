// Pure grounding rules, kept free of path aliases so `node --test` can import it directly.
export type Verdict = "TRUE" | "FALSE" | "MISLEADING" | "UNVERIFIED";
export type Claim = { claim: string; verdict: Verdict; explanation: string; evidence_ids: string[] };

export const NOT_COVERED =
  "Our evidence pack does not cover this claim, so we can't confirm or deny it. Please check with a doctor.";

// Drop evidence ids that don't exist; a rated claim left with no real evidence becomes UNVERIFIED.
export function groundClaims(claims: Claim[], validIds: Set<string>): Claim[] {
  return claims.map((c) => {
    const ids = [...new Set(c.evidence_ids.filter((id) => validIds.has(id)))];
    if (c.verdict !== "UNVERIFIED" && ids.length === 0) {
      return { ...c, verdict: "UNVERIFIED", explanation: NOT_COVERED, evidence_ids: [] };
    }
    return { ...c, evidence_ids: ids };
  });
}
