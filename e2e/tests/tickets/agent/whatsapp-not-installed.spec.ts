import { join } from "node:path";
import type { Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { openTicket } from "../../../helpers/ticket";

usePersona("agent");

const SCREENS = process.env.SCREENS_DIR || join(process.cwd(), ".factory", "screens");

// boots the desk as if the whatsapp app were not installed
async function hideWhatsAppApp(page: Page) {
  await page.addInitScript(() => {
    let apps: string[] = [];
    Object.defineProperty(window, "apps", {
      get: () => apps,
      set: (value: string[]) => {
        apps = value.filter((app) => app !== "whatsapp");
      },
    });
  });
}

async function shoot(page: Page) {
  const device = (page.viewportSize()?.width ?? 1440) < 640 ? "phone" : "desktop";
  for (const theme of ["light", "dark"] as const) {
    await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
    await page.screenshot({
      animations: "disabled",
      path: join(SCREENS, `agent-whatsapp-not-installed-${device}-${theme}.png`),
    });
  }
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("a WhatsApp ticket shows no WhatsApp tab or reply without the whatsapp app", async ({ page, api }) => {
      const { name: ticket } = await api.insert("HD Ticket", {
        subject: `Uninstalled WhatsApp ${uid()}`,
        source: "WhatsApp",
      });
      await hideWhatsAppApp(page);

      await openTicket(page, ticket);
      await expect(page.getByRole("button", { name: "Comment", exact: true })).toBeVisible();
      await expect(page.getByRole("tab", { name: "WhatsApp" })).toHaveCount(0);
      await expect(page.getByRole("tab", { name: "Emails" })).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Reply", exact: true })).toHaveCount(0);
      await shoot(page);
    });
  });
}
