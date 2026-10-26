import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { raiseTicket } from "../../../helpers/factories";
import { openTicket } from "../../../helpers/ticket";
import {
  FakeMeta,
  makeWhatsAppAccount,
  newWhatsAppNumber,
  pressPromptButton,
  receiveWhatsApp,
  whatsAppMessagesOf,
} from "../../../helpers/whatsapp";

usePersona("agent");

type Ticket = { name: string; subject: string };

const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

const makeAccount = (api: Api) => makeWhatsAppAccount(api, metaUrl);

/** Open a WhatsApp Ticket the way the webhook does, by receiving a message. */
async function receiveMessage(api: Api, account: string, from = newWhatsAppNumber()): Promise<Ticket> {
  const subject = `WhatsApp merge ${uid()}`;
  const message = await receiveWhatsApp(api, account, from, { message: subject });
  return { name: message.reference_docname, subject };
}

/** Two open tickets of one customer: they ask for a new one, then an agent reopens the first. */
async function ticketsOfOneCustomer(api: Api, account: string): Promise<[Ticket, Ticket]> {
  const from = newWhatsAppNumber();
  const first = await receiveMessage(api, account, from);
  await api.update("HD Ticket", first.name, { status: "Closed" });
  await receiveWhatsApp(api, account, from, { message: "Hello again" });
  const answer = await pressPromptButton(api, account, from, first.name, "helpdesk_new_ticket");
  const second = { name: answer.reference_docname, subject: `WhatsApp merge ${uid()}` };
  await api.update("HD Ticket", second.name, { subject: second.subject });
  await api.update("HD Ticket", first.name, { status: "Open" });
  return [first, second];
}

async function mergeFromUi(page: Page, source: Ticket, target: Ticket) {
  await openTicket(page, source.name);
  await page.getByRole("banner").getByRole("button", { name: "More actions" }).click();
  await page.getByRole("menuitem", { name: "Merge Ticket" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "Ticket", exact: true }).click();
  await page.getByRole("combobox", { name: "Select Ticket" }).fill(target.subject);
  await page.getByRole("option", { name: `${target.subject} ${target.name},` }).click();
  await dialog.getByRole("button", { name: `Merge with ticket #${target.name}` }).click();
}

const messagesOf = (api: Api, ticket: string) => whatsAppMessagesOf(api, ticket, ["name"]);

test("a WhatsApp ticket cannot merge into a portal ticket", async ({ page, api, apiAs }) => {
  const target = await raiseTicket(await apiAs("customer"));
  const source = await receiveMessage(api, await makeAccount(api));

  await mergeFromUi(page, source, target);
  await expect(
    page.getByText("A WhatsApp ticket can only be merged with another WhatsApp ticket")
  ).toBeVisible();
  expect((await api.get("HD Ticket", source.name)).is_merged).toBe(0);
});

test("WhatsApp tickets on different numbers cannot merge", async ({ page, api }) => {
  const target = await receiveMessage(api, await makeAccount(api));
  const source = await receiveMessage(api, await makeAccount(api));

  await mergeFromUi(page, source, target);
  await expect(
    page.getByText("WhatsApp tickets can only be merged when they share a business number")
  ).toBeVisible();
});

test("WhatsApp tickets of different customers cannot merge", async ({ page, api }) => {
  const account = await makeAccount(api);
  const target = await receiveMessage(api, account);
  const source = await receiveMessage(api, account);

  await mergeFromUi(page, source, target);
  await expect(
    page.getByText("WhatsApp tickets can only be merged when they belong to the same customer")
  ).toBeVisible();
});

test("a WhatsApp merge moves the messages onto the target", async ({ page, api }) => {
  const [source, target] = await ticketsOfOneCustomer(api, await makeAccount(api));
  const moved = (await messagesOf(api, source.name)).map((m) => m.name);

  await mergeFromUi(page, source, target);
  await expect(page.getByText("Ticket merged successfully.")).toBeVisible();
  expect(await messagesOf(api, source.name)).toEqual([]);
  const onTarget = (await messagesOf(api, target.name)).map((m) => m.name);
  expect(onTarget).toEqual(expect.arrayContaining(moved));
  expect(await api.get("HD Ticket", source.name)).toMatchObject({
    is_merged: 1,
    merged_with: target.name,
  });
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 800 } });

  test("a merged WhatsApp ticket opens as closed and merged", async ({ page, api }) => {
    const [target, source] = await ticketsOfOneCustomer(api, await makeAccount(api));
    await api.call("helpdesk.helpdesk.doctype.hd_ticket.api.merge_ticket", {
      source: source.name,
      target: target.name,
    });

    await openTicket(page, source.name);
    await expect(page.getByText("Closed").first()).toBeVisible();
    expect(await messagesOf(api, source.name)).toEqual([]);
  });
});
