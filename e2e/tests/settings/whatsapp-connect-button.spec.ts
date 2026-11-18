import type { Locator, Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expect, skipGettingStarted, test, uid, usePersona } from "../../helpers/fixtures";
import { openSettings } from "../../helpers/settings";

// The Connect with Meta and Reconnect buttons of @whatsapp/ui and of the WA Account desk form.
// The test site has no Pilot credentials, so a v2 site is faked by answering can_connect_with_meta,
// and Meta's sign-in page by answering the URL initiate_connect returns.
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

    test("a site off Frappe Cloud shows the manual form only", async ({ page, api }) => {
      const asked: string[] = [];
      page.on("request", (request) => asked.push(request.url()));
      const account = await makeAccount(api, "Disconnected");
      try {
        const dialog = await openAccounts(page, account);
        await dialog.getByRole("button", { name: "New account" }).click();
        await expect(dialog.getByLabel("Access token")).toBeVisible();
        await expect(dialog.getByRole("button", { name: "Connect with Meta" })).toHaveCount(0);

        await page.goto("/helpdesk/tickets");
        await openAccount(await openAccounts(page, account), account);
        const banner = page.getByTestId("whatsapp-account-disconnected");
        await expect(banner.getByText("Disconnected", { exact: true })).toBeVisible();
        await expect(banner).toContainText("Enter a new access token below.");
        await expect(banner.getByRole("button", { name: "Reconnect" })).toHaveCount(0);
        expect(asked.filter((url) => url.includes("initiate_connect"))).toEqual([]);
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("Connect with Meta sends the browser to Meta's sign-in", async ({ page, api }) => {
      const account = await makeAccount(api, "Active");
      try {
        await fakeFrappeCloud(page);
        const dialog = await openAccounts(page, account);
        await dialog.getByRole("button", { name: "New account" }).click();
        const connect = dialog.getByTestId("whatsapp-connect-with-meta");
        await expect(connect.getByRole("button", { name: "Connect with Meta" })).toBeVisible();
        await expect(dialog.getByLabel("Access token")).toBeVisible();
        await shoot(page, "account-form-connect");

        const started = page.waitForRequest(`${OAUTH}initiate_connect`);
        await connect.getByRole("button", { name: "Connect with Meta" }).click();
        const body = (await started).postDataJSON();
        expect(body.wa_account ?? null).toBeNull();
        expect(body.redirect_to).toMatch(/^\/helpdesk\//);
        await expect(page).toHaveURL(new RegExp(`^${META_SIGN_IN}`));
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("a Disconnected account shows the badge and reconnects that account", async ({ page, api }) => {
      const account = await makeAccount(api, "Disconnected");
      try {
        await fakeFrappeCloud(page);
        await openAccount(await openAccounts(page, account), account);
        const banner = page.getByTestId("whatsapp-account-disconnected");
        await expect(banner.getByText("Disconnected", { exact: true })).toBeVisible();
        await shoot(page, "account-form-disconnected");

        const started = page.waitForRequest(`${OAUTH}initiate_connect`);
        await banner.getByRole("button", { name: "Reconnect" }).click();
        expect((await started).postDataJSON().wa_account).toBe(account);
        await expect(page).toHaveURL(new RegExp(`^${META_SIGN_IN}`));
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("an Active account has no Reconnect", async ({ page, api }) => {
      const account = await makeAccount(api, "Active");
      try {
        await fakeFrappeCloud(page);
        const dialog = await openAccounts(page, account);
        await shoot(page, "account-list");
        await openAccount(dialog, account);
        await expect(dialog.getByLabel("Access token")).toBeVisible();
        await expect(page.getByTestId("whatsapp-account-disconnected")).toHaveCount(0);
        await expect(dialog.getByRole("button", { name: "Reconnect" })).toHaveCount(0);
        await shoot(page, "account-form-connected");
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("the desk form has Connect with Meta and Reconnect", async ({ page, api }) => {
      const account = await makeAccount(api, "Disconnected");
      try {
        await fakeFrappeCloud(page);
        await page.goto("/desk/wa-account/new");
        await expect(await deskAction(page, "Connect with Meta")).toBeVisible();
        await page.keyboard.press("Escape");
        await shoot(page, "desk-form-new");

        await page.goto(`/desk/wa-account?account_name=${encodeURIComponent(account)}`);
        await expect(page.getByRole("link", { name: account })).toBeVisible();
        // the phone layout of a desk list has no status column
        if (viewport !== PHONE) await expect(disconnectedPill(page)).toBeVisible();
        await shoot(page, "desk-list");

        await page.goto(`/desk/wa-account/${encodeURIComponent(account)}`);
        // the phone layout shows the status as a coloured dot, without its label
        if (viewport !== PHONE) await expect(disconnectedPill(page)).toBeVisible();
        await shoot(page, "desk-form-disconnected");
        const started = page.waitForRequest(`${OAUTH}initiate_connect`);
        await (await deskAction(page, "Reconnect")).click();
        expect((await started).postDataJSON().wa_account).toBe(account);
        await expect(page).toHaveURL(new RegExp(`^${META_SIGN_IN}`));
      } finally {
        await api.delete("WA Account", account).catch(() => {});
      }
    });

    test("the desk form off Frappe Cloud has neither button", async ({ page, api }) => {
      const account = await makeAccount(api, "Disconnected");
      try {
        for (const path of [encodeURIComponent(account), "new"]) {
          const asked = page.waitForResponse(`${OAUTH}can_connect_with_meta`);
          await page.goto(`/desk/wa-account/${path}`);
          expect((await (await asked).json()).message).toBe(false);
          await expect(page.getByRole("button", { name: "Save", exact: true })).toBeVisible();
          // counts hidden menu items too, so it holds for the phone layout's Menu
          await expect(page.getByText(/^(Connect with Meta|Reconnect)$/)).toHaveCount(0);
        }
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
      account_name: `E2E Connect ${tag}`,
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

/** The WhatsApp Accounts tab, listing only `account` so accounts other suites leave never page it out. */
async function openAccounts(page: Page, account: string): Promise<Locator> {
  await page.route("**/api/method/frappe.client.get_list", (route) => {
    const body = route.request().postDataJSON();
    if (body?.doctype !== "WA Account") return route.fallback();
    route.fallback({ postData: { ...body, filters: { name: account } } });
  });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "WhatsApp");
  await dialog.getByRole("tab", { name: "Accounts" }).click();
  await expect(dialog.getByRole("button", { name: account })).toBeVisible();
  return dialog;
}

async function openAccount(dialog: Locator, account: string) {
  await dialog.getByRole("button", { name: account }).click();
  await expect(dialog.getByLabel("Account name")).toHaveValue(account);
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

function disconnectedPill(page: Page) {
  return page.getByText("Disconnected", { exact: true }).filter({ visible: true }).first();
}

/** A desk form's custom button; the phone layout lists them in the Menu. */
async function deskAction(page: Page, name: string | RegExp) {
  if ((page.viewportSize()?.width ?? 1440) > PHONE.width) return page.getByRole("button", { name });
  await expect(page.getByRole("button", { name: "Save", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Menu", exact: true }).click();
  return page.getByRole("menuitem", { name });
}
