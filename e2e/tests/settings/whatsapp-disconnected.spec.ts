import { createServer } from "node:http";
import type { AddressInfo } from "node:net";
import type { Page } from "@playwright/test";
import { expect, skipGettingStarted, test, uid, usePersona } from "../../helpers/fixtures";
import { openSettings } from "../../helpers/settings";

const PHONE = { width: 640, height: 844 };
const SETTINGS = "WA Settings";

/** A Graph API whose every answer is Meta's error 190: the account's token expired or was revoked. */
const expiredMeta = createServer((_, response) => {
  response.statusCode = 401;
  response.setHeader("content-type", "application/json");
  response.end(
    JSON.stringify({
      error: { message: "Error validating access token", type: "OAuthException", code: 190 },
    })
  );
});
let metaUrl: string;

usePersona("admin");

test.beforeAll(async () => {
  await new Promise<void>((resolve) => expiredMeta.listen(0, "127.0.0.1", resolve));
  metaUrl = `http://127.0.0.1:${(expiredMeta.address() as AddressInfo).port}`;
});
test.afterAll(() => expiredMeta.close());
test.beforeEach(({ page }) => skipGettingStarted(page, "Administrator"));

for (const viewport of [{ width: 1440, height: 900 }, PHONE]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("an expired Meta token marks the account Disconnected", async ({ page, api }) => {
      const settings = await api.get(SETTINGS, SETTINGS);
      const tag = uid();
      const account = (
        await api.insert("WA Account", {
          account_name: `E2E Expired ${tag}`,
          phone_id: uid(),
          business_id: uid(),
          status: "Active",
          access_token: "e2e-expired-token",
        })
      ).name as string;
      await api.update(SETTINGS, SETTINGS, { whatsapp_api_url: metaUrl });

      try {
        await showOnlyAccount(page, tag);
        await page.route("**/*.get_active_accounts", (route) =>
          route.fulfill({ json: { message: [{ name: account }] } })
        );
        await page.goto("/helpdesk/tickets");
        const dialog = await openSettings(page, "WhatsApp");
        await dialog.getByRole("button", { name: "Sync" }).click();
        await expect(page.getByText(`Could not sync ${account}`)).toBeVisible();

        await dialog.getByRole("tab", { name: "Accounts" }).click();
        const row = dialog.getByTestId("whatsapp-account").filter({ hasText: tag });
        await expect(row.getByText("Disconnected", { exact: true })).toBeVisible();
        expect((await api.get("WA Account", account)).status).toBe("Disconnected");
      } finally {
        await api.update(SETTINGS, SETTINGS, {
          whatsapp_api_url: settings.whatsapp_api_url ?? "",
          default_account: settings.default_account ?? "",
        });
        await api.delete("WA Account", account).catch(() => {});
      }
    });
  });
}

/** Ask only for this test's WA Account, so accounts other suites leave never page it out of the list. */
async function showOnlyAccount(page: Page, tag: string) {
  await page.route("**/api/method/frappe.client.get_list", (route) => {
    const body = route.request().postDataJSON();
    if (body?.doctype !== "WA Account") return route.fallback();
    const only = ["WA Account", "name", "like", `%${tag}%`];
    const filters = Array.isArray(body.filters)
      ? [...body.filters, only]
      : [...Object.entries(body.filters ?? {}).map(([key, value]) => ["WA Account", key, "=", value]), only];
    route.fallback({ postData: { ...body, filters } });
  });
}
