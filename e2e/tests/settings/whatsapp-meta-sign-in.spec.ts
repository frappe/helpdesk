import type { Page } from "@playwright/test";
import { Api } from "../../helpers/api";
import { expect, skipGettingStarted, test, uid, usePersona } from "../../helpers/fixtures";
import { openSettings } from "../../helpers/settings";
import { becomeFrappeCloudSite, FakeCentral, FakeMeta } from "../../helpers/whatsapp";

// Meta's sign-in from end to end: the site asks a fake Central, through its Pilot, for the sign-in
// link and the token, and a fake Meta sign-in page sends the browser back with a code. The site is
// a Frappe Cloud v2 site only while this file runs.
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";
const SETTINGS = "WA Settings";
// the phone layout of Helpdesk has no settings modal, so phone size is its narrowest width that has one
const PHONE = { width: 640, height: 844 };

usePersona("admin");

const central = new FakeCentral();
const meta = new FakeMeta();
let becomeSelfHosted: () => Promise<void>;
let settings: { whatsapp_api_url?: string; default_account?: string };
let admin: Api;

test.beforeAll(async () => {
  test.setTimeout(180_000);
  admin = await Api.login(
    process.env.BASE_URL || "http://localhost:8000",
    "Administrator",
    ADMIN_PASSWORD,
  );
  settings = await admin.get(SETTINGS, SETTINGS);
  // deleting a Meta account unsubscribes Meta's app from it, which goes to the fake Graph API
  await admin.update(SETTINGS, SETTINGS, {
    whatsapp_api_url: await meta.start(),
  });
  await central.start();
  becomeSelfHosted = await becomeFrappeCloudSite(admin, central);
});

test.afterAll(async () => {
  test.setTimeout(180_000);
  if (settings) {
    await admin.update(SETTINGS, SETTINGS, { whatsapp_api_url: settings.whatsapp_api_url ?? "" });
  }
  await becomeSelfHosted?.();
  central.stop();
  meta.stop();
});

test.beforeEach(({ page }) => skipGettingStarted(page, "Administrator"));

for (const viewport of [{ width: 1440, height: 900 }, PHONE]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("Connect with Meta signs in and lists the new account on the Accounts tab", async ({
      page,
      api,
    }) => {
      const tag = uid();
      central.account = { waba_id: `waba-${tag}`, phone_id: `phone-${tag}` };
      const account = central.account.phone_id;
      try {
        const dialog = await openAccounts(page, account);
        await dialog.getByRole("button", { name: "Connect with Meta" }).click();
        await signInWithMeta(page);

        await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
        await expect(page.getByText(`The WhatsApp account ${account} is connected.`)).toBeVisible();
        const accounts = page.getByRole("dialog");
        await expect(accounts.getByRole("tab", { name: "Accounts", selected: true })).toBeVisible();
        const row = accounts.getByTestId("whatsapp-account").filter({ hasText: account });
        await expect(row.getByText("Active", { exact: true })).toBeVisible();

        expect(await api.get("WA Account", account)).toMatchObject({
          business_id: central.account.waba_id,
          phone_id: account,
          app_id: "e2e-app",
          connected_with_meta: 1,
          status: "Active",
        });
        expect(central.asked).toEqual(expect.arrayContaining(["start", "relay_token"]));
      } finally {
        await deleteAccount(api, account);
      }
    });

    test("a Disconnected account shows the badge and reconnects with Meta", async ({ page, api }) => {
      const tag = uid();
      central.account = { waba_id: `waba-${tag}`, phone_id: `phone-${tag}` };
      const account = (
        await api.insert("WA Account", {
          account_name: `E2E Meta ${tag}`,
          business_id: central.account.waba_id,
          phone_id: central.account.phone_id,
          access_token: "e2e-old-token",
          connected_with_meta: 1,
        })
      ).name as string;
      try {
        // set after insert: a new account starts Active
        await api.update("WA Account", account, { status: "Disconnected" });
        const dialog = await openAccounts(page, central.account.phone_id);
        const row = dialog.getByTestId("whatsapp-account").filter({ hasText: account });
        await expect(row.getByText("Disconnected", { exact: true })).toBeVisible();

        await dialog.getByRole("button", { name: account }).click();
        const banner = dialog.getByTestId("whatsapp-account-disconnected");
        await expect(banner.getByText("Disconnected", { exact: true })).toBeVisible();
        await banner.getByRole("button", { name: "Reconnect" }).click();
        await signInWithMeta(page);

        await expect(page.getByText(`The WhatsApp account ${account} is connected again.`)).toBeVisible();
        const accounts = page.getByRole("dialog");
        await expect(
          accounts
            .getByTestId("whatsapp-account")
            .filter({ hasText: account })
            .getByText("Active", { exact: true }),
        ).toBeVisible();
        expect(await api.get("WA Account", account)).toMatchObject({
          status: "Active",
          app_id: "e2e-app",
        });
      } finally {
        await deleteAccount(api, account);
      }
    });
  });
}

/** Finish the fake Meta sign-in, which sends the browser back to the site's callback. */
async function signInWithMeta(page: Page) {
  await expect(page).toHaveURL(new RegExp(`^${central.url}/dialog/oauth`));
  await expect(page.getByRole("heading", { name: "Meta sign-in" })).toBeVisible();
  await page.getByRole("link", { name: "Continue" }).click();
}

/** Open the Accounts tab, listing only the account of `phoneId`, so other suites' accounts never page it out. */
async function openAccounts(page: Page, phoneId: string) {
  await page.route("**/api/method/frappe.client.get_list", (route) => {
    const body = route.request().postDataJSON();
    if (body?.doctype !== "WA Account") return route.fallback();
    route.fallback({ postData: { ...body, filters: { phone_id: phoneId } } });
  });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "WhatsApp");
  await dialog.getByRole("tab", { name: "Accounts" }).click();
  return dialog;
}

/** Delete the test's account. A new account becomes the default when the site has none, and the default can't be deleted. */
async function deleteAccount(api: Api, account: string) {
  await api.update(SETTINGS, SETTINGS, { default_account: settings.default_account ?? "" });
  await api.delete("WA Account", account).catch(() => {});
}
