import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { TicketList, resetDefaultTicketView } from "../../../helpers/list";
import { personas } from "../../../helpers/personas";

usePersona("manager");

test.afterEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

test("tickets group by priority with a count per group and a total, kept on reload", async ({
  page,
  api,
  apiAs,
}) => {
  const token = uid();
  const customer = await apiAs("customer");
  const priorities = {
    [`E2E high ${token}`]: "High",
    [`E2E high again ${token}`]: "High",
    [`E2E low ${token}`]: "Low",
  };
  // one at a time, since parallel inserts deadlock
  for (const [subject, priority] of Object.entries(priorities)) {
    const ticket = await raiseTicket(customer, subject);
    await api.update("HD Ticket", ticket.name, { priority });
  }

  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(token);
  await groupBy(page, "Priority", { totals: true });

  await expect(groupRow(page, "High")).toContainText("2");
  await expect(groupRow(page, "Low")).toContainText("1");
  await expect(page.locator("[data-totals]")).toContainText("3");
  await expect(list.rows().filter({ hasText: token })).toHaveCount(0);
  await expect.poll(() => savedGroupBy(api)).toContain("priority");

  await page.reload();
  await expect(page.getByRole("button", { name: "Group", exact: true })).toHaveText(
    "Grouped by Priority"
  );
  await expect(groupRow(page, "High")).toContainText("2");

  await page.getByRole("button", { name: "Clear grouping" }).click();
  await expect(list.row(`E2E low ${token}`)).toBeVisible();
  await expect.poll(() => savedGroupBy(api)).toBeFalsy();
});

test("grouped tickets export as CSV with one row per group", async ({ page, api, apiAs }) => {
  const token = uid();
  const customer = await apiAs("customer");
  for (const subject of [`E2E export ${token}`, `E2E export again ${token}`]) {
    const ticket = await raiseTicket(customer, subject);
    await api.update("HD Ticket", ticket.name, { priority: "Urgent" });
  }
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(token);
  await groupBy(page, "Priority");
  await expect(groupRow(page, "Urgent")).toContainText("2");

  await page.getByRole("button", { name: "Export" }).click();
  const download = page.waitForEvent("download");
  await page.getByRole("menuitem", { name: "CSV" }).click();
  const file = await download;
  expect(file.suggestedFilename()).toMatch(/\.csv$/);
  const content = Buffer.concat(await (await file.createReadStream()).toArray()).toString();
  expect(content).toMatch(/"?Urgent"?,"?2"?/);
  expect(content).not.toContain(token);
});

test.describe("customer portal", () => {
  usePersona("customer");

  test("customers get no grouping on their ticket list", async ({ page }) => {
    await page.goto("/helpdesk/my-tickets");
    await expect(page.getByRole("button", { name: "Filter", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Group", exact: true })).toHaveCount(0);
  });
});

/** Group the list by one field from the Group popover and wait for the groups. */
async function groupBy(page: Page, field: string, { totals = false } = {}) {
  await page.getByRole("button", { name: "Group", exact: true }).click();
  await page.getByRole("combobox", { name: "Select field" }).click();
  await page.getByRole("option", { name: field, exact: true }).click();
  if (totals) await page.getByRole("switch", { name: "Show totals" }).click();
  const loaded = page.waitForResponse(/get_grouped_list/);
  await page.getByRole("button", { name: "Apply" }).click();
  await loaded;
}

function groupRow(page: Page, value: string) {
  return page
    .getByRole("row")
    .filter({ has: page.getByRole("cell", { name: value, exact: true }) });
}

async function savedGroupBy(api: Api) {
  const [view] = await api.list("HD View", {
    fields: ["list_group_by"],
    filters: { user: personas.manager.email, dt: "HD Ticket", is_default: 1 },
  });
  return view?.list_group_by;
}
