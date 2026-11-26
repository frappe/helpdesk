import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { TicketList, resetDefaultTicketView } from "../../../helpers/list";
import { personas } from "../../../helpers/personas";

usePersona("manager");

test.beforeEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

test.afterEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

test("pasting ticket IDs into an In filter selects them all and narrows the list", async ({
  page,
  context,
  apiAs,
}) => {
  const id = uid();
  const customer = await apiAs("customer");
  const tickets = [];
  for (const n of [1, 2, 3, 4, 5]) tickets.push(await raiseTicket(customer, `${id} ${n}`));
  const picked = tickets.slice(0, 4).map((ticket) => String(ticket.name));

  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(id);
  await expect(list.rows()).toHaveCount(5);

  await list.chooseFilterField("ID");
  await list.chooseFilterOperator("In");
  const popover = list.filterPopover();

  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.evaluate((text) => navigator.clipboard.writeText(text), picked.join(", "));
  await popover.getByPlaceholder("Search...").press("ControlOrMeta+V");

  await expect(list.rows()).toHaveCount(4);
  await expect(list.row(`${id} 5`)).toHaveCount(0);
  await expect(popover.locator("[role=option][aria-selected=true]")).toHaveCount(4);

  await page.keyboard.press("Escape");
  await page.getByRole("button", { name: "Filter", exact: true }).click();
  await expect(popover).toContainText(`ID in ${picked.slice(0, 3).join(", ")} and 1 other`);
});

test("the clear all X empties the filters and closes the popover", async ({
  page,
  api,
  apiAs,
}) => {
  const customer = await apiAs("customer");
  const ticket = await raiseTicket(customer);
  await api.update("HD Ticket", ticket.name, { priority: "High" });

  const list = new TicketList(page);
  await list.goto();
  await list.addFilter("Priority", "High");
  const popover = list.filterPopover();
  await expect(popover).toContainText("Priority is High");

  const clearAll = page.getByRole("button", { name: "Clear all Filter" });
  await clearAll.click();
  await expect(popover).toBeHidden();
  await expect(clearAll).toBeHidden();

  await page.keyboard.press("f");
  await expect(popover).toBeVisible();
});
