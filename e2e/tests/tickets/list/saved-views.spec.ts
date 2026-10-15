import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import {
  TicketList,
  createPinnedTicketView,
  resetDefaultTicketView,
} from "../../../helpers/list";
import { personas } from "../../../helpers/personas";

usePersona("manager");

test.afterEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

test("a saved view can be pinned and unpinned, made public and deleted", async ({
  page,
  api,
}) => {
  const label = `E2E view ${uid()}`;
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(label);
  const view = await list.createView(api, label);
  expect((await api.get("HD View", view)).filters).toContain(label);
  const saved = (field: string) => async () => (await api.get("HD View", view))[field];

  const sidebar = page.getByRole("navigation", { name: "Main" });
  await list.viewAction(label, "Pin View");
  await expect(sidebar.getByRole("button", { name: label })).toBeVisible();
  await expect.poll(saved("pinned")).toBe(1);
  await list.viewAction(label, "Unpin View");
  await expect.poll(saved("pinned")).toBe(0);

  await list.viewAction(label, "Make Public");
  await expect.poll(saved("public")).toBe(1);

  await list.viewAction(label, "Delete");
  await page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();
  await expect.poll(() => api.exists("HD View", { label })).toBeUndefined();
  await expect(sidebar.getByRole("button", { name: label })).toHaveCount(0);
});

test("changing a view's filters and saving them sticks when it is reopened", async ({
  page,
  api,
  apiAs,
}) => {
  const token = uid();
  const customer = await apiAs("customer");
  const first = await raiseTicket(customer, `E2E first ${token}`);
  const second = await raiseTicket(customer, `E2E second ${token}`);
  const label = `E2E view ${token}`;
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(first.subject);
  const view = await list.createView(api, label);

  await list.searchSubject(second.subject);
  await page.getByRole("button", { name: "Save Changes" }).click();
  await expect.poll(async () => (await api.get("HD View", view)).filters).toContain(second.subject);

  await list.goto();
  await page.goto(`/helpdesk/tickets?view=${view}`);
  await expect(list.row(second.subject)).toBeVisible();
  await expect(list.row(first.subject)).toHaveCount(0);
});

test("a view can be duplicated and renamed", async ({ page, api }) => {
  const label = `E2E view ${uid()}`;
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(label);
  const original = await list.createView(api, label);

  await list.viewAction(label, "Duplicate");
  const duplicate = page.getByRole("dialog", { name: "Duplicate View" });
  await expect(duplicate.getByRole("textbox").first()).toHaveValue(`${label} (New)`);
  await duplicate.getByRole("button", { name: "Duplicate" }).click();
  await expect.poll(() => api.exists("HD View", { label: `${label} (New)` })).toBeTruthy();
  const copy = (await api.exists("HD View", { label: `${label} (New)` }))!;
  expect((await api.get("HD View", copy)).filters).toBe((await api.get("HD View", original)).filters);

  const renamed = `E2E view ${uid()} renamed`;
  await list.viewAction(label, "Edit");
  const edit = page.getByRole("dialog", { name: "Edit View" });
  await edit.getByRole("textbox").first().fill(renamed);
  await edit.getByRole("button", { name: "Update" }).click();
  await expect.poll(async () => (await api.get("HD View", original)).label).toBe(renamed);
});

test("public views reach other agents and private ones do not", async ({
  page,
  api,
  pageAs,
}) => {
  const label = `E2E view ${uid()}`;
  const list = new TicketList(page);
  await list.goto();
  await list.searchSubject(label);
  const view = await list.createView(api, label);
  const agentSees = async () => {
    const agentPage = await pageAs("agent");
    await new TicketList(agentPage).goto();
    await agentPage.getByRole("banner").getByRole("button", { name: "List", exact: true }).click();
    const count = await agentPage.getByRole("menuitem", { name: label }).count();
    await agentPage.close();
    return count;
  };

  expect(await agentSees()).toBe(0);
  await list.viewAction(label, "Make Public");
  await expect.poll(async () => (await api.get("HD View", view)).public).toBe(1);
  expect(await agentSees()).toBe(1);

  await list.viewAction(label, "Make Private");
  await page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();
  await expect.poll(async () => (await api.get("HD View", view)).public).toBe(0);
  expect(await agentSees()).toBe(0);
});

test("a standard view can be hidden from and shown in the sidebar", async ({ page, api }) => {
  const standard = (await api.list("HD View", {
    fields: ["name", "label"],
    filters: { is_standard: 1, public: 1, dt: "HD Ticket" },
    limit: 1,
  }))[0];
  const sidebar = page.getByRole("navigation", { name: "Main" });
  const list = new TicketList(page);
  try {
    await list.goto();
    await expect(sidebar.getByRole("button", { name: standard.label })).toBeVisible();

    await list.viewAction(standard.label, "Hide from sidebar");
    await page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();
    await expect(sidebar.getByRole("button", { name: standard.label })).toHaveCount(0);
    await expect.poll(async () => (await api.get("HD View", standard.name)).public).toBe(0);

    await list.viewAction(standard.label, "Show in sidebar");
    await expect(sidebar.getByRole("button", { name: standard.label })).toBeVisible();
  } finally {
    await api.update("HD View", standard.name, { public: 1 });
  }
});

test.describe("the open view is kept in the browser, not the URL", () => {
  let ticket: Record<string, any>;
  let view: Record<string, any>;

  test.beforeEach(async ({ api, apiAs }) => {
    ticket = await raiseTicket(await apiAs("customer"));
    view = await createPinnedTicketView(api, personas.manager.email, ticket.subject);
  });

  test("a view chosen in the sidebar opens without ?view and stays open after a reload", async ({
    page,
  }) => {
    const list = new TicketList(page);
    await list.goto();
    await page.getByRole("navigation", { name: "Main" }).getByRole("button", { name: view.label }).click();
    await expect(list.viewButton(view.label)).toBeVisible();
    await expect(list.rows()).toHaveCount(1);
    await expect(page).toHaveURL(/\/helpdesk\/tickets$/);

    await list.reload();
    await expect(list.viewButton(view.label)).toBeVisible();
    await expect(list.row(ticket.subject)).toBeVisible();
    await expect(list.rows()).toHaveCount(1);
  });

  test("the ticket page breadcrumb shows the open view and Tickets goes back to the default list", async ({
    page,
  }) => {
    const list = new TicketList(page);
    await list.goto();
    await page.getByRole("navigation", { name: "Main" }).getByRole("button", { name: view.label }).click();
    await list.row(ticket.subject).click();
    await expect(page.getByRole("tab", { name: "Activity" })).toBeVisible();
    const crumbs = page.getByRole("banner");
    await expect(crumbs.getByRole("link", { name: view.label })).toBeVisible();

    await crumbs.getByRole("link", { name: "Tickets", exact: true }).click();
    await expect(list.viewButton("List")).toBeVisible();
    await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
    await list.reload();
    await expect(list.viewButton("List")).toBeVisible();
    await expect(list.viewButton(view.label)).toHaveCount(0);
  });

  test("the later of two quick view picks on a ticket page stays open after a reload", async ({
    page,
    api,
  }) => {
    const later = await createPinnedTicketView(api, personas.manager.email, ticket.subject);
    const list = new TicketList(page);
    await page.goto(`/helpdesk/tickets/${ticket.name}`);
    await expect(page.getByRole("tab", { name: "Activity" })).toBeVisible();
    const sidebar = page.getByRole("navigation", { name: "Main" });
    // click both in one task, so the second push cancels the first before it lands
    await sidebar.getByRole("button", { name: view.label }).evaluate(
      (first, second) => {
        first.dispatchEvent(new MouseEvent("click", { bubbles: true }));
        second.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      },
      await sidebar.getByRole("button", { name: later.label }).elementHandle()
    );
    await expect(list.viewButton(later.label)).toBeVisible();

    await list.reload();
    await expect(list.viewButton(later.label)).toBeVisible();
    await expect(list.row(ticket.subject)).toBeVisible();
  });

  test("an old ?view link opens the view and drops view from the URL", async ({ page }) => {
    const list = new TicketList(page);
    await page.goto(`/helpdesk/tickets?view=${view.name}`);
    await expect(list.viewButton(view.label)).toBeVisible();
    await expect(list.row(ticket.subject)).toBeVisible();
    await expect(list.rows()).toHaveCount(1);
    await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
  });

  test("Tickets in the sidebar and deleting the open view fall back to the default list", async ({
    page,
    api,
  }) => {
    const list = new TicketList(page);
    const sidebar = page.getByRole("navigation", { name: "Main" });
    await list.goto();
    await sidebar.getByRole("button", { name: view.label }).click();
    await expect(list.viewButton(view.label)).toBeVisible();
    await sidebar.getByRole("button", { name: "Tickets", exact: true }).click();
    await expect(list.viewButton("List")).toBeVisible();

    await sidebar.getByRole("button", { name: view.label }).click();
    await expect(list.viewButton(view.label)).toBeVisible();
    await list.viewAction(view.label, "Delete");
    await page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();
    await expect.poll(() => api.exists("HD View", { name: view.name })).toBeUndefined();
    await expect(list.viewButton("List")).toBeVisible();
    await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
  });

  test.describe("on a phone", () => {
    test.use({ viewport: { width: 390, height: 844 } });

    test("resetting to the default list after the drawer closes survives a reload", async ({
      page,
    }) => {
      const list = new TicketList(page);
      await page.goto(`/helpdesk/tickets/${ticket.name}`);
      // the drawer toggle is an unlabelled icon button left of the page header
      await page.locator("div:has(+ #app-header) button").click();
      const drawer = page.getByRole("navigation", { name: "Main" });
      await drawer.getByRole("button", { name: view.label }).click();
      await expect(list.viewButton(view.label)).toBeVisible();
      await expect(drawer).toBeHidden();

      await page.getByRole("banner").getByRole("link", { name: "..." }).click();
      await expect(list.viewButton("List")).toBeVisible();
      await list.reload();
      await expect(list.viewButton("List")).toBeVisible();
      await expect(list.viewButton(view.label)).toHaveCount(0);
    });
  });
});
