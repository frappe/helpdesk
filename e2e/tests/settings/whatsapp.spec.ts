import type { Locator, Page } from "@playwright/test";
import { expectDenied, type Api } from "../../helpers/api";
import { expect, skipGettingStarted, test, uid, usePersona } from "../../helpers/fixtures";
import { openSettings } from "../../helpers/settings";
import { FakeMeta, makeWhatsAppAccount } from "../../helpers/whatsapp";

const WEBHOOK_PATH = "/api/method/whatsapp.whatsapp.webhook.handler";
const SCREENS = process.env.FACTORY_SCREENS;
const PHONE = { width: 640, height: 844 };

/** Save light and dark screenshots when FACTORY_SCREENS names a folder for them. */
async function shoot(page: Page, name: string) {
  if (!SCREENS) return;
  const device = (page.viewportSize()?.width ?? 1440) <= PHONE.width ? "phone" : "desktop";
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
    await page.screenshot({
      path: `${SCREENS}/${name}-${device}-${theme}.png`,
      animations: "disabled",
    });
  }
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
}

const meta = new FakeMeta();
let metaUrl: string;

usePersona("admin");

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());
test.beforeEach(({ page }) => skipGettingStarted(page, "Administrator"));

for (const viewport of [{ width: 1440, height: 900 }, PHONE]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });
    let tag: string;
    let accounts: string[];
    let restoreSettings: () => Promise<void>;

    test.beforeEach(async ({ api, page }) => {
      restoreSettings = await snapshotSettings(api);
      tag = uid();
      accounts = [await makeAccount(api, `E2E Support ${tag}`)];
      await showOnly(page, "WA Account", tag);
      await showOnly(page, "WA Template", tag, "template_label");
    });

    test.afterEach(async ({ api }) => {
      await restoreSettings();
      for (const name of accounts) await api.delete("WA Account", name).catch(() => {});
    });

    test("an admin creates, edits and defaults an account and copies the webhook URL", async ({ page, api }) => {
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await openTab(dialog, "Advanced");
      await expect(dialog.getByTestId("whatsapp-webhook-url")).toHaveValue(new RegExp(`${WEBHOOK_PATH.replaceAll(".", "\\.")}$`));
      await dialog.getByRole("button", { name: "Copy webhook URL" }).click();
      await expect(page.getByText("Copied to clipboard.")).toBeVisible();
      await openTab(dialog, "Accounts");
      await expect(accountRow(dialog, accounts[0]).getByText("Active", { exact: true })).toBeVisible();
      await expect(page.getByText("Copied to clipboard.")).toBeHidden({
        timeout: 15000,
      });
      await shoot(page, "wa-settings-list");

      const created = `E2E Sales ${tag}`;
      await dialog.getByRole("button", { name: "New account" }).click();
      await expect(dialog.getByLabel("Account name")).toBeVisible();
      await dialog.getByLabel("Account name").fill(created);
      await dialog.getByLabel("Phone ID").fill(`${Date.now()}`);
      await dialog.getByLabel("Access token").fill("e2e-token");
      await shoot(page, "wa-settings-create");
      await dialog.getByRole("button", { name: "Create", exact: true }).click();
      accounts.push(created);
      await expect(page.getByText("Account created")).toBeVisible();
      const row = accountRow(dialog, created);
      await expect(row.getByText("Active", { exact: true })).toBeVisible();

      await row.getByRole("button", { name: "Account actions" }).click();
      await page.getByRole("menuitem", { name: "Set as default" }).click();
      await expect(row.getByText("Default", { exact: true })).toBeVisible();
      await expect.poll(async () => (await api.get("WA Settings", "WA Settings")).default_account).toBe(created);

      await row.getByRole("button", { name: created }).click();
      await expect(dialog.getByLabel("Account name")).toHaveValue(created);
      await dialog.getByLabel("Phone ID").fill("15550100199");
      await expect(page.getByText("Default account updated")).toBeHidden({
        timeout: 15000,
      });
      await expect(dialog.getByRole("button", { name: "Save", exact: true })).toBeVisible();
      await shoot(page, "wa-settings-edit");
      await dialog.getByRole("button", { name: "Save", exact: true }).click();
      await expect(page.getByText("Account updated")).toBeVisible();
      expect((await api.get("WA Account", created)).phone_id).toBe("15550100199");
      await dialog.getByRole("button", { name: created }).click();
      await expect(accountRow(dialog, created)).toContainText("Phone ID: 15550100199");
    });

    test("a new default account survives saving the verify token", async ({ page, api }) => {
      const other = await makeAccount(api, `E2E Billing ${tag}`);
      accounts.push(other);
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await openTab(dialog, "Accounts");
      await accountRow(dialog, other).getByRole("button", { name: "Account actions" }).click();
      await page.getByRole("menuitem", { name: "Set as default" }).click();
      await expect(accountRow(dialog, other).getByText("Default", { exact: true })).toBeVisible();
      await openTab(dialog, "Advanced");
      const token = `verify-${tag}`;
      await dialog.getByLabel("Verify token").fill(token);
      await dialog.getByRole("button", { name: "Save", exact: true }).click();
      await expect(page.getByText("Webhook settings saved")).toBeVisible();
      await expect(dialog.getByRole("button", { name: "Save", exact: true })).toHaveCount(0);
      const settings = await api.get("WA Settings", "WA Settings");
      expect(settings.webhook_verify_token).toBe(token);
      expect(settings.default_account).toBe(other);
    });

    test("unsaved edits ask before they are dropped", async ({ page, api }) => {
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await openTab(dialog, "Advanced");
      await dialog.getByLabel("Verify token").fill(`draft-${tag}`);
      await openTab(dialog, "Accounts");
      const confirm = page.getByRole("dialog", { name: "Unsaved changes" });
      await expect(confirm).toBeVisible();
      await confirm.getByRole("button", { name: "Confirm" }).click();
      await accountRow(dialog, accounts[0]).getByRole("button", { name: accounts[0] }).click();

      const phoneId = (await api.get("WA Account", accounts[0])).phone_id;
      await dialog.getByLabel("Phone ID").fill("15550100777");
      await dialog.getByRole("button", { name: accounts[0] }).click();
      await expect(confirm).toBeVisible();
      await shoot(page, "wa-settings-unsaved-confirm");
      await confirm.getByRole("button", { name: "Close" }).click();
      await expect(dialog.getByLabel("Phone ID")).toHaveValue("15550100777");
      await dialog.getByRole("button", { name: accounts[0] }).click();
      await confirm.getByRole("button", { name: "Confirm" }).click();
      await expect(accountRow(dialog, accounts[0])).toContainText(`Phone ID: ${phoneId}`);
      await openTab(dialog, "Advanced");
      await expect(dialog.getByLabel("Verify token")).not.toHaveValue(`draft-${tag}`);
    });

    test("failed loads offer a retry and the missing App secret is flagged", async ({ page }) => {
      await page.route("**/api/method/frappe.client.get?*", async (route) => {
        if (!route.request().url().includes("WA+Settings") && !route.request().url().includes("WA%20Settings")) return route.fallback();
        const response = await route.fetch();
        const body = await response.json();
        await route.fulfill({
          response,
          json: { ...body, message: { ...body.message, webhook_secret: "" } },
        });
      });
      await page.route("**/api/method/frappe.client.get_list", (route) =>
        route.request().postDataJSON()?.doctype === "WA Account" ? route.fulfill({ status: 500, json: {} }) : route.fallback()
      );
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await openTab(dialog, "Advanced");
      await expect(dialog.getByTestId("whatsapp-secret-warning")).toBeVisible();
      await openTab(dialog, "Accounts");
      const listError = dialog.getByTestId("whatsapp-accounts-error");
      await expect(listError).toBeVisible();
      await expect(dialog.getByRole("button", { name: "New account" })).toBeVisible();
      await expect(page.getByText("Internal Server Error")).toBeHidden({
        timeout: 15000,
      });
      await shoot(page, "wa-settings-accounts-error");
      await page.unroute("**/api/method/frappe.client.get_list");
      await showOnly(page, "WA Account", tag);
      await listError.getByRole("button", { name: "Retry" }).click();
      const row = accountRow(dialog, accounts[0]);
      await expect(row).toBeVisible();

      await page.route("**/api/method/frappe.client.get", (route) =>
        route.request().postDataJSON()?.doctype === "WA Account" ? route.fulfill({ status: 500, json: {} }) : route.fallback()
      );
      await row.getByRole("button", { name: accounts[0] }).click();
      const loadError = dialog.getByTestId("whatsapp-account-error");
      await expect(loadError).toBeVisible();
      await expect(dialog.getByRole("button", { name: "Save", exact: true })).toHaveCount(0);
      await expect(dialog.getByText("Unsaved", { exact: true })).toHaveCount(0);
      await shoot(page, "wa-settings-account-error");
      await page.unroute("**/api/method/frappe.client.get");
      await loadError.getByRole("button", { name: "Retry" }).click();
      await expect(dialog.getByLabel("Account name")).toHaveValue(accounts[0]);
      await expect(dialog.getByRole("button", { name: "Save", exact: true })).toHaveCount(0);
    });

    test("an admin creates, previews, syncs and opens a template", async ({ page, api }) => {
      const account = await makeWhatsAppAccount(api, metaUrl);
      accounts.push(account);
      await api.update("WA Settings", "WA Settings", {
        default_account: account,
      });
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await expect(dialog.getByTestId("whatsapp-templates-empty")).toBeVisible();

      const label = `E2E Order shipped ${tag}`;
      await dialog.getByRole("button", { name: "New template" }).click();
      await dialog.getByLabel("Template label").fill(label);
      await dialog.locator("[contenteditable=true]").first().fill("Your order is on its way.");
      await shoot(page, "wa-settings-template-create");
      await dialog.getByRole("button", { name: "Preview" }).click();
      await expect(dialog.getByText("Your order is on its way.")).toBeVisible();
      await dialog.getByRole("button", { name: "Create", exact: true }).click();
      await expect(page.getByText("Template created and sent to Meta for review")).toBeVisible();

      const row = dialog.getByTestId("whatsapp-template").filter({ hasText: label });
      await expect(row.getByText("Pending", { exact: true })).toBeVisible();
      await expect(row).toContainText(account);
      const search = dialog.getByPlaceholder("Search template");
      await search.fill("no-such-template");
      await expect(dialog.getByText("No templates match your search")).toBeVisible();
      await search.fill(tag);
      await expect(row).toBeVisible();
      await shoot(page, "wa-settings-templates");
      await page.route("**/*.get_active_accounts", (route) => route.fulfill({ json: { message: accounts.map((name) => ({ name })) } }));
      await dialog.getByRole("button", { name: "Sync" }).click();
      await expect(page.getByText(/\d+ new, \d+ updated/)).toBeVisible();
      // the spec's own account has no access token, which skips it but not the rest
      await expect(page.getByText(`Could not sync ${accounts[0]}`)).toBeVisible();

      await row.getByRole("button", { name: label }).click();
      await expect(dialog.getByLabel("Template label")).toHaveValue(label);
      await dialog.getByRole("button", { name: label }).click();
      await expect(row).toBeVisible();
    });

    test("an account that still appends to HD Ticket is flagged on the Accounts tab", async ({ page }) => {
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await openTab(dialog, "Accounts");
      await expect(accountRow(dialog, accounts[0])).toBeVisible();
      const warning = dialog.getByTestId("whatsapp-ticket-append-warning");
      await expect(warning).toHaveCount(0);

      // saving refuses the row now, so only an account set up before this release can hold one
      await page.route("**/api/method/frappe.client.get_list", (route) =>
        JSON.stringify(route.request().postDataJSON()?.filters ?? []).includes("WA Account Append")
          ? route.fulfill({ json: { message: [{ account_name: accounts[0] }, { account_name: accounts[0] }] } })
          : route.fallback()
      );
      await openTab(dialog, "Templates");
      await openTab(dialog, "Accounts");
      await expect(warning).toContainText(`Remove the append action to HD Ticket from ${accounts[0]}`);
      await expect(warning).toContainText("Helpdesk files WhatsApp messages on tickets itself.");
      // one account with two such rows is named once
      await expect(warning).not.toContainText(`${accounts[0]}, ${accounts[0]}`);
      await shoot(page, "wa-settings-ticket-append-warning");
    });

    test("with no accounts or templates both tabs show an empty state", async ({ page }) => {
      await page.unroute("**/api/method/frappe.client.get_list");
      await showOnly(page, "WA Account", `none-${uid()}`);
      await showOnly(page, "WA Template", `none-${uid()}`, "template_label");
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await expect(dialog.getByTestId("whatsapp-templates-empty")).toContainText("No WhatsApp templates yet");
      await openTab(dialog, "Accounts");
      const empty = dialog.getByTestId("whatsapp-empty-state");
      await expect(empty).toContainText("No WhatsApp accounts yet");
      await shoot(page, "wa-settings-empty");
      await dialog.getByRole("button", { name: "New account" }).click();
      await expect(dialog.getByLabel("Account name")).toBeVisible();
      await dialog.getByRole("button", { name: "New account" }).click();
      await expect(empty).toBeVisible();
    });
  });
}

test.describe("as an agent manager", () => {
  usePersona("manager");

  test("the WhatsApp tab is hidden and accounts and settings refuse writes", async ({ page, apiAs }) => {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Preferences");
    await expect(dialog.getByRole("button", { name: "WhatsApp", exact: true })).toHaveCount(0);
    const manager = await apiAs("manager");
    await expectDenied(
      manager.raw("frappe.client.insert", {
        doc: { doctype: "WA Account", account_name: `E2E ${uid()}` },
      })
    );
    await expectDenied(
      manager.raw("frappe.client.set_value", {
        doctype: "WA Settings",
        name: "WA Settings",
        fieldname: "webhook_verify_token",
        value: "x",
      })
    );
  });
});

function accountRow(dialog: Locator, name: string) {
  return dialog.getByTestId("whatsapp-account").filter({ hasText: name });
}

function openTab(dialog: Locator, name: "Templates" | "Accounts" | "Advanced") {
  return dialog.getByRole("tab", { name }).click();
}

/** Ask only for `doctype` rows whose `field` holds `tag`, so the hundreds other suites leave never page this spec's rows out. */
async function showOnly(page: Page, doctype: string, tag: string, field = "name") {
  await page.route("**/api/method/frappe.client.get_list", (route) => {
    const body = route.request().postDataJSON();
    if (body?.doctype !== doctype) return route.fallback();
    const only = [doctype, field, "like", `%${tag}%`];
    const filters = Array.isArray(body.filters)
      ? [...body.filters, only]
      : [...Object.entries(body.filters ?? {}).map(([key, value]) => [doctype, key, "=", value]), only];
    route.fallback({ postData: { ...body, filters } });
  });
}

async function makeAccount(api: Api, accountName: string) {
  const doc = await api.insert("WA Account", {
    account_name: accountName,
    phone_id: `${Date.now()}`,
    status: "Active",
  });
  return doc.name as string;
}

/** Put back what these tests change on WA Settings, so other suites keep theirs. */
async function snapshotSettings(api: Api) {
  const settings = await api.get("WA Settings", "WA Settings");
  const saved = {
    default_account: settings.default_account ?? "",
    webhook_verify_token: settings.webhook_verify_token ?? "",
    whatsapp_api_url: settings.whatsapp_api_url ?? "",
  };
  return async () => {
    await api.update("WA Settings", "WA Settings", saved);
  };
}
