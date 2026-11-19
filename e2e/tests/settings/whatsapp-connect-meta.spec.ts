import type { Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expect, skipGettingStarted, test, uid, usePersona } from "../../helpers/fixtures";
import { openSettings } from "../../helpers/settings";

// The WhatsApp Accounts tab with Connect with Meta. The test site has no Pilot credentials, so a
// Frappe Cloud v2 site is faked by answering can_connect_with_meta, and Meta's sign-in page too.
const OAUTH = "**/api/method/whatsapp.whatsapp.oauth.";
const META_SIGN_IN = "https://meta.e2e.test/dialog/oauth";
const SCREENS = process.env.FACTORY_SCREENS;
// the phone layout of Helpdesk has no settings modal, so phone size is its narrowest width that has one
const PHONE = { width: 640, height: 844 };

usePersona("admin");
test.beforeEach(({ page }) => skipGettingStarted(page, "Administrator"));

for (const viewport of [{ width: 1440, height: 900 }, PHONE]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("the Accounts tab connects a new account with Meta and keeps manual add", async ({ page, api }) => {
      const account = await makeAccount(api, "Disconnected");
      try {
        await fakeFrappeCloud(page);
        const dialog = await openAccounts(page, account);
        const row = dialog.getByTestId("whatsapp-account").filter({ hasText: account });
        await expect(row.getByText("Disconnected", { exact: true })).toBeVisible();
        await expect(dialog.getByRole("button", { name: "New account" })).toBeVisible();
        await shoot(page, "accounts-tab");

        const started = page.waitForRequest(`${OAUTH}initiate_connect`);
        await dialog.getByRole("button", { name: "Connect with Meta" }).click();
        const body = (await started).postDataJSON();
        expect(body.wa_account ?? null).toBeNull();
        expect(body.redirect_to).toMatch(/^\/helpdesk\//);
        await expect(page).toHaveURL(new RegExp(`^${META_SIGN_IN}`));
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("a site off Frappe Cloud adds accounts by hand only", async ({ page, api }) => {
      const account = await makeAccount(api, "Active");
      try {
        const dialog = await openAccounts(page, account);
        await expect(dialog.getByRole("button", { name: "New account" })).toBeVisible();
        await expect(dialog.getByRole("button", { name: "Connect with Meta" })).toHaveCount(0);
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("the account page of a Disconnected account offers Reconnect", async ({ page, api }) => {
      const account = await makeAccount(api, "Disconnected");
      try {
        await fakeFrappeCloud(page);
        const dialog = await openAccounts(page, account);
        await dialog.getByRole("button", { name: account }).click();
        const banner = dialog.getByTestId("whatsapp-account-disconnected");
        await expect(banner.getByText("Disconnected", { exact: true })).toBeVisible();
        await shoot(page, "account-page-disconnected");

        const started = page.waitForRequest(`${OAUTH}initiate_connect`);
        await banner.getByRole("button", { name: "Reconnect" }).click();
        expect((await started).postDataJSON().wa_account).toBe(account);
        await expect(page).toHaveURL(new RegExp(`^${META_SIGN_IN}`));
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("back from Meta's sign-in opens the Accounts tab and says the account is connected", async ({ page, api }) => {
      const account = await makeAccount(api, "Active");
      try {
        await onlyAccount(page, account);
        await page.goto(
          `/helpdesk/tickets?whatsapp_connect=connected&whatsapp_account=${encodeURIComponent(account)}`
        );
        const dialog = page.getByRole("dialog");
        await expect(dialog.getByRole("tab", { name: "Accounts", selected: true })).toBeVisible();
        await expect(dialog.getByRole("button", { name: account })).toBeVisible();
        await expect(page.getByText(`The WhatsApp account ${account} is connected.`)).toBeVisible();
        await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });
  });
}

async function makeAccount(api: Api, status: string) {
  const tag = uid();
  const name = (
    await api.insert("WA Account", {
      account_name: `E2E Meta ${tag}`,
      phone_id: tag,
      business_id: tag,
      access_token: "e2e-token",
    })
  ).name as string;
  // set after insert: a new account starts Active
  if (status !== "Active") await api.update("WA Account", name, { status });
  return name;
}

/** A v2 site with Meta turned on, and Meta's sign-in page. */
async function fakeFrappeCloud(page: Page) {
  await page.route(`${OAUTH}can_connect_with_meta`, (route) => route.fulfill({ json: { message: true } }));
  await page.route(`${OAUTH}initiate_connect`, (route) =>
    route.fulfill({ json: { message: `${META_SIGN_IN}?client_id=e2e` } })
  );
  await page.route(`${META_SIGN_IN}**`, (route) =>
    route.fulfill({ contentType: "text/html", body: "<h1>Meta sign-in</h1>" })
  );
}

/** List only `account`, so accounts other suites leave never page it out. */
function onlyAccount(page: Page, account: string) {
  return page.route("**/api/method/frappe.client.get_list", (route) => {
    const body = route.request().postDataJSON();
    if (body?.doctype !== "WA Account") return route.fallback();
    route.fallback({ postData: { ...body, filters: { name: account } } });
  });
}

async function openAccounts(page: Page, account: string) {
  await onlyAccount(page, account);
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "WhatsApp");
  await dialog.getByRole("tab", { name: "Accounts" }).click();
  await expect(dialog.getByRole("button", { name: account })).toBeVisible();
  return dialog;
}

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
