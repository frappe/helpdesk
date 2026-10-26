import { join } from "node:path";
import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { openTicket } from "../../../helpers/ticket";
import {
  FakeMeta,
  makeWhatsAppAccount,
  newWhatsAppNumber,
  pressPromptButton,
  receiveWhatsApp,
} from "../../../helpers/whatsapp";

usePersona("agent");

const SCREENS = process.env.SCREENS_DIR || join(process.cwd(), ".factory", "screens");

const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

/** A customer writing to a Business Number through the webhook, the way Meta delivers it. */
class Customer {
  readonly number = newWhatsAppNumber();

  private constructor(private api: Api, private account: string) {}

  static async writingTo(api: Api) {
    return new Customer(api, await makeWhatsAppAccount(api, metaUrl));
  }

  text(message: string) {
    return receiveWhatsApp(this.api, this.account, this.number, { message });
  }

  press(ticket: string, button: "helpdesk_new_ticket" | "helpdesk_no_ticket") {
    return pressPromptButton(this.api, this.account, this.number, ticket, button);
  }
}

const bubble = (page: Page, text: string) =>
  page.getByTestId("whatsapp-thread").getByText(text).first();

async function shoot(page: Page, scenario: string, dark = false) {
  const device = (page.viewportSize()?.width ?? 1440) < 640 ? "phone" : "desktop";
  if (dark) await page.evaluate(() => document.documentElement.setAttribute("data-theme", "dark"));
  await page.screenshot({ path: join(SCREENS, `inbound-${scenario}-${device}${dark ? "-dark" : ""}.png`) });
}

async function seeConversation(page: Page, ticket: string, ...texts: string[]) {
  await openTicket(page, ticket, "#whatsapp");
  await page.getByRole("tab", { name: "WhatsApp" }).click();
  for (const text of texts) await expect(bubble(page, text)).toBeVisible();
}

/** Close the customer's ticket, then message again and answer the Closed-Ticket Prompt. */
async function reopenAfterClosing(api: Api, customer: Customer, closed: string, held: string) {
  await api.update("HD Ticket", closed, { status: "Closed" });
  const heldMessage = await customer.text(held);
  expect(heldMessage.reference_docname).toBeFalsy();
  const [prompt] = await api.list("WA Message", {
    filters: { reference_docname: closed, direction: "Outgoing", to: heldMessage.to },
  });
  const { interactive_buttons } = await api.get("WA Message", prompt.name);
  expect(interactive_buttons.map((button: any) => button.title)).toEqual(["Create new ticket", "No, thanks"]);
  const answer = await customer.press(closed, "helpdesk_new_ticket");
  expect(answer.reference_docname).not.toBe(closed);
  return answer.reference_docname as string;
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 800 },
]) {
  test.describe(`inbound at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("the first message opens a WhatsApp ticket and later messages join it", async ({ page, api }) => {
      const customer = await Customer.writingTo(api);
      const subject = `Order ${uid()} never arrived`;
      const first = await customer.text(subject);
      const second = await customer.text("It was due on Monday");

      expect(second.reference_docname).toBe(first.reference_docname);
      expect(await api.get("HD Ticket", first.reference_docname)).toMatchObject({ source: "WhatsApp", subject });
      await page.goto("/helpdesk/tickets");
      await expect(page.getByText(subject).first()).toBeVisible();
      await seeConversation(page, first.reference_docname, subject, "It was due on Monday");
      await shoot(page, "new-ticket");
      if (viewport.width > 640) await shoot(page, "new-ticket", true);
    });

    test("a closed ticket asks first, then a new ticket takes the held message", async ({ page, api }) => {
      const customer = await Customer.writingTo(api);
      const closed = (await customer.text(`Refund ${uid()} please`)).reference_docname;
      const held = `Card ${uid()} charged twice`;
      const ticket = await reopenAfterClosing(api, customer, closed, held);

      expect(await api.get("HD Ticket", ticket)).toMatchObject({ source: "WhatsApp", subject: held });
      expect((await api.get("HD Ticket", closed)).status).toBe("Closed");
      await seeConversation(page, closed, "is closed. Do you want to raise a new one?");
      await shoot(page, "closed-prompt");
      await seeConversation(page, ticket, held, "Create new ticket");
      await shoot(page, "held-message-ticket");
    });
  });
}
