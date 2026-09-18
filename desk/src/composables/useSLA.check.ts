/**
 * Self-check for SLA deadline comparisons across timezones. Run with:
 *   node run-check.mjs src/composables/useSLA.check.ts
 * (goes through Vite because useSLA imports frappe-ui; no test framework needed.)
 */
import assert from "node:assert/strict";
import { dayjs, setConfig } from "frappe-ui";
import { ref } from "vue";
import { useSLA } from "./useSLA";

const SITE_TIMEZONE = "Asia/Riyadh";
const SERVER_FORMAT = "YYYY-MM-DD HH:mm:ss";

// response_by / resolution_by arrive as naive strings on the site's wall clock.
function siteDeadline(minutesFromNow: number): string {
  return dayjs()
    .tz(SITE_TIMEZONE)
    .add(minutesFromNow, "minute")
    .format(SERVER_FORMAT);
}

function metricsFor(deadline: string) {
  const ticket = ref({
    doc: { sla: "Default", response_by: deadline, resolution_by: deadline },
  });
  const { firstResponse, resolution } = useSLA(ticket);
  return { firstResponse: firstResponse.value!, resolution: resolution.value! };
}

setConfig("systemTimezone", SITE_TIMEZONE);

// Agent east of the site (+5:30 vs +3). Reading the site's wall clock as the
// agent's own clock puts every deadline 2h30m in the past, so a deadline ten
// minutes away used to paint a red "Failed" badge the moment a ticket was made.
setConfig("localTimezone", "Asia/Kolkata");
let { firstResponse, resolution } = metricsFor(siteDeadline(10));
assert.equal(
  firstResponse.state,
  "due",
  "a future deadline must not read as overdue"
);
assert.equal(resolution.state, "due");
assert.match(firstResponse.value, /^Due in /);

// Agent west of the site (+1 vs +3). The same mistake now pushes deadlines two
// hours into the future, so a breach that already happened kept counting down.
setConfig("localTimezone", "Europe/London");
({ firstResponse, resolution } = metricsFor(siteDeadline(-10)));
assert.equal(
  firstResponse.state,
  "overdue",
  "a passed deadline must read as overdue"
);
assert.equal(resolution.state, "overdue");
assert.match(firstResponse.value, /^Overdue by /);

console.log("useSLA: all checks passed");
