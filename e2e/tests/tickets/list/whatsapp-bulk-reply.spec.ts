import { join } from "node:path";
import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { TicketList, resetDefaultTicketView } from "../../../helpers/list";
import { personas } from "../../../helpers/personas";
import {
  FakeMeta,
  makeWhatsAppAccount,
  newWhatsAppNumber,
  receiveWhatsApp,
} from "../../../helpers/whatsapp";

usePersona("manager");

const SCREENS = process.env.SCREENS_DIR;
const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

test.beforeEach(async ({ api }) => {
  await resetDefaultTicketView(api, personas.manager.email);
});

for (const viewport of [
  { name: "desktop", width: 1280, height: 800 },
  { name: "phone", width: 390, height: 760 },
]) {
  test.describe(viewport.name, () => {
    test.use({ viewport });

    test("bulk reply skips WhatsApp tickets and names them", async ({
      page,
      context,
      api,
      apiAs,
    }) => {
      await context.grantPermissions(["clipboard-read", "clipboard-write"]);
      const id = uid();
      const email = await raiseTicket(await apiAs("customer"), `${id} email`);
      const account = await makeWhatsAppAccount(api, metaUrl);
      const whatsapp = (await receiveWhatsApp(api, account, newWhatsAppNumber())).reference_docname;
      await api.update("HD Ticket", whatsapp, { subject: `${id} whatsapp` });

      const list = new TicketList(page);
      await list.goto();
      await narrowTo(page, list, [email.name, whatsapp]);
      await expect(list.rows().filter({ hasText: id })).toHaveCount(2);
      await list.select(`${id} email`, `${id} whatsapp`);
      await list.selectionBar().getByRole("button", { name: "Reply" }).click();
      const dialog = page.getByRole("dialog");
      await dialog.locator("[contenteditable=true]").fill(`${id} bulk reply`);
      await dialog.getByRole("button", { name: "Send to 2 tickets" }).click();

      const toast = page.getByText(`Sent to 1 of 2 tickets. Reply to #${whatsapp} on WhatsApp.`);
      await expect(toast).toBeVisible();
      await expect(dialog).toBeHidden();
      await expect.poll(() => sentEmails(api, email.name)).toBe(1);
      expect(await sentEmails(api, whatsapp)).toBe(0);
      if (SCREENS) await shoot(page, `bulk-reply-skipped-${viewport.name}`);
    });

    test("bulk reply to only WhatsApp tickets keeps the dialog and draft", async ({
      page,
      context,
      api,
    }) => {
      await context.grantPermissions(["clipboard-read", "clipboard-write"]);
      const id = uid();
      const account = await makeWhatsAppAccount(api, metaUrl);
      const whatsapp = (await receiveWhatsApp(api, account, newWhatsAppNumber())).reference_docname;
      await api.update("HD Ticket", whatsapp, { subject: `${id} whatsapp` });

      const list = new TicketList(page);
      await list.goto();
      await narrowTo(page, list, [whatsapp]);
      await list.select(`${id} whatsapp`);
      await list.selectionBar().getByRole("button", { name: "Reply" }).click();
      const dialog = page.getByRole("dialog");
      const editor = dialog.locator("[contenteditable=true]");
      await editor.fill(`${id} draft`);
      await dialog.getByRole("button", { name: "Send Reply" }).click();

      await expect(page.getByText(`Nothing sent. Reply to #${whatsapp} on WhatsApp.`)).toBeVisible();
      await expect(dialog).toBeVisible();
      await expect(editor).toContainText(`${id} draft`);
      expect(await sentEmails(api, whatsapp)).toBe(0);
      if (SCREENS) await shoot(page, `bulk-reply-all-skipped-${viewport.name}`);
      await dialog.getByRole("button", { name: "Discard" }).click();
    });
  });
}

// phone has no Subject quick filter, so filter by ID through the popover
async function narrowTo(page: Page, list: TicketList, names: string[]) {
  await list.chooseFilterField("ID");
  await list.chooseFilterOperator("In");
  await page.evaluate((text) => navigator.clipboard.writeText(text), names.join(", "));
  await list.filterPopover().getByPlaceholder("Search...").press("ControlOrMeta+V");
  await page.keyboard.press("Escape");
}

async function shoot(page: Page, name: string) {
  // let the dialog and toast finish animating
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(SCREENS!, `${name}-light.png`) });
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(SCREENS!, `${name}-dark.png`) });
}

async function sentEmails(api: Api, ticket: string): Promise<number> {
  const rows = await api.list("Communication", {
    fields: ["name"],
    filters: { reference_doctype: "HD Ticket", reference_name: ticket, sent_or_received: "Sent" },
  });
  return rows.length;
}
