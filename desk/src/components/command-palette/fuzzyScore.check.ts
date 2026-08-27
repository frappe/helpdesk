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
  hideWhenEmpty: true,
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
  hideWhenEmpty: true,
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

// Hidden flat rows need a deliberate (substring-or-better) match: "sett" is a
// scattered subsequence of "Set status: …"/"Set priority: …", so it would
// un-hide every option row at once and bury Settings' exact prefix match.
assert.equal(scoreCommand(setUrgent, "sett"), NO_MATCH);
assert.equal(scoreCommand(setOpen, "sett"), NO_MATCH);
assert.ok(
  scoreCommand(setOpen, "set status") > NO_MATCH,
  "a deliberate prefix still surfaces the flat rows"
);
assert.ok(
  scoreCommand(changeStatus, "chst") > NO_MATCH,
  "normal rows keep scattered abbreviation matching"
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

// --- a root row must not outrank the category it belongs to ----------------
// "Saved Replies" leads with the word both rows share, which is what keeps the
// category on top. The rule this pins: a category title must not bury its own
// distinguishing word mid-title, because prefix (1000) vs word-boundary (~950)
// is a wider gap than CONTEXT_WEIGHT 1.2 vs FLAT_OPTION_WEIGHT 1.15 can close.

const savedReplies: Command = {
  id: "ticket-saved-reply",
  title: "Saved Replies",
  group: "Ticket",
  weight: CONTEXT_WEIGHT,
  keywords: "reply template canned macro snippet",
};
const oneSavedReply: Command = {
  id: "saved-reply-flat-x",
  title: "Refund policy",
  subtitle: "Saved Reply",
  group: "Ticket",
  weight: FLAT_OPTION_WEIGHT,
  hideWhenEmpty: true,
};

for (const term of ["saved", "saved repl", "reply", "canned"]) {
  assert.ok(
    scoreCommand(savedReplies, term) > scoreCommand(oneSavedReply, term),
    `"${term}" must lead with the category, not with one saved reply`
  );
}

// "reply" is not a substring of "replies", so a plural title cannot be found by
// the singular the agent actually types — it has to be carried in keywords.
assert.equal(
  scoreCommand({ ...savedReplies, keywords: undefined }, "reply"),
  -1,
  "documents why 'reply' is in the keywords and not left to the title"
);

// ...while the reply's own words still reach it directly, which is its whole job.
for (const term of ["refund", "polic"]) {
  assert.ok(
    scoreCommand(oneSavedReply, term) > scoreCommand(savedReplies, term),
    `"${term}" must reach the reply itself`
  );
}

// The hazard this arrangement avoids, worth pinning because it is not obvious:
// a category row that carries its distinguishing word *mid-title* loses to a
// root row that leads with it. Prefix (1000) vs word-boundary (~950) is a bigger
// gap than CONTEXT_WEIGHT 1.2 vs FLAT_OPTION_WEIGHT 1.15 can close.
const midTitleCategory: Command = { ...savedReplies, title: "Insert saved reply" };
const titlePrefixedRow: Command = {
  ...oneSavedReply,
  title: "Saved Reply: Refund policy",
};
assert.ok(
  scoreCommand(titlePrefixedRow, "saved") > scoreCommand(midTitleCategory, "saved"),
  "a mid-title category is buried by a root row that leads with the same word"
);

// Leading with that word is what makes the category safe — both score a prefix
// match, so the weights decide and the category wins. Note this means the
// subtitle is chosen for readability, not to escape the hazard above: a
// "Saved reply: X" title would rank correctly under "Saved replies" too.
assert.ok(
  scoreCommand(savedReplies, "saved") > scoreCommand(titlePrefixedRow, "saved"),
  "a category leading with the shared word outranks a root row on weight alone"
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
