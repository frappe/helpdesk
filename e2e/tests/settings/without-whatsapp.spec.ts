import type { Page } from "@playwright/test";
import { Api } from "../../helpers/api";
import { expect, skipGettingStarted, test } from "../../helpers/fixtures";
import { TicketList } from "../../helpers/list";
import { openSettings } from "../../helpers/settings";
import { siteHeader } from "../../helpers/site";

// Runs only against a site without the whatsapp app, e.g. `--no-deps` with BASE_URL at a throwaway site.
const SCREENS = process.env.FACTORY_SCREENS;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || "admin";

async function shoot(page: Page, name: string) {
  if (!SCREENS) return;
  const device = (page.viewportSize()?.width ?? 1440) < 640 ? "phone" : "desktop";
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
    await page.screenshot({ path: `${SCREENS}/${name}-${device}-${theme}.png`, animations: "disabled" });
  }
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
}

test.beforeAll(async ({ baseURL }) => {
  const api = await Api.login(baseURL!, "Administrator", ADMIN_PASSWORD);
  const versions = await api.call("frappe.utils.change_log.get_versions");
  test.skip("whatsapp" in versions, "needs a site without the whatsapp app");
});

test.beforeEach(async ({ page }) => {
  await page.request.post("/api/method/login", {
    form: { usr: "Administrator", pwd: ADMIN_PASSWORD },
    headers: siteHeader(),
  });
  await skipGettingStarted(page, "Administrator");
});

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("the Source filter offers only Email and Portal", async ({ page }) => {
      const list = new TicketList(page);
      await list.goto();
      await list.chooseFilterField("Source");
      await expect(page.getByRole("option")).toHaveText(["Email", "Portal"]);
      await shoot(page, "without-whatsapp-source-filter");
    });
  });
}

// the phone layout has no settings modal
test("the settings modal has no WhatsApp tab", async ({ page }) => {
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Email Accounts");
  await expect(dialog.getByRole("button", { name: "WhatsApp", exact: true })).toHaveCount(0);
  await shoot(page, "without-whatsapp-settings");
});
