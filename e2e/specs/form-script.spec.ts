import type { Page } from "@playwright/test";
import { raiseTicket } from "../support/factories";
import { expect, test } from "../support/fixtures";
import {
  FormScripts,
  TEMPLATE,
  clicksOn,
  countingAction,
  ensureTemplate,
} from "../support/form-script";

const NEW_WITH_TEMPLATE = `/helpdesk/tickets/new/${encodeURIComponent(TEMPLATE)}`;

let scripts: FormScripts;

test.beforeEach(({ api }) => {
  scripts = new FormScripts(api);
});

test.afterEach(async () => {
  await scripts.removeAll();
});

test("a flat action fires exactly once on each page", async ({ apiAs, pageAs }) => {
  await scripts.create(countingAction("E2E Agent Ticket"));
  await scripts.create(countingAction("E2E Portal Ticket"), { portal: true });
  await scripts.create(countingAction("E2E Agent New"), { newPage: true });
  const ticket = await raiseTicket(await apiAs("customer"));

  const surfaces = [
    { persona: "agent", url: `/helpdesk/tickets/${ticket.name}`, label: "E2E Agent Ticket" },
    { persona: "customer", url: `/helpdesk/my-tickets/${ticket.name}`, label: "E2E Portal Ticket" },
    { persona: "agent", url: "/helpdesk/tickets/new", label: "E2E Agent New" },
  ] as const;
  for (const surface of surfaces) {
    const page = await pageAs(surface.persona);
    await page.goto(surface.url);
    await page.getByRole("button", { name: surface.label }).click();
    await expect.poll(() => clicksOn(page)).toBe(1);
  }
});

test("grouped actions render, including the legacy items shape", async ({ apiAs, pageAs }) => {
  await scripts.create(
    countingAction(
      "E2E Flat",
      `, { group: "E2E Group", options: [{ label: "E2E Option", onClick: () => {} }] },
      { group: "E2E Legacy", items: [{ label: "E2E Legacy Item", onClick: () => {
        window.__e2eClicks = (window.__e2eClicks || 0) + 1;
      } }] },
      { group: "E2E Labelled", buttonLabel: "E2E Menu", label: "E2E Menu Item", onClick: () => {} }`
    )
  );
  const ticket = await raiseTicket(await apiAs("customer"));
  const page = await pageAs("agent");
  await page.goto(`/helpdesk/tickets/${ticket.name}`);

  await page.getByRole("button", { name: "E2E Menu" }).click();
  await expect(page.getByRole("menuitem", { name: "E2E Menu Item" })).toBeVisible();
  await page.keyboard.press("Escape");

  await openMoreMenu(page);
  await expect(page.getByRole("menuitem", { name: "E2E Option" })).toBeVisible();
  await page.getByRole("menuitem", { name: "E2E Legacy Item" }).click();
  await expect.poll(() => clicksOn(page)).toBe(1);
});

test("actions can update fields, call the server, open dialogs and route", async ({
  api,
  apiAs,
  pageAs,
}) => {
  await scripts.create(`return { actions: [
    { label: "E2E Set Priority", onClick: () => ctx.updateField("priority", "High") },
    { label: "E2E Call", onClick: () => ctx.call("frappe.client.get_count", { doctype: "HD Ticket Priority" })
      .then((count) => { window.__e2eCount = count; }) },
    { label: "E2E Dialog", onClick: () => ctx.$dialog({ title: "E2E Dialog Title", message: "From a form script" }) },
    { label: "E2E Route", onClick: () => ctx.router.push({ name: "TicketsAgent" }) },
  ] };`);
  const ticket = await raiseTicket(await apiAs("customer"));
  const page = await pageAs("agent");
  await page.goto(`/helpdesk/tickets/${ticket.name}`);

  await page.getByRole("button", { name: "E2E Set Priority" }).click();
  await expect.poll(async () => (await api.get("HD Ticket", ticket.name)).priority).toBe("High");

  await page.getByRole("button", { name: "E2E Call" }).click();
  await expect.poll(() => page.evaluate(() => (window as any).__e2eCount)).toBeGreaterThan(0);

  await page.getByRole("button", { name: "E2E Dialog" }).click();
  await expect(page.getByRole("dialog").getByText("E2E Dialog Title")).toBeVisible();
  await page.keyboard.press("Escape");

  await page.getByRole("button", { name: "E2E Route" }).click();
  await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
});

test("toast shows a message", async ({ apiAs, pageAs }) => {
  await scripts.create(`return { actions: [
    { label: "E2E Toast", onClick: () => ctx.toast.success("E2E plain toast") },
  ] };`);
  const ticket = await raiseTicket(await apiAs("customer"));
  const page = await pageAs("agent");
  await page.goto(`/helpdesk/tickets/${ticket.name}`);

  await page.getByRole("button", { name: "E2E Toast" }).click();
  await expect(page.getByText("E2E plain toast", { exact: true })).toBeVisible();
});

test("createToast reads duration as seconds", async ({ apiAs, pageAs }) => {
  // Form scripts pass seconds; vue-sonner reads milliseconds.
  await scripts.create(`return { actions: [
    { label: "E2E Timed Toast", onClick: () => ctx.createToast({ message: "E2E timed toast", type: "success", duration: 5 }) },
  ] };`);
  const ticket = await raiseTicket(await apiAs("customer"));
  const page = await pageAs("agent");
  await page.goto(`/helpdesk/tickets/${ticket.name}`);

  await page.getByRole("button", { name: "E2E Timed Toast" }).click();
  await expect(page.getByText("E2E timed toast", { exact: true })).toBeVisible();
  // A 5 second toast must still be up after 1.5s; read as ms it is long gone.
  await page.waitForTimeout(1500);
  await expect(page.getByText("E2E timed toast", { exact: true })).toBeVisible();
});

test.describe("new ticket form", () => {
  test.beforeEach(async ({ api }) => {
    await ensureTemplate(api);
  });

  test("onChange narrows a dependent field with applyFilters", async ({ pageAs }) => {
    await scripts.create(
      `return { actions: [], onChange: { e2e_trigger: (value) =>
        ctx.applyFilters("e2e_choice", value === "Show" ? ["Alpha", "Beta"] : null) } };`,
      { newPage: true }
    );
    const page = await pageAs("agent");
    await page.goto(NEW_WITH_TEMPLATE);

    await pick(page, "E2E trigger", "Show");
    await field(page, "E2E choice").getByRole("combobox").click();
    await expect(page.getByRole("option")).toHaveText(["Alpha", "Beta"]);
    await page.keyboard.press("Escape");

    await pick(page, "E2E trigger", "Hide");
    await expect(field(page, "E2E choice").getByRole("combobox")).toBeDisabled();
  });

  test("depends_on and mandatory_depends_on follow other values", async ({ pageAs }) => {
    const page = await pageAs("agent");
    await page.goto(NEW_WITH_TEMPLATE);
    await expect(field(page, "E2E shown")).toHaveCount(0);
    await expect(field(page, "E2E needed").getByText("*")).toHaveCount(0);

    await pick(page, "E2E trigger", "Show");
    await expect(field(page, "E2E shown")).toBeVisible();
    await expect(field(page, "E2E needed").getByText("*")).toBeVisible();
  });

  test.fixme("read_only_depends_on locks a field", async ({ pageAs }) => {
    // get_fields in hd_ticket_template/api.py never selects read_only_depends_on.
    const page = await pageAs("agent");
    await page.goto(NEW_WITH_TEMPLATE);
    await pick(page, "E2E trigger", "Show");
    await expect(field(page, "E2E locked").getByRole("textbox")).toBeDisabled();
  });
});

test.describe("scoping", () => {
  test("portal flag keeps agent and portal scripts apart", async ({ apiAs, pageAs }) => {
    await scripts.create(countingAction("E2E Agent Only"));
    await scripts.create(countingAction("E2E Portal Only"), { portal: true });
    const ticket = await raiseTicket(await apiAs("customer"));

    const agent = await pageAs("agent");
    await agent.goto(`/helpdesk/tickets/${ticket.name}`);
    await expect(agent.getByRole("button", { name: "E2E Agent Only" })).toBeVisible();
    await expect(agent.getByRole("button", { name: "E2E Portal Only" })).toHaveCount(0);

    const customer = await pageAs("customer");
    await customer.goto(`/helpdesk/my-tickets/${ticket.name}`);
    await expect(customer.getByRole("button", { name: "E2E Portal Only" })).toBeVisible();
    await expect(customer.getByRole("button", { name: "E2E Agent Only" })).toHaveCount(0);
  });

  test("a disabled script never runs and two enabled scripts combine", async ({
    apiAs,
    pageAs,
  }) => {
    await scripts.create(countingAction("E2E First"));
    await scripts.create(countingAction("E2E Second"));
    await scripts.create(countingAction("E2E Disabled"), { enabled: false });
    const ticket = await raiseTicket(await apiAs("customer"));

    const page = await pageAs("agent");
    await page.goto(`/helpdesk/tickets/${ticket.name}`);
    await expect(page.getByRole("button", { name: "E2E First" })).toBeVisible();
    await expect(page.getByRole("button", { name: "E2E Second" })).toBeVisible();
    await expect(page.getByRole("button", { name: "E2E Disabled" })).toHaveCount(0);
  });

  test.fixme("new ticket scripts respect the portal flag", async ({ pageAs }) => {
    // hd_ticket_template/api.py get_one hardcodes is_customer_portal=False.
    await scripts.create(countingAction("E2E Agent New Only"), { newPage: true });
    await scripts.create(countingAction("E2E Portal New Only"), { newPage: true, portal: true });

    const customer = await pageAs("customer");
    await customer.goto("/helpdesk/my-tickets/new");
    await expect(customer.getByRole("button", { name: "E2E Portal New Only" })).toBeVisible();
    await expect(customer.getByRole("button", { name: "E2E Agent New Only" })).toHaveCount(0);
  });
});

function field(page: Page, label: string) {
  return page.locator(".space-y-1\\.5").filter({
    has: page.getByText(new RegExp(`^${label}\\b`)),
  });
}

async function pick(page: Page, label: string, option: string) {
  await field(page, label).getByRole("combobox").click();
  await page.getByRole("option", { name: option, exact: true }).click();
}

async function openMoreMenu(page: Page) {
  await page.getByRole("banner").getByRole("button").last().click();
}
