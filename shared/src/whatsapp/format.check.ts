/**
 * Self-check for the WhatsApp text formatter. Run with:
 *   node shared/src/whatsapp/format.check.ts
 */
import assert from "node:assert/strict";
import { formatWhatsAppText } from "./format.ts";

assert.equal(formatWhatsAppText("*Hi* _there_ ~old~ `x`"), "<b>Hi</b> <i>there</i> <s>old</s> <code>x</code>");
assert.equal(formatWhatsAppText("a\nb"), "a<br>b");
assert.equal(formatWhatsAppText("<img src=x onerror=alert(1)>"), "&lt;img src=x onerror=alert(1)&gt;");
assert.equal(formatWhatsAppText("order_id_here"), "order_id_here");
assert.equal(
  formatWhatsAppText("see https://x.io/a_b_c now"),
  'see <a href="https://x.io/a_b_c" target="_blank" rel="noopener noreferrer" class="underline">https://x.io/a_b_c</a> now'
);
assert.ok(!formatWhatsAppText('https://x.io/"><script>').includes("<script>"));
assert.equal(formatWhatsAppText(null), "");
console.log("format.check: ok");
