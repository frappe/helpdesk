/**
 * Self-check for the address parser. Run from `desk/` with:
 *   node src/components/communication-area/addresses.check.ts
 * (Node 22+ strips the types itself; no test framework needed.)
 */
import assert from "node:assert/strict";
import { toRecipient, toRecipientList } from "./addresses.ts";

assert.deepEqual(toRecipient('"Kapoor, Riya" <r@x.io>'), {
  email: "r@x.io",
  label: "Kapoor, Riya",
});
assert.deepEqual(toRecipient("Riya Kapoor <r@x.io>"), {
  email: "r@x.io",
  label: "Riya Kapoor",
});
assert.deepEqual(toRecipient("  r@x.io "), { email: "r@x.io" });
assert.deepEqual(toRecipient("<r@x.io>"), { email: "r@x.io" });
assert.deepEqual(toRecipientList(["a@x.io", "", undefined, "B <b@x.io>"]), [
  { email: "a@x.io" },
  { email: "b@x.io", label: "B" },
]);
console.log("addresses ok");
