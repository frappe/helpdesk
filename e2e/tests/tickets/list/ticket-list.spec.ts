import type { Api } from "../../../helpers/api";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import {
  TicketList,
  resetDefaultTicketView,
} from "../../../helpers/list";
import { personas } from "../../../helpers/personas";

usePersona("manager");

test.beforeEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

test.afterEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

test("filters and quick filters narrow the list and clear back", async ({
  page,
  api,
  apiAs,
}) => {
  const id = uid();
  const customer = await apiAs("customer");
  const high = await raiseTicket(customer, `${id} high`);
  const low = await raiseTicket(customer, `${id} low`);
  await api.update("HD Ticket", high.name, { priority: "High" });
  await api.update("HD Ticket", low.name, { priority: "Low" });
  const org = `E2E Org ${id}`;
  await api.insert("HD Customer", { customer_name: org });
  await api.update("HD Ticket", low.name, { customer: org });

  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(id);
  await expect(list.rows()).toHaveCount(2);

  await list.addFilter("Priority", "High");
  await expect(list.rows()).toHaveCount(1);
  await expect(list.row(`${id} high`)).toBeVisible();

  const popover = page.getByRole("dialog", { name: "Filter" });
  await popover
    .locator(".group", { hasText: "Priority is High" })
    .getByRole("button", { name: "Remove filter" })
    .click();
  await expect(list.rows()).toHaveCount(2);
  await page.keyboard.press("Escape");

  await page.getByRole("combobox", { name: "Customer" }).click();
  await page.getByRole("option", { name: org }).click();
  await expect(list.rows()).toHaveCount(1);
  await expect(list.row(`${id} low`)).toBeVisible();

  await page.getByRole("button", { name: "Filter" }).click();
  await popover.getByRole("button", { name: "Clear all" }).click();
  await expect(page.getByRole("textbox", { name: "Subject" })).toHaveValue("");
  await expect(list.rows().nth(2)).toBeVisible();
});

test("a date quick filter keeps its value and narrows the list", async ({
  page,
  api,
  apiAs,
}) => {
  const id = uid();
  const customer = await apiAs("customer");
  await raiseTicket(customer, `${id} today`);
  const old = await raiseTicket(customer, `${id} old`);
  await api.update("HD Ticket", old.name, { opening_date: "2020-01-15" });
  const setter = await api.insert("Property Setter", {
    doctype_or_field: "DocField",
    doc_type: "HD Ticket",
    field_name: "opening_date",
    property: "in_standard_filter",
    property_type: "Check",
    value: "1",
  });
  try {
    // The meta cache is cleared before the setter commits, so a concurrent read can re-cache it stale.
    await expect
      .poll(async () => {
        const filters = await api.call("helpdesk.api.doc.get_quick_filters", { doctype: "HD Ticket" });
        const found = filters.some((filter: { name: string }) => filter.name === "opening_date");
        if (!found) await api.update("Property Setter", setter.name, { value: "1" });
        return found;
      })
      .toBe(true);
    const list = new TicketList(page);
    await list.goto();
    await list.searchSubject(id);
    await expect(list.rows()).toHaveCount(2);

    const dateFilter = page.getByRole("combobox", { name: "Opening Date" });
    await dateFilter.click();
    await page.getByRole("gridcell", { name: /\(Today\)/ }).click();
    await expect(list.rows()).toHaveCount(1);
    await expect(list.row(`${id} today`)).toBeVisible();
    await expect(dateFilter).not.toHaveValue("");
  } finally {
    await api.delete("Property Setter", setter.name);
  }
});

test("sort by a picked field, flip direction and clear", async ({ page, apiAs }) => {
  const id = uid();
  const customer = await apiAs("customer");
  for (const word of ["bravo", "alpha", "charlie"]) {
    await raiseTicket(customer, `${id} ${word}`);
  }
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(id);
  await expect(list.rows()).toHaveCount(3);
  const order = async () =>
    (await list.rows().allInnerTexts()).map((text) =>
      ["alpha", "bravo", "charlie"].find((word) => text.includes(`${id} ${word}`))
    );

  await page.getByRole("button", { name: "Last Modified" }).click();
  const sortPopover = page.getByRole("dialog", { name: "Last Modified" });
  await sortPopover.getByRole("button", { name: "Last Modified" }).click();
  await page.getByRole("option", { name: "Subject", exact: true }).click();
  await expect.poll(order).toEqual(["charlie", "bravo", "alpha"]);

  await page.getByRole("dialog", { name: "Subject" }).locator("button").first().click();
  await expect.poll(order).toEqual(["alpha", "bravo", "charlie"]);

  await page.getByRole("button", { name: "Clear Sort" }).click();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Sort", exact: true })).toBeVisible();
});

test("an added datetime column renders relative time and can be removed", async ({
  page,
  apiAs,
}) => {
  const subject = `${uid()} columns`;
  await raiseTicket(await apiAs("customer"), subject);
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(subject);
  await expect(list.rows()).toHaveCount(1);
  const row = list.row(subject);
  await expect(row).not.toContainText(/ago.*ago/);

  await page.getByRole("button", { name: "Columns" }).click();
  await page.getByRole("button", { name: "Add Column" }).click();
  await page.getByPlaceholder("Select option").fill("Last Modified");
  await page.getByRole("option", { name: "Last Modified", exact: true }).click();
  await page.keyboard.press("Escape");
  // Regression: the column was saved with type "option" and showed the raw value.
  await expect(row).toContainText(/ago.*ago/);
  await expect(row).not.toContainText(/\d{4}-\d{2}-\d{2}/);

  await page.getByRole("button", { name: "Columns" }).click();
  await page
    .getByRole("dialog", { name: "Columns" })
    .locator(".cursor-grab", { hasText: "Last Modified" })
    .getByRole("button")
    .last()
    .click();
  await expect(row).not.toContainText(/ago.*ago/);
});

test("page length and load more page through the list", async ({ page, apiAs }) => {
  const id = uid();
  const customer = await apiAs("customer");
  for (let index = 0; index < 21; index++) {
    await raiseTicket(customer, `${id} page ${index}`);
  }
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(id);
  await expect(list.rows()).toHaveCount(20);

  await page.getByRole("radio", { name: "50" }).click();
  await expect(list.rows()).toHaveCount(21);

  await page.getByRole("radio", { name: "20" }).click();
  await expect(list.rows()).toHaveCount(20);
  await page.getByRole("button", { name: "Load More" }).click();
  await expect(list.rows()).toHaveCount(21);
});

test("clicking an assignee avatar filters the list by that agent", async ({
  page,
  api,
  apiAs,
}) => {
  const id = uid();
  const customer = await apiAs("customer");
  const { agent, agent2 } = personas;
  const assignments = {
    solo: [agent.email],
    other: [agent2.email],
    both: [agent.email, agent2.email],
  };
  for (const [label, users] of Object.entries(assignments)) {
    const ticket = await raiseTicket(customer, `${id} ${label}`);
    await assign(api, ticket.name, users);
  }
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(id);
  await expect(list.rows()).toHaveCount(3);

  // Regression: a single assignee arrives as a string and the click did nothing.
  await list.row(`${id} solo`).locator(`.user-avatar[data-name="${agent.email}"]`).click();
  await expect(list.rows()).toHaveCount(2);
  await expect(list.row(`${id} other`)).toHaveCount(0);

  // the avatar filter is auto saved to the default view, so a reload would keep it
  await list.clearFilters();
  await list.searchSubject(id);
  await expect(list.rows()).toHaveCount(3);
  await list.row(`${id} both`).locator(`.user-avatar[data-name="${agent2.email}"]`).click();
  await expect(list.rows()).toHaveCount(2);
  await expect(list.row(`${id} solo`)).toHaveCount(0);
});

test("bulk edit, assign and reply act on every selected ticket", async ({
  page,
  api,
  apiAs,
}) => {
  const id = uid();
  const customer = await apiAs("customer");
  const first = await raiseTicket(customer, `${id} first`);
  const second = await raiseTicket(customer, `${id} second`);
  const names = [first.name, second.name];
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(id);
  await expect(list.rows()).toHaveCount(2);

  await list.select(`${id} first`, `${id} second`);
  await list.selectionBar().getByRole("button", { name: "Assign" }).click();
  const assignDialog = page.getByRole("dialog", { name: "Assign" });
  await assignDialog.getByRole("button", { name: "Select agents" }).click();
  const picker = page.getByRole("dialog", { name: "Select agents" });
  await picker.getByRole("textbox").fill(personas.agent2.firstName);
  await picker.getByRole("button", { name: new RegExp(personas.agent2.firstName) }).click();
  await page.keyboard.press("Escape");
  await assignDialog.getByRole("button", { name: "Assign 2 tickets" }).click();
  await expect(page.getByText("Assigned 2 ticket(s)")).toHaveCount(1);
  for (const name of names) {
    await expect.poll(() => assignees(api, name)).toContain(personas.agent2.email);
  }

  await list.select(`${id} first`, `${id} second`);
  await list.selectionMenu("Edit");
  const editDialog = page.getByRole("dialog", { name: "Edit" });
  await editDialog.getByRole("combobox").click();
  await page.getByRole("option", { name: "Priority", exact: true }).click();
  await editDialog.getByRole("combobox").nth(1).click();
  await page.getByRole("option", { name: "Urgent" }).click();
  await editDialog.getByRole("button", { name: "Update 2 tickets" }).click();
  await expect(page.getByText("Updated 2 tickets")).toHaveCount(1);
  for (const name of names) {
    await expect.poll(async () => (await api.get("HD Ticket", name)).priority).toBe("Urgent");
  }

  await list.select(`${id} first`, `${id} second`);
  await list.selectionBar().getByRole("button", { name: "Reply" }).click();
  const replyDialog = page.getByRole("dialog");
  await replyDialog.locator("[contenteditable=true]").fill(`${id} bulk reply`);
  await replyDialog.getByRole("button", { name: /Send|Reply/ }).last().click();
  for (const name of names) {
    await expect.poll(() => replyCount(api, name, id)).toBe(1);
  }
});

test("selected tickets export as CSV", async ({ page, apiAs }) => {
  const subject = `${uid()} export`;
  await raiseTicket(await apiAs("customer"), subject);
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(subject);
  await list.select(subject);

  await list.selectionMenu("Export");
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("combobox").click();
  await page.getByRole("option", { name: "CSV" }).click();
  const download = page.waitForEvent("download");
  await dialog.getByRole("button", { name: "Download" }).click();
  const file = await download;
  expect(file.suggestedFilename()).toMatch(/\.csv$/);
  const content = await (await file.createReadStream()).toArray();
  expect(Buffer.concat(content).toString()).toContain(subject);
});

async function assign(api: Api, name: string, users: string[]) {
  await api.call("frappe.desk.form.assign_to.add", {
    doctype: "HD Ticket",
    name,
    assign_to: JSON.stringify(users),
  });
}

async function assignees(api: Api, name: string) {
  const todos = await api.list("ToDo", {
    fields: ["allocated_to"],
    filters: { reference_type: "HD Ticket", reference_name: name, status: "Open" },
  });
  return todos.map((todo) => todo.allocated_to);
}

async function replyCount(api: Api, name: string, text: string) {
  const replies = await api.list("Communication", {
    fields: ["content"],
    filters: { reference_doctype: "HD Ticket", reference_name: name, sent_or_received: "Sent" },
  });
  return replies.filter((reply) => reply.content.includes(text)).length;
}
