import type { Api } from "../../helpers/api";
import { expect, test } from "../../helpers/fixtures";
import { FormScripts } from "../../helpers/form-script";
import { snapshotSettings } from "../../helpers/settings";
import { openTicket } from "../../helpers/ticket";

test.describe("field permission notice", () => {
  const NOTICE = "show_ticket_field_permission_notice";
  let restoreSettings: () => Promise<unknown>;

  test.beforeEach(async ({ api }) => {
    restoreSettings = await snapshotSettings(api, [
      NOTICE,
      "show_customer_portal_permission_notice",
    ]);
    // the customer portal notice has its own Learn more button
    await api.update("HD Settings", "HD Settings", {
      [NOTICE]: 1,
      show_customer_portal_permission_notice: 0,
    });
  });

  test.afterEach(async () => {
    await restoreSettings();
  });

  test("a manager sees it until they dismiss it in any tab", async ({ api, pageAs }) => {
    const text = "Some fields are now hidden from customers";
    const otherTab = await pageAs("manager");
    await otherTab.goto("/helpdesk/tickets");
    await expect(otherTab.getByText(text)).toBeVisible();
    const page = await pageAs("manager");
    await page.goto("/helpdesk/tickets");
    const banner = page.getByText(text);
    await expect(banner).toBeVisible();

    await page.getByRole("button", { name: "Learn more" }).click();
    const dialog = page.getByRole("dialog", { name: "Ticket fields have changed" });
    await expect(dialog.getByRole("link", { name: "See how" })).toHaveAttribute(
      "href",
      /perm-levels-in-helpdesk/
    );
    await dialog.getByRole("button", { name: "Got it" }).click();
    await expect(dialog).toHaveCount(0);
    await expect(banner).toHaveCount(0);
    expect((await api.get("HD Settings", "HD Settings"))[NOTICE]).toBe(0);
    await expect(otherTab.getByText(text)).toHaveCount(0);

    await page.reload();
    await page.waitForLoadState("networkidle");
    await expect(banner).toHaveCount(0);
  });

  test("agents and customers never see it", async ({ pageAs }) => {
    for (const [persona, url] of [
      ["agent", "/helpdesk/tickets"],
      ["customer", "/help/customer-tickets"],
    ] as const) {
      const page = await pageAs(persona);
      await page.goto(url);
      await page.waitForLoadState("networkidle");
      await expect(page.getByText("Ticket fields update")).toHaveCount(0);
    }
  });
});

test.describe("Default template rows", () => {
  let restoreTemplate: () => Promise<unknown>;

  test.afterEach(async () => {
    await restoreTemplate?.();
  });

  test("a row visible to Agents shows on the agent pages only", async ({
    api,
    pageAs,
    ticket,
  }) => {
    restoreTemplate = await setTemplateRows(api, [
      { fieldname: "priority", visible_to: "Everyone" },
      { fieldname: "ticket_type", visible_to: "Agents" },
    ]);
    await api.update("HD Ticket", ticket.name, { priority: "High", ticket_type: "Bug" });

    const customer = await pageAs("customer");
    await customer.goto("/help/tickets/new");
    await expect(customer.getByText("Priority", { exact: true })).toBeVisible();
    await expect(customer.getByText("Ticket Type", { exact: true })).toHaveCount(0);

    await customer.goto(`/help/tickets/${ticket.name}`);
    await expect(customer.getByText("High", { exact: true })).toBeVisible();
    await expect(customer.getByText("Bug", { exact: true })).toHaveCount(0);

    const agent = await pageAs("agent");
    await openTicket(agent, ticket.name);
    await expect(agent.getByRole("combobox", { name: "Set Ticket Type..." })).toHaveValue("Bug");
    await agent.goto("/helpdesk/tickets/new");
    await expect(agent.getByText("Ticket Type", { exact: true })).toBeVisible();
  });

  test("a portal script changes only the fields editable after creation", async ({
    api,
    pageAs,
    ticket,
  }) => {
    restoreTemplate = await setTemplateRows(api, [
      { fieldname: "priority", visible_to: "Everyone", editable_after_creation: 1 },
      { fieldname: "ticket_type", visible_to: "Everyone", editable_after_creation: 0 },
    ]);
    await api.update("HD Ticket", ticket.name, { priority: "High", ticket_type: "Question" });
    const scripts = new FormScripts(api);
    await scripts.create(
      `return { actions: [
        { label: "E2E Set Priority", onClick: () => ctx.updateField("priority", "Low") },
        { label: "E2E Set Type", onClick: () => ctx.updateField("ticket_type", "Bug") },
      ] };`,
      { portal: true }
    );
    try {
      const page = await pageAs("customer");
      await page.goto(`/help/tickets/${ticket.name}`);
      await page.getByRole("button", { name: "E2E Set Priority" }).click();
      await expect.poll(async () => (await api.get("HD Ticket", ticket.name)).priority).toBe("Low");

      const refused = page.waitForResponse((r) =>
        r.url().endsWith("/api/method/frappe.client.set_value")
      );
      await page.getByRole("button", { name: "E2E Set Type" }).click();
      expect((await refused).status()).toBe(403);
      expect((await api.get("HD Ticket", ticket.name)).ticket_type).toBe("Question");
    } finally {
      await scripts.removeAll();
    }
  });
});

/** Replace the Default template's rows; returns a function that puts them back. */
async function setTemplateRows(api: Api, rows: Record<string, unknown>[]) {
  const { fields } = await api.get("HD Ticket Template", "Default");
  await api.update("HD Ticket Template", "Default", { fields: rows });
  return () => api.update("HD Ticket Template", "Default", { fields });
}
