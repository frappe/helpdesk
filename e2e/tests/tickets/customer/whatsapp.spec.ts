import { join } from "node:path";
import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { emailOf } from "../../../helpers/personas";
import {
  approveTemplate,
  FAKE_DISPLAY_NUMBER,
  FakeMeta,
  makeWhatsAppAccount,
  newWhatsAppNumber,
  receiveWhatsApp,
  updateWhatsAppStatus,
} from "../../../helpers/whatsapp";

usePersona("customer");

const API = "helpdesk.integrations.whatsapp.api";
const MESSAGES_API = "whatsapp.whatsapp.api.messages";
const SCREENS = process.env.SCREENS_DIR || join(process.cwd(), ".factory", "screens");

const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

type Thread = {
  ticket: string;
  question: string;
  answer: string;
  failed: string;
  thanks: string;
  account: string;
  number: string;
  to: string;
};

/** A WhatsApp ticket from the customer persona's phone with text, media, a template, a quote, a reaction and a failed send. */
async function seedThread(api: Api, agent: Api): Promise<Thread> {
  const account = await makeWhatsAppAccount(api, metaUrl);
  const number = newWhatsAppNumber();
  const contact = await api.exists("Contact", { email_id: emailOf("customer") });
  await api.update("Contact", contact!, {
    phone_nos: [{ phone: `+${number}`, is_primary_mobile_no: 1 }],
  });
  const question = `Parcel ${uid()} never arrived`;
  const first = await receiveWhatsApp(api, account, number, { message: `*Help*, ${question}` });
  const ticket = first.reference_docname;
  const scope = { to: first.to, reference_doctype: "HD Ticket", reference_docname: ticket };
  await receiveWhatsApp(api, account, number, { type: "image", image: { id: uid(), mime_type: "image/jpeg" } });
  await receiveWhatsApp(api, account, number, {
    type: "document",
    document: { id: uid(), mime_type: "application/pdf", filename: "receipt.pdf" },
  });
  const answer = `Courier ${uid()} is on it`;
  const sent = await agent.call<string>(`${MESSAGES_API}.send_message`, { ...scope, message: answer });
  const template = await insertTemplate(api, account);
  await agent.call(`${MESSAGES_API}.send_template`, { ...scope, template });
  const { message_id } = await api.get("WA Message", sent);
  await receiveWhatsApp(api, account, number, { type: "reaction", reaction: { emoji: "👍", message_id } });
  const thanks = `Thanks ${uid()}`;
  await receiveWhatsApp(api, account, number, { message: thanks, context: { id: message_id } });
  const failed = `Could you share ${uid()}?`;
  const failedName = await agent.call<string>(`${MESSAGES_API}.send_message`, { ...scope, message: failed });
  await updateWhatsAppStatus(api, account, failedName, "failed", [{ code: 131026, title: "Undeliverable" }]);
  return { ticket, question, answer, failed, thanks, account, number, to: first.to };
}

async function insertTemplate(api: Api, account: string): Promise<string> {
  const template = await api.insert("WA Template", {
    template_label: `E2E portal ${uid()}`,
    template_type: "Utility",
    language: "en",
    header_type: "Text",
    header_text: "Delivery update",
    message: "Your ticket {{ticket}} is out for delivery.",
    footer: "Helpdesk team",
    reference_doctype: "HD Ticket",
    whatsapp_account: account,
    template_variables: [{ variable_name: "ticket", variable_example: "42", variable_field: "name" }],
    buttons: [{ button_type: "URL", button_text: "Track parcel", url: "https://example.com/track" }],
  });
  await approveTemplate(api, template.name);
  return template.name;
}

const conversation = (page: Page) => page.getByRole("log", { name: "Conversation" });
const messageRow = (page: Page, text: string) =>
  conversation(page).getByRole("listitem").filter({ hasText: text });

async function expectReadOnlyThread(page: Page, thread: Thread) {
  await page.goto(`/help/my-tickets/${thread.ticket}`);
  await expect(messageRow(page, thread.question)).toBeVisible();
  await expect(messageRow(page, thread.question).locator("b")).toHaveText("Help");
  await expect(conversation(page).getByText("Photo", { exact: true })).toBeVisible();
  await expect(conversation(page).getByText("receipt.pdf", { exact: true })).toBeVisible();
  await expect(messageRow(page, thread.answer).first().getByLabel("Reaction: 👍")).toBeVisible();
  await expect(messageRow(page, thread.thanks).locator("blockquote")).toHaveText(thread.answer);
  await expect(messageRow(page, thread.failed)).toContainText("Not delivered");
  await expect(messageRow(page, thread.answer).first()).not.toContainText("Not delivered");
  const template = messageRow(page, `Your ticket ${thread.ticket} is out for delivery.`);
  await expect(template.getByText("Delivery update")).toBeVisible();
  await expect(template.getByText("Helpdesk team")).toBeVisible();
  await expect(template.getByRole("list", { name: "Reply buttons" })).toHaveText("Track parcel");
  await expect(page.getByText("Reply to this ticket on WhatsApp.")).toBeVisible();
  await expect(page.getByRole("textbox")).toHaveCount(0);
}

async function shoot(page: Page, scenario: string) {
  const device = (page.viewportSize()?.width ?? 1440) < 640 ? "phone" : "desktop";
  for (const theme of ["light", "dark"] as const) {
    await page.evaluate((value) => document.documentElement.setAttribute("data-theme", value), theme);
    await page.screenshot({
      path: join(SCREENS, `portal-ui-${scenario}-${device}-${theme}.png`),
      animations: "disabled",
    });
  }
  await page.evaluate(() => document.documentElement.setAttribute("data-theme", "light"));
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("a WhatsApp ticket shows its conversation read-only, customer on the right", async ({
      page,
      api,
      apiAs,
    }) => {
      const thread = await seedThread(api, await apiAs("agent"));
      await expectReadOnlyThread(page, thread);

      const agentTime = await messageRow(page, thread.answer).first().locator("time").boundingBox();
      const customerTime = await messageRow(page, thread.question).locator("time").boundingBox();
      expect(customerTime!.x).toBeGreaterThan(agentTime!.x);
      await shoot(page, "thread");
    });

    test("a closed WhatsApp ticket shows the Closed-Ticket Prompt's buttons read-only", async ({
      page,
      api,
      apiAs,
    }) => {
      const thread = await seedThread(api, await apiAs("agent"));
      await api.update("HD Ticket", thread.ticket, { status: "Closed" });
      const held = await receiveWhatsApp(api, thread.account, thread.number, { message: "Me again" });
      expect(held.reference_docname).toBeFalsy();

      await page.goto(`/help/my-tickets/${thread.ticket}`);
      const prompt = messageRow(page, "Do you want to raise a new one?");
      const buttons = prompt.getByRole("list", { name: "Reply buttons" }).getByRole("listitem");
      await expect(buttons).toHaveText(["Create new ticket", "No, thanks"]);
      await expect(buttons.getByRole("button")).toHaveCount(0);
      // a reply now raises the prompt instead of reaching this ticket
      await expect(page.getByText("Reply to this ticket on WhatsApp.")).toHaveCount(0);
      await prompt.scrollIntoViewIfNeeded();
      await shoot(page, "prompt");
    });

    test("the reply note opens WhatsApp at the Business Number, or stays plain without one", async ({
      page,
      api,
      apiAs,
    }) => {
      const thread = await seedThread(api, await apiAs("agent"));
      await page.goto(`/help/my-tickets/${thread.ticket}`);
      const link = page.getByRole("link", { name: "Reply to this ticket on WhatsApp." });
      await expect(link).toHaveAttribute("href", `https://wa.me/${FAKE_DISPLAY_NUMBER.replace(/\D/g, "")}`);
      await expect(link).toHaveAttribute("target", "_blank");
      await expect(link).toHaveAttribute("rel", "noopener");
      await link.scrollIntoViewIfNeeded();
      await shoot(page, "note-link");

      await page.route(/whatsapp\.api\.get_messages/, async (route) => {
        const response = await route.fetch();
        const body = await response.json();
        body.message.business_number = null;
        await route.fulfill({ response, json: body });
      });
      await page.reload();
      await expect(page.getByText("Reply to this ticket on WhatsApp.")).toBeVisible();
      await expect(link).toHaveCount(0);
      await shoot(page, "note-plain");
    });

    test("new WhatsApp messages appear on an open portal thread", async ({ page, api, apiAs }) => {
      const agent = await apiAs("agent");
      const thread = await seedThread(api, agent);
      await expectReadOnlyThread(page, thread);
      const followUp = `Courier ${uid()} is at your door`;
      await agent.call(`${MESSAGES_API}.send_message`, {
        to: thread.to,
        message: followUp,
        reference_doctype: "HD Ticket",
        reference_docname: thread.ticket,
      });
      await expect(messageRow(page, followUp)).toBeVisible();
      const thanks = `Got it ${uid()}`;
      const reply = await receiveWhatsApp(api, thread.account, thread.number, { message: thanks });
      expect(reply.reference_docname).toBe(thread.ticket);
      await expect(messageRow(page, thanks)).toBeVisible();

      // a send failing later is the one status change the portal shows
      const late = `Late ${uid()}`;
      const lateName = await agent.call<string>(`${MESSAGES_API}.send_message`, {
        to: thread.to,
        message: late,
        reference_doctype: "HD Ticket",
        reference_docname: thread.ticket,
      });
      await expect(messageRow(page, late)).not.toContainText("Not delivered");
      await updateWhatsAppStatus(api, thread.account, lateName, "failed", [{ code: 131026, title: "Undeliverable" }]);
      await expect(messageRow(page, late)).toContainText("Not delivered");
    });

    test("a burst of messages all reach an open thread", async ({ page, api, apiAs }) => {
      const thread = await seedThread(api, await apiAs("agent"));
      await expectReadOnlyThread(page, thread);
      // the first read answers last, so a stale reply would land after a fresh one
      let reads = 0;
      await page.route(/whatsapp\.api\.get_messages/, async (route) => {
        const response = await route.fetch();
        if (++reads === 1) await new Promise((resolve) => setTimeout(resolve, 3000));
        await route.fulfill({ response });
      });
      const burst = [`One ${uid()}`, `Two ${uid()}`, `Three ${uid()}`];
      for (const message of burst) await receiveWhatsApp(api, thread.account, thread.number, { message });
      for (const message of burst) await expect(messageRow(page, message)).toBeVisible({ timeout: 10000 });
      await page.waitForTimeout(3500);
      for (const message of burst) await expect(messageRow(page, message)).toBeVisible();
    });

    test("a document's sender-chosen name stays text, never a link", async ({ page, api, apiAs }) => {
      const thread = await seedThread(api, await apiAs("agent"));
      for (const filename of ["https://evil.example/login", "//evil.example/x"]) {
        await receiveWhatsApp(api, thread.account, thread.number, {
          type: "document",
          document: { id: uid(), mime_type: "application/pdf", filename },
        });
      }
      await page.goto(`/help/my-tickets/${thread.ticket}`);
      for (const filename of ["https://evil.example/login", "//evil.example/x"]) {
        await expect(conversation(page).getByText(filename, { exact: true })).toBeVisible();
      }
      await expect(conversation(page).locator('a[href*="evil.example"]')).toHaveCount(0);
    });

    test("the thread loads with chat bubbles, never email cards", async ({ page, api, apiAs }) => {
      const thread = await seedThread(api, await apiAs("agent"));
      await page.route(/whatsapp\.api\.get_messages/, async (route) => {
        const response = await route.fetch();
        await new Promise((resolve) => setTimeout(resolve, 4000));
        await route.fulfill({ response }).catch(() => {});
      });
      await page.goto(`/help/my-tickets/${thread.ticket}`);
      const skeleton = page.locator(".portal-thread.is-chat .portal-skeleton");
      await expect(skeleton).toBeVisible();
      await expect(skeleton.locator(".rounded-6")).not.toHaveCount(0);
      await expect(skeleton.locator(".border")).toHaveCount(0);
      await shoot(page, "loading");
    });

    test("a thread that fails to load offers a retry instead of the reply note", async ({ page, api, apiAs }) => {
      const thread = await seedThread(api, await apiAs("agent"));
      await page.route(/whatsapp\.api\.get_messages/, (route) => route.fulfill({ status: 500, body: "{}" }));
      await page.goto(`/help/my-tickets/${thread.ticket}`);
      await expect(page.getByText("Could not load this conversation.")).toBeVisible();
      await expect(page.getByText("Reply to this ticket on WhatsApp.")).toHaveCount(0);
      await shoot(page, "error");

      await page.unroute(/whatsapp\.api\.get_messages/);
      await page.getByRole("button", { name: "Retry" }).click();
      await expect(messageRow(page, thread.question)).toBeVisible();
      await expect(page.getByText("Reply to this ticket on WhatsApp.")).toBeVisible();
    });

    test("a customer cannot load someone else's WhatsApp thread", async ({ page, api, apiAs }) => {
      const account = await makeWhatsAppAccount(api, metaUrl);
      const question = `Private ${uid()}`;
      const { reference_docname: ticket } = await receiveWhatsApp(api, account, newWhatsAppNumber(), {
        message: question,
      });
      const customer = await apiAs("customer");

      for (const [method, params] of [
        [`${API}.get_messages`, { ticket }],
        [`${MESSAGES_API}.get_messages`, { references: JSON.stringify([["HD Ticket", ticket]]) }],
      ] as const) {
        const response = await customer.raw(method, params);
        expect(response.status()).toBe(403);
        expect(await response.text()).not.toContain(question);
      }
      await page.goto(`/help/my-tickets/${ticket}`);
      await expect(page.getByText("Ticket not found")).toBeVisible();
      await expect(page.getByText(question)).toHaveCount(0);
      await expect(conversation(page)).toHaveCount(0);
      await shoot(page, "denied");
    });
  });
}
