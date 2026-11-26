import { expect, test, usePersona } from "../../helpers/fixtures";
import { FormScripts } from "../../helpers/form-script";
import { snapshotSettings } from "../../helpers/settings";

const NOTICE = "show_ticket_source_notice";
const OTHER_NOTICES = [
  "show_customer_portal_permission_notice",
  "show_ticket_field_permission_notice",
];

usePersona("manager");
test.use({ permissions: ["clipboard-read", "clipboard-write"] });

// Below 640px MobileLayout shows no sidebar banners, so that is the narrowest width they appear at
for (const [viewport, size] of [
  ["desktop", { width: 1440, height: 900 }],
  ["phone", { width: 640, height: 900 }],
] as const) {
  test.describe(`ticket source notice on ${viewport}`, () => {
    let restoreSettings: () => Promise<unknown>;
    let scripts: FormScripts;

    test.use({ viewport: size });

    test.beforeEach(async ({ api }) => {
      restoreSettings = await snapshotSettings(api, [NOTICE, ...OTHER_NOTICES]);
      // the other notices have their own Learn more buttons
      await api.update("HD Settings", "HD Settings", {
        [NOTICE]: 1,
        ...Object.fromEntries(OTHER_NOTICES.map((notice) => [notice, 0])),
      });
      scripts = new FormScripts(api);
    });

    test.afterEach(async () => {
      await scripts.removeAll();
      await restoreSettings();
    });

    test("a manager sees the scripts to fix until they dismiss it", async ({ api, page }) => {
      const script = await scripts.create("if (doc.via_customer_portal) {}", { enabled: false });
      await page.goto("/helpdesk/tickets");
      const banner = page.getByText("Via Customer Portal field is now called Source");
      await expect(banner).toBeVisible();

      await page.getByRole("button", { name: "Learn more" }).click();
      const dialog = page.getByRole("dialog", { name: "Via Customer Portal is now Source" });
      await expect(dialog.getByRole("link", { name: script })).toHaveAttribute(
        "href",
        `/app/hd-form-script/${encodeURIComponent(script)}`
      );

      await dialog.getByRole("button", { name: "Copy fix prompt" }).click();
      await expect(page.getByText("Fix prompt copied")).toBeVisible();
      const prompt = await page.evaluate(() => navigator.clipboard.readText());
      expect(prompt).toContain(`- HD Form Script: ${script}`);

      await dialog.getByRole("button", { name: "Got it" }).click();
      await expect(dialog).toHaveCount(0);
      await expect(banner).toHaveCount(0);
      expect((await api.get("HD Settings", "HD Settings"))[NOTICE]).toBe(0);
    });

    test("the collapsed sidebar names its notice button", async ({ page }) => {
      await page.goto("/helpdesk/tickets");
      await page.getByRole("button", { name: "Collapse" }).click();
      await page.getByRole("button", { name: "Fieldname changed" }).click();
      await expect(
        page.getByRole("dialog", { name: "Via Customer Portal is now Source" })
      ).toBeVisible();
    });

    test("an agent never sees it", async ({ pageAs }) => {
      const agent = await pageAs("agent");
      await agent.setViewportSize(size);
      await agent.goto("/helpdesk/tickets");
      await agent.waitForLoadState("networkidle");
      await expect(agent.getByText("Fieldname changed")).toHaveCount(0);
    });
  });
}
