import type { Locator, Page } from "@playwright/test";
import { expectDenied, type Api } from "../../helpers/api";
import { expect, skipGettingStarted, test, uid, usePersona } from "../../helpers/fixtures";
import { openSettings } from "../../helpers/settings";

const WEBHOOK_PATH = "/api/method/whatsapp.whatsapp.webhook.handler";
const SCREENS = process.env.FACTORY_SCREENS;
const PHONE = { width: 640, height: 844 };

/** Save light and dark screenshots when FACTORY_SCREENS names a folder for them. */
async function shoot(page: Page, name: string) {
  if (!SCREENS) return;
  const device = (page.viewportSize()?.width ?? 1440) <= PHONE.width ? "phone" : "desktop";
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
    await page.screenshot({ path: `${SCREENS}/${name}-${device}-${theme}.png`, animations: "disabled" });
  }
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
}

usePersona("admin");

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
      await showOnlyAccounts(page, tag);
    });

    test.afterEach(async ({ api }) => {
      await restoreSettings();
      for (const name of accounts) await api.delete("WA Account", name).catch(() => {});
    });

    test("an admin creates, edits and defaults an account and copies the webhook URL", async ({ page, api }) => {
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await expect(dialog.getByTestId("whatsapp-webhook-url")).toHaveValue(new RegExp(`${WEBHOOK_PATH.replaceAll(".", "\\.")}$`));
      await dialog.getByRole("button", { name: "Copy webhook URL" }).click();
      await expect(page.getByText("Copied to clipboard.")).toBeVisible();
      await expect(accountRow(dialog, accounts[0]).getByText("Active", { exact: true })).toBeVisible();
      await expect(page.getByText("Copied to clipboard.")).toBeHidden({ timeout: 15000 });
      await shoot(page, "wa-settings-list");

      const created = `E2E Sales ${tag}`;
      await dialog.getByRole("button", { name: "New", exact: true }).click();
      await expect(dialog.getByRole("button", { name: "New account" })).toBeVisible();
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
      await expect(page.getByText("Default account updated")).toBeHidden({ timeout: 15000 });
      await expect(dialog.getByRole("button", { name: "Save", exact: true })).toBeVisible();
      await shoot(page, "wa-settings-edit");
      await dialog.getByRole("button", { name: "Save", exact: true }).click();
      await expect(page.getByText("Account updated")).toBeVisible();
      expect((await api.get("WA Account", created)).phone_id).toBe("15550100199");
      await dialog.getByRole("button", { name: created }).click();
      await expect(accountRow(dialog, created)).toContainText("Phone ID: 15550100199");
    });

    test("the verify token survives setting a default and saves to WA Settings", async ({ page, api }) => {
      const other = await makeAccount(api, `E2E Billing ${tag}`);
      accounts.push(other);
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      const token = `verify-${tag}`;
      await dialog.getByLabel("Verify token").fill(token);
      await accountRow(dialog, other).getByRole("button", { name: "Account actions" }).click();
      await page.getByRole("menuitem", { name: "Set as default" }).click();
      await expect(accountRow(dialog, other).getByText("Default", { exact: true })).toBeVisible();
      await expect(dialog.getByLabel("Verify token")).toHaveValue(token);
      await dialog.getByRole("button", { name: "Save", exact: true }).click();
      await expect(page.getByText("Webhook settings saved")).toBeVisible();
      await expect(dialog.getByRole("button", { name: "Save", exact: true })).toHaveCount(0);
      expect((await api.get("WA Settings", "WA Settings")).webhook_verify_token).toBe(token);
    });

    test("unsaved edits ask before they are dropped", async ({ page, api }) => {
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await dialog.getByLabel("Verify token").fill(`draft-${tag}`);
      await accountRow(dialog, accounts[0]).getByRole("button", { name: accounts[0] }).click();
      const confirm = page.getByRole("dialog", { name: "Unsaved changes" });
      await expect(confirm).toBeVisible();
      await confirm.getByRole("button", { name: "Confirm" }).click();

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
      await expect(dialog.getByLabel("Verify token")).not.toHaveValue(`draft-${tag}`);
    });

    test("failed loads offer a retry and the missing App secret is flagged", async ({ page }) => {
      await page.route("**/api/method/frappe.client.get?*", async (route) => {
        if (!route.request().url().includes("WA+Settings") && !route.request().url().includes("WA%20Settings")) return route.fallback();
        const response = await route.fetch();
        const body = await response.json();
        await route.fulfill({ response, json: { ...body, message: { ...body.message, webhook_secret: "" } } });
      });
      await page.route("**/api/method/frappe.client.get_list", (route) =>
        route.request().postDataJSON()?.doctype === "WA Account" ? route.fulfill({ status: 500, json: {} }) : route.fallback()
      );
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      await expect(dialog.getByTestId("whatsapp-secret-warning")).toBeVisible();
      const listError = dialog.getByTestId("whatsapp-accounts-error");
      await expect(listError).toBeVisible();
      await expect(dialog.getByRole("button", { name: "New", exact: true })).toBeVisible();
      await expect(page.getByText("Internal Server Error")).toBeHidden({ timeout: 15000 });
      await shoot(page, "wa-settings-accounts-error");
      await page.unroute("**/api/method/frappe.client.get_list");
      await showOnlyAccounts(page, tag);
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

    test("with no accounts the page offers to create one", async ({ page }) => {
      await page.unroute("**/api/method/frappe.client.get_list");
      await showOnlyAccounts(page, `none-${uid()}`);
      await page.goto("/helpdesk/tickets");
      const dialog = await openSettings(page, "WhatsApp");
      const empty = dialog.getByTestId("whatsapp-empty-state");
      await expect(empty).toContainText("No WhatsApp accounts yet");
      await expect(dialog.getByRole("button", { name: "New", exact: true })).toHaveCount(0);
      await empty.scrollIntoViewIfNeeded();
      await shoot(page, "wa-settings-empty");
      await empty.getByRole("button", { name: "Create account" }).click();
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
    await expectDenied(manager.raw("frappe.client.insert", { doc: { doctype: "WA Account", account_name: `E2E ${uid()}` } }));
    await expectDenied(
      manager.raw("frappe.client.set_value", { doctype: "WA Settings", name: "WA Settings", fieldname: "webhook_verify_token", value: "x" })
    );
  });
});

function accountRow(dialog: Locator, name: string) {
  return dialog.getByTestId("whatsapp-account").filter({ hasText: name });
}

/** Ask only for accounts named with `tag`, so the hundreds other suites leave never page this spec's rows out. */
async function showOnlyAccounts(page: Page, tag: string) {
  await page.route("**/api/method/frappe.client.get_list", (route) => {
    const body = route.request().postDataJSON();
    if (body?.doctype !== "WA Account") return route.fallback();
    route.fallback({ postData: { ...body, filters: { name: ["like", `%${tag}%`] } } });
  });
}

async function makeAccount(api: Api, accountName: string) {
  const doc = await api.insert("WA Account", { account_name: accountName, phone_id: `${Date.now()}`, status: "Active" });
  return doc.name as string;
}

/** Put back what these tests change on WA Settings, so other suites keep theirs. */
async function snapshotSettings(api: Api) {
  const settings = await api.get("WA Settings", "WA Settings");
  const saved = {
    default_account: settings.default_account ?? "",
    webhook_verify_token: settings.webhook_verify_token ?? "",
  };
  return async () => {
    await api.update("WA Settings", "WA Settings", saved);
  };
}
