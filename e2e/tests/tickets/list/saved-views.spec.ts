import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { TicketList, resetDefaultTicketView } from "../../../helpers/list";
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
