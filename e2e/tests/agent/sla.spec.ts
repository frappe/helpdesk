import type { Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { raiseTicket } from "../../helpers/factories";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { personas, type PersonaKey } from "../../helpers/personas";

type PageAs = (key: PersonaKey) => Promise<Page>;

usePersona("agent");

test("first response counts down, then reads Fulfilled after the agent replies", async ({
  page,
  api,
  apiAs,
  pageAs,
}) => {
  const subject = `E2E SLA ${uid()}`;
  const ticket = await raiseTicket(await apiAs("customer"), subject);
  expect((await api.get("HD Ticket", ticket.name)).agreement_status).toBe(
    "First Response Due"
  );

  await page.goto(`/helpdesk/tickets/${ticket.name}`);
  await expect(sidebarValue(page, "First Response")).toHaveText(/^Due in /);
  const row = await listRow(api, pageAs, ticket.name);
  await expect(row).toContainText(/\d+h \d+m|\d+ days?/);
  await expect(row).not.toContainText("Fulfilled");

  await replyAsAgent(await apiAs("agent"), ticket.name);

  await page.goto(`/helpdesk/tickets/${ticket.name}`);
  await expect(sidebarValue(page, "First Response")).toHaveText(/^Fulfilled/);
  await expect(await listRow(api, pageAs, ticket.name)).toContainText("Fulfilled");
});

test("a ticket on hold stays Paused after its deadlines pass", async ({
  api,
  apiAs,
  pageAs,
}) => {
  const subject = `E2E SLA hold ${uid()}`;
  const ticket = await raiseTicket(await apiAs("customer"), subject);
  await api.update("HD Ticket", ticket.name, { status: "Replied" });

  // Rewind the clock: SLA started a week ago, answered and held 10 minutes in.
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000;
  const heldAt = await siteDatetime(api, weekAgo + 10 * 60 * 1000);
  await api.update("HD Ticket", ticket.name, {
    service_level_agreement_creation: await siteDatetime(api, weekAgo),
    first_responded_on: heldAt,
    on_hold_since: heldAt,
  });
  await api.update("HD Ticket", ticket.name, { subject: `${subject} edited` });

  const saved = await api.get("HD Ticket", ticket.name);
  expect(saved.resolution_by < (await siteDatetime(api, Date.now()))).toBe(true);
  expect(saved.agreement_status).toBe("Paused");
  await expect(await listRow(api, pageAs, ticket.name)).toContainText("Paused");
});

test("analytics tab counts the opening message once", async ({ page, apiAs, ticket }) => {
  await replyAsAgent(await apiAs("agent"), ticket.name);

  await page.goto(`/helpdesk/tickets/${ticket.name}`);
  await page.getByRole("tab", { name: "Analytics" }).click();

  await expect(page.getByText("Created", { exact: true }).first()).toBeVisible();
  await expect(summaryValue(page, "Customer messages")).toHaveText("1");
  await expect(summaryValue(page, "Agent replies")).toHaveText("1");
});

async function replyAsAgent(agent: Api, ticket: string) {
  await agent.call("run_doc_method", {
    dt: "HD Ticket",
    dn: ticket,
    method: "reply_via_agent",
    args: { message: "<p>E2E agent reply</p>" },
  });
}

function sidebarValue(page: Page, label: string) {
  return page
    .locator("div.min-h-7")
    .filter({ has: page.getByText(label, { exact: true }) })
    .locator("span.truncate");
}

function summaryValue(page: Page, label: string) {
  return page
    .locator("div.justify-between")
    .filter({ has: page.getByText(label, { exact: true }) })
    .locator("span")
    .last();
}

/** The ticket's list row, seen by the manager with their saved view reset. */
async function listRow(api: Api, pageAs: PageAs, ticket: string) {
  const saved = await api.list("HD View", {
    filters: { user: personas.manager.email, dt: "HD Ticket", is_default: 1 },
  });
  for (const view of saved) await api.delete("HD View", view.name);
  const page = await pageAs("manager");
  const filters = encodeURIComponent(JSON.stringify({ name: ticket }));
  await page.goto(`/helpdesk/tickets?filters=${filters}`);
  return page.getByRole("link", { name: new RegExp(`^${ticket} `) });
}

/** Frappe stores naive datetimes in the site's timezone. */
async function siteDatetime(api: Api, epoch: number) {
  const settings = await api.get("System Settings", "System Settings");
  return new Date(epoch)
    .toLocaleString("sv-SE", { timeZone: settings.time_zone })
    .slice(0, 19);
}
