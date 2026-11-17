import { join } from "node:path";
import type { Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { emailOf } from "../../../helpers/personas";

usePersona("customer");

const API = "helpdesk.integrations.whatsapp.api";
const SCREENS = process.env.SCREENS_DIR || join(process.cwd(), ".factory", "screens");

async function shoot(page: Page) {
  const device = (page.viewportSize()?.width ?? 1440) < 640 ? "phone" : "desktop";
  for (const theme of ["light", "dark"] as const) {
    await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
    await page.screenshot({ path: join(SCREENS, `portal-whatsapp-not-installed-${device}-${theme}.png`) });
  }
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("a WhatsApp ticket says the conversation is unavailable once the app is gone", async ({ page, api }) => {
      const { name: ticket } = await api.insert("HD Ticket", {
        subject: `Uninstalled WhatsApp ${uid()}`,
        source: "WhatsApp",
        raised_by: emailOf("customer"),
      });
      await page.route(`**/api/method/${API}.get_messages`, (route) =>
        route.fulfill({
          json: {
            message: { installed: false, messages: [], reply_window_open: false, business_number: null },
          },
        })
      );

      await page.goto(`/help/my-tickets/${ticket}`);
      await expect(page.getByTestId("whatsapp-unavailable")).toHaveText("This conversation is not available right now.");
      await expect(page.getByText("Reply to this ticket on WhatsApp.")).toHaveCount(0);
      await expect(page.getByRole("log", { name: "Conversation" })).toHaveCount(0);
      await expect(page.getByText("Type a message")).toHaveCount(0);
      await shoot(page);
    });
  });
}
