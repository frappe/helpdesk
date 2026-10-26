import { join } from "node:path";
import type { Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { openTicket } from "../../../helpers/ticket";
import {
  FakeMeta,
  makeWhatsAppAccount,
  newWhatsAppNumber,
  receiveWhatsApp,
} from "../../../helpers/whatsapp";

usePersona("agent");

const SCREENS = process.env.SCREENS_DIR;
const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

for (const device of [
  { name: "desktop", viewport: { width: 1440, height: 900 } },
  { name: "phone", viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true },
]) {
  test.describe(device.name, () => {
    const { name, ...options } = device;
    test.use(options);

    test("a notification email on a WhatsApp ticket offers no email reply", async ({
      page,
      api,
    }) => {
      const errors: Error[] = [];
      page.on("pageerror", (error) => errors.push(error));
      const account = await makeWhatsAppAccount(api, metaUrl);
      const ticket = (await receiveWhatsApp(api, account, newWhatsAppNumber())).reference_docname;
      const recipient = `${uid()}@example.com`;
      await api.insert("Communication", {
        communication_type: "Automated Message",
        communication_medium: "Email",
        sent_or_received: "Sent",
        subject: "Assigned",
        content: "You were assigned",
        recipients: recipient,
        reference_doctype: "HD Ticket",
        reference_name: ticket,
      });

      await openTicket(page, ticket, "#activity");
      await page.getByRole("tab", { name: "Activity" }).click();
      // the body renders in an iframe, so find the email by its recipient
      await expect(page.getByText(recipient)).toBeVisible();
      // the innermost block holding the recipient and the actions is the email card
      const card = page
        .locator("div")
        .filter({ hasText: recipient })
        .filter({ has: page.getByRole("button") })
        .last();
      // only the more-actions menu is left; Reply and Reply All are gone
      await expect(card.getByRole("button")).toHaveCount(1);
      if (SCREENS) await shoot(page, `activity-email-${name}`);
      expect(errors).toEqual([]);
    });

    test("the contact card has no email button on a WhatsApp ticket", async ({ page, api }) => {
      test.skip(name === "desktop", "the contact card's buttons are phone only");
      const account = await makeWhatsAppAccount(api, metaUrl);
      const ticket = (await receiveWhatsApp(api, account, newWhatsAppNumber())).reference_docname;

      await openTicket(page, ticket);
      await page.getByRole("tab", { name: "Details" }).click();
      const card = page.getByTestId("ticket-contact-card");
      await expect(card).toBeVisible();
      await expect(card.getByRole("button", { name: "Email" })).toHaveCount(0);
      if (SCREENS) await shoot(page, `contact-card-${name}`);
    });
  });
}

async function shoot(page: Page, scenario: string) {
  for (const theme of ["light", "dark"]) {
    await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
    await page.screenshot({ animations: "disabled", path: join(SCREENS!, `${scenario}-${theme}.png`) });
  }
}
