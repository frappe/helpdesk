/**
 * Self-check for the palette's filter merge. Run with:
 *   node_modules/.bin/tsx src/components/listViewFilters.check.ts
 * (tsx lives in the repo root node_modules; no test framework needed.)
 */
import assert from "node:assert/strict";
import {
  applyListFilters,
  listFilters,
  type FilterCondition,
} from "./listViewFilters";

let applied: FilterCondition[] = [];

function mountList(current: FilterCondition[]) {
  applied = [];
  listFilters.value = {
    current: () => current,
    apply: (filters) => (applied = filters),
  };
}

// No list mounted: the caller has to fall back to navigating.
listFilters.value = null;
assert.equal(applyListFilters([["status", "=", "Open"]]), false);

// Filters on different fields layer, rather than replacing each other — this is
// the whole bug: two palette filters used to leave only the second applied.
mountList([["status", "=", "Open"]]);
assert.equal(applyListFilters([["priority", "=", "High"]]), true);
assert.deepEqual(applied, [
  ["status", "=", "Open"],
  ["priority", "=", "High"],
]);

// A second filter on the same field replaces the first, never stacks.
mountList([
  ["status", "=", "Open"],
  ["priority", "=", "Low"],
]);
applyListFilters([["priority", "=", "High"]]);
assert.deepEqual(applied, [
  ["status", "=", "Open"],
  ["priority", "=", "High"],
]);

// Re-applying the identical filter is idempotent, not a no-op dead key.
mountList([["status", "=", "Open"]]);
assert.equal(applyListFilters([["status", "=", "Open"]]), true);
assert.deepEqual(applied, [["status", "=", "Open"]]);

// Clearing drops everything, matching the filter popover's "Clear all".
mountList([["status", "=", "Open"]]);
applyListFilters([]);
assert.deepEqual(applied, []);

console.log("listViewFilters: all checks passed");
