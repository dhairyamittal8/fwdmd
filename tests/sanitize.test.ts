import { test } from "node:test";
import assert from "node:assert/strict";
import { groundClaims, NOT_COVERED } from "../lib/sanitize.ts";

const valid = new Set(["dengue-lemon-hot-water", "covid-5g"]);

test("drops unknown ids and keeps known ones", () => {
  const [c] = groundClaims(
    [{ claim: "x", verdict: "FALSE", explanation: "e", evidence_ids: ["dengue-lemon-hot-water", "made-up", "dengue-lemon-hot-water"] }],
    valid,
  );
  assert.equal(c.verdict, "FALSE");
  assert.deepEqual(c.evidence_ids, ["dengue-lemon-hot-water"]);
});

test("downgrades a rated claim with no valid evidence", () => {
  const [c] = groundClaims([{ claim: "x", verdict: "TRUE", explanation: "e", evidence_ids: ["made-up"] }], valid);
  assert.equal(c.verdict, "UNVERIFIED");
  assert.equal(c.explanation, NOT_COVERED);
  assert.deepEqual(c.evidence_ids, []);
});

test("leaves UNVERIFIED claims alone", () => {
  const [c] = groundClaims([{ claim: "x", verdict: "UNVERIFIED", explanation: "e", evidence_ids: [] }], valid);
  assert.equal(c.explanation, "e");
});
