/**
 * Self-check for the palette scorer. Run with:
 *   node_modules/.bin/tsx src/components/command-palette/fuzzyScore.check.ts
 * (tsx lives in the repo root node_modules; no test framework needed.)
 */
import assert from "node:assert/strict";
import { fuzzyScore } from "./fuzzyScore";

const NO_MATCH = -1;

// Ranking order is the whole point: prefix > word-boundary > mid-word > scattered.
assert.ok(
  fuzzyScore("Change status", "change") > fuzzyScore("Change status", "status"),
  "prefix must outrank a later word"
);
assert.ok(
  fuzzyScore("Change status", "status") > fuzzyScore("Assign to", "sgn"),
  "substring must outrank a scattered subsequence"
);
assert.equal(fuzzyScore("Change status", "zzz"), NO_MATCH);
assert.equal(fuzzyScore("Change status", ""), 0, "empty query is neutral");

// A missing letter must fail even when every other letter is present in order.
assert.equal(fuzzyScore("Reply to ticket", "replyx"), NO_MATCH);

// Subsequence matching still finds acronym-ish input.
assert.ok(fuzzyScore("Change priority", "cp") > NO_MATCH);

// Word-boundary bonus: "status" after a space beats the same distance mid-word.
assert.ok(
  fuzzyScore("Change status", "status") > fuzzyScore("Changestatus", "status"),
  "word-boundary hit must beat a mid-word hit at the same offset"
);

// Guards against undefined titles reaching the scorer.
assert.equal(fuzzyScore(undefined as unknown as string, "a"), NO_MATCH);

console.log("fuzzyScore: all checks passed");
