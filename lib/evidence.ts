import raw from "@/data/evidence.json";

export type Evidence = (typeof raw)[number];

export const EVIDENCE: Evidence[] = raw;
export const EVIDENCE_BY_ID = new Map(EVIDENCE.map((e) => [e.id, e]));
