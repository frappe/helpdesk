import { expect, skipGettingStarted, test, uid } from "../../helpers/fixtures";
import { siteHeader } from "../../helpers/site";

// The landing of Meta's sign-in (whatsapp.whatsapp.oauth.callback) in the desk. The test site has no
// Pilot credentials, so it is not a Frappe Cloud v2 site and the callback refuses the sign-in.
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";
const CALLBACK = "/api/method/whatsapp.whatsapp.oauth.callback?state=e2e&code=e2e";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test.describe("logged in", () => {
      test.beforeEach(async ({ page }) => {
        await page.request.post("/api/method/login", {
          form: { usr: "Administrator", pwd: ADMIN_PASSWORD },
          headers: siteHeader(),
        });
        await skipGettingStarted(page, "Administrator");
      });

      test("a site off Frappe Cloud lands on the accounts list and says why", async ({ page }) => {
        await page.goto(CALLBACK);

        // The list view may add its saved filters; only the sign-in result must leave the URL.
        await expect(page).toHaveURL(/\/wa-account(\?(?!.*whatsapp_)[^#]*)?$/);
        const dialog = page.locator(".msgprint-dialog");
        await expect(dialog).toContainText("Connect with Meta is only available on Frappe Cloud.");
      });

      test("a connected account is named in the message, as text", async ({ page }) => {
        const account = `<b>E2E ${uid()}</b>`;
        await page.goto(
          `/desk/wa-account?whatsapp_connect=connected&whatsapp_account=${encodeURIComponent(account)}`
        );

        const dialog = page.locator(".msgprint-dialog");
        await expect(dialog).toContainText(`The WhatsApp account ${account} is connected.`);
        // The list view may add its saved filters; only the sign-in result must leave the URL.
        await expect(page).toHaveURL(/\/wa-account(\?(?!.*whatsapp_)[^#]*)?$/);
      });
    });

    test("a guest is asked to log in first", async ({ page }) => {
      await page.goto(CALLBACK);

      await expect(page).toHaveURL(/\/login/);
    });
  });
}
