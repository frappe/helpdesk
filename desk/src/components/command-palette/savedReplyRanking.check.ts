/**
 * Self-check for saved-reply ordering and promotion. Run with:
 *   node_modules/.bin/tsx src/components/command-palette/savedReplyRanking.check.ts
 * (tsx lives in the repo root node_modules; no test framework needed.)
 */
import assert from "node:assert/strict";
import {
  mostUsedFirst,
  topSavedReplies,
  withUse,
  withoutReply,
  type SavedReplyUsage,
} from "./savedReplyRanking";

const usage: SavedReplyUsage = {
  refund: { title: "Refund policy", count: 12 },
  reset: { title: "Password reset", count: 6 },
  escalate: { title: "Escalation notice", count: 5 },
  shipping: { title: "Shipping delay", count: 4 },
};

// --- ordering ------------------------------------------------------------

const list = [
  { name: "shipping" },
  { name: "refund" },
  { name: "never-used" },
  { name: "reset" },
];

assert.deepEqual(
  mostUsedFirst(list, usage).map((reply) => reply.name),
  ["refund", "reset", "shipping", "never-used"],
  "most-used first"
);

// Stability is what makes cold start sane: with no history at all the list must
// come back in the order the server sent it (modified desc), not reshuffled.
assert.deepEqual(
  mostUsedFirst(list, {}).map((reply) => reply.name),
  ["shipping", "refund", "never-used", "reset"],
  "no usage must preserve source order"
);

// Ties must not reorder either, or the drill-down would shuffle between opens.
assert.deepEqual(
  mostUsedFirst(list, {
    shipping: { title: "s", count: 3 },
    reset: { title: "r", count: 3 },
  }).map((reply) => reply.name),
  ["shipping", "reset", "refund", "never-used"],
  "equal counts must preserve source order"
);

// mostUsedFirst must not mutate its input: the caller holds the resource's data.
const original = [{ name: "shipping" }, { name: "refund" }];
mostUsedFirst(original, usage);
assert.deepEqual(
  original.map((reply) => reply.name),
  ["shipping", "refund"],
  "must not sort the caller's array in place"
);

// --- promotion to a root row ---------------------------------------------

assert.deepEqual(
  topSavedReplies(usage, 5, 3).map((reply) => reply.name),
  ["refund", "reset", "escalate"],
  "top rows are the highest counts at or above the threshold"
);

// The threshold is inclusive at exactly minUses, and excludes just below it.
assert.deepEqual(
  topSavedReplies(usage, 5, 99).map((reply) => reply.name),
  ["refund", "reset", "escalate"],
  "count === minUses qualifies, count < minUses does not"
);

// The whole point of earning the row: long-tail usage yields no rows at all,
// rather than promoting whatever happens to be least-rare.
assert.deepEqual(
  topSavedReplies({ a: { title: "A", count: 2 }, b: { title: "B", count: 1 } }, 5, 3),
  [],
  "long-tail usage must promote nothing"
);

assert.deepEqual(topSavedReplies({}, 5, 3), [], "no history promotes nothing");

assert.equal(
  topSavedReplies(usage, 1, 2).length,
  2,
  "maxRows caps the row count"
);

// Titles ride along so a root row needs no list fetch to render.
assert.equal(
  topSavedReplies(usage, 5, 1)[0]?.title,
  "Refund policy",
  "the stored title comes back with the row"
);

// --- recording -----------------------------------------------------------

assert.equal(withUse({}, "refund", "Refund policy").refund?.count, 1);
assert.equal(withUse(usage, "refund", "Refund policy").refund?.count, 13);

// A rename is picked up on next use rather than needing a migration.
assert.equal(
  withUse(usage, "refund", "Refund policy v2").refund?.title,
  "Refund policy v2",
  "the latest title wins"
);

assert.equal(usage.refund?.count, 12, "withUse must not mutate");

assert.ok(
  !("refund" in withoutReply(usage, "refund")),
  "a deleted reply is dropped"
);
assert.equal(usage.refund?.count, 12, "withoutReply must not mutate");

// A reply that just fell below the threshold must lose its row immediately.
assert.deepEqual(
  topSavedReplies(withoutReply(usage, "refund"), 5, 3).map((r) => r.name),
  ["reset", "escalate"],
  "dropping a reply removes its root row"
);

console.log("savedReplyRanking: all checks passed");
