/**
 * Self-check for the palette scorer. Run with:
 *   node_modules/.bin/tsx src/components/command-palette/fuzzyScore.check.ts
 * (tsx lives in the repo root node_modules; no test framework needed.)
 */
import assert from "node:assert/strict";
import { fuzzyScore, scoreCommand } from "./fuzzyScore";
import {
  CONTEXT_WEIGHT,
  FLAT_OPTION_WEIGHT,
  titleRuns,
  type Command,
} from "./paletteTypes";

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

// --- flat option rows vs their drill-down parent --------------------------
// The whole point of the flat rows: "urgent" must SET the priority, while
// "priority" must still lead with the picker. If these invert, Enter silently
// does the wrong one of the two.

const changePriority: Command = {
  id: "ticket-priority",
  title: "Change priority",
  group: "Ticket",
  weight: CONTEXT_WEIGHT,
  keywords: "level",
};
const setUrgent: Command = {
  id: "priority-Urgent",
  title: "Set priority: Urgent",
  group: "Ticket",
  weight: FLAT_OPTION_WEIGHT,
  keywords: "Urgent",
};
const changeStatus: Command = {
  id: "ticket-status",
  title: "Change status",
  group: "Ticket",
  weight: CONTEXT_WEIGHT,
  keywords: "state",
};
const setOpen: Command = {
  id: "status-Open",
  title: "Set status: Open",
  group: "Ticket",
  weight: FLAT_OPTION_WEIGHT,
  keywords: "Open",
};

assert.ok(
  scoreCommand(setUrgent, "urgent") > scoreCommand(changePriority, "urgent"),
  "typing an option name must lead with the row that sets it"
);
assert.ok(
  scoreCommand(setOpen, "open") > scoreCommand(changeStatus, "open"),
  "same for status names"
);
assert.ok(
  scoreCommand(changePriority, "priority") > scoreCommand(setUrgent, "priority"),
  "typing the field name must still lead with the picker"
);
assert.ok(
  scoreCommand(changeStatus, "status") > scoreCommand(setOpen, "status"),
  "same for status"
);

// Flat rows must clear the fixed rank server search hits carry (~950), or a
// ticket whose subject contains "urgent" buries the row that sets it.
const TOP_SEARCH_RANK = 950;
assert.ok(
  scoreCommand(setUrgent, "urgent") > TOP_SEARCH_RANK,
  "flat option rows must outrank server search hits"
);

// An empty query scores 0 everywhere, which is exactly why hideWhenEmpty exists
// rather than a low weight — weight cannot separate rows that all tie at 0.
assert.equal(scoreCommand(setUrgent, ""), 0);
assert.equal(scoreCommand(changePriority, ""), 0);

// Fixed ranks bypass the scorer entirely.
assert.equal(
  scoreCommand({ ...setUrgent, rank: 42 }, "nomatchwhatsoever"),
  42,
  "rank must win over the fuzzy path"
);

// --- server highlighting -------------------------------------------------
// Lives here rather than in its own file: same shape of pure, import-free helper.

assert.deepEqual(
  titleRuns("Cannot <mark>login</mark> to portal"),
  [
    { text: "Cannot ", match: false },
    { text: "login", match: true },
    { text: " to portal", match: false },
  ],
  "runs alternate around the marked text"
);

assert.deepEqual(
  titleRuns("<mark>Refund</mark> for <mark>order</mark>"),
  [
    { text: "Refund", match: true },
    { text: " for ", match: false },
    { text: "order", match: true },
  ],
  "several marks in one title"
);

assert.deepEqual(
  titleRuns("Nothing highlighted"),
  [{ text: "Nothing highlighted", match: false }],
  "an unhighlighted title is one plain run"
);

// Empty runs would render as stray nodes between adjacent marks.
assert.deepEqual(
  titleRuns("<mark>a</mark><mark>b</mark>"),
  [
    { text: "a", match: true },
    { text: "b", match: true },
  ],
  "adjacent marks leave no empty run between them"
);

assert.deepEqual(titleRuns(""), [], "empty in, empty out");

// The whole reason for rendering runs as text nodes: markup in ticket content
// must come out inert, never as elements.
assert.deepEqual(
  titleRuns("<script>alert(1)</script> and <mark>hi</mark>"),
  [
    { text: "alert(1) and ", match: false },
    { text: "hi", match: true },
  ],
  "other tags are stripped, not rendered"
);

console.log("fuzzyScore: all checks passed");
