import type { Api } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { emailOf } from "../../helpers/personas";
import { setHelpdeskSetting } from "../../helpers/ticket";

const SLA = "HD Service Level Agreement";
const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MINUTE = 60;

usePersona("customer");

const cleanups: (() => Promise<unknown>)[] = [];

test.afterEach(async () => {
  for (const cleanup of cleanups.splice(0).reverse()) await cleanup();
});

test("a break pushes the response target past it", async ({ api }) => {
  const { subject, now } = await createSla(api);
  await setBreak(api, subject, now + 10 * MINUTE, now + 40 * MINUTE);

  const ticket = await createTicket(api, subject);
  expect(ticket.sla).toBe(subject);
  expect(ticket.raised_outside_working_hours).toBe(0);
  // 1h of working time plus the 30m break
  expect(secondsBetween(ticket.service_level_agreement_creation, ticket.response_by)).toBe(90 * MINUTE);
});

for (const [device, viewport] of [
  ["desktop", { width: 1440, height: 900 }],
  ["phone", { width: 390, height: 800 }],
] as const) {
  test.describe(device, () => {
    test.use({ viewport });

    test("a ticket raised during the break shows the outside-hours banner", async ({ page, api }) => {
      cleanups.push(await setHelpdeskSetting(api, "enable_outside_hours_banner", 1));
      const { subject, now } = await createSla(api);
      await setBreak(api, subject, now - 30 * MINUTE, now + 30 * MINUTE);

      const ticket = await createTicket(api, subject);
      expect(ticket.sla).toBe(subject);
      expect(ticket.raised_outside_working_hours).toBe(1);

      await page.goto(`/help/my-tickets/${ticket.name}`);
      await expect(page.getByRole("alert")).toBeVisible();
    });
  });
}

/**
 * An SLA that only this spec's tickets match, working all day today with a
 * 1h response target. Returns the site's clock as seconds since midnight.
 */
async function createSla(api: Api) {
  const subject = `E2E SLA break ${uid()}`;
  const year = new Date().getUTCFullYear();
  await api.insert("HD Service Holiday List", {
    holiday_list_name: subject,
    from_date: `${year - 1}-01-01`,
    to_date: `${year + 1}-12-31`,
  });
  cleanups.push(() => api.delete("HD Service Holiday List", subject));
  const sla = await api.insert(SLA, {
    service_level: subject,
    holiday_list: subject,
    condition: `doc.subject == '${subject}'`,
    rank: 1,
    enabled: 1,
    default_sla: 0,
    apply_sla_for_resolution: 0,
    priorities: ["Low", "Medium", "High", "Urgent"].map((priority) => ({
      priority,
      response_time: 60 * MINUTE,
      default_priority: priority === "Medium" ? 1 : 0,
    })),
    support_and_resolution: WEEKDAYS.map((workday) => ({
      workday,
      start_time: "00:00:00",
      end_time: "23:59:59",
    })),
  });
  cleanups.push(() => api.delete(SLA, subject));
  const time = sla.creation.split(" ")[1];
  const [hours, minutes, seconds] = time.split(":").map(Number);
  const now = hours * 3600 + minutes * MINUTE + Math.floor(seconds);
  test.skip(now < 60 * MINUTE || now > 22 * 60 * MINUTE, "the break would cross midnight on the site's clock");
  return { subject, now };
}

async function setBreak(api: Api, subject: string, start: number, end: number) {
  const sla = await api.get(SLA, subject);
  await api.update(SLA, subject, {
    support_and_resolution: sla.support_and_resolution.map((row) => ({
      ...row,
      break_start: clock(start),
      break_end: clock(end),
    })),
  });
}

async function createTicket(api: Api, subject: string) {
  const ticket = await api.insert("HD Ticket", {
    subject,
    description: `<p>${subject}</p>`,
    raised_by: emailOf("customer"),
  });
  cleanups.push(() => api.delete("HD Ticket", ticket.name));
  return ticket;
}

function clock(seconds: number) {
  return [seconds / 3600, (seconds % 3600) / MINUTE, seconds % MINUTE]
    .map((part) => String(Math.floor(part)).padStart(2, "0"))
    .join(":");
}

/** Both are naive site datetimes, so read them in one zone. */
function secondsBetween(start: string, end: string) {
  const parse = (value: string) => Date.parse(`${value.replace(" ", "T")}Z`);
  return Math.round((parse(end) - parse(start)) / 1000);
}
