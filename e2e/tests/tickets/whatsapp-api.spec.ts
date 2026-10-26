import { request } from "@playwright/test";
import { expectDenied } from "../../helpers/api";
import { expect, test } from "../../helpers/fixtures";
import { raiseTicket } from "../../helpers/factories";
import { personas } from "../../helpers/personas";
import { siteHeader } from "../../helpers/site";
import {
  FakeMeta,
  makeWhatsAppAccount,
  newWhatsAppNumber,
  receiveWhatsApp,
  whatsAppMessagesOf,
} from "../../helpers/whatsapp";

const APP = "whatsapp.whatsapp.api.messages";
const API = "helpdesk.integrations.whatsapp.api";

const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

test("an agent replies, quotes and reacts from the ticket's business number", async ({
  api,
  apiAs,
}) => {
  const number = newWhatsAppNumber();
  const first = await receiveWhatsApp(api, await makeWhatsAppAccount(api, metaUrl), number);
  const ticket = first.reference_docname;
  const agent = await apiAs("agent");
  const { to } = await agent.call(`${API}.get_conversation`, { ticket });
  const reply = { to, reference_doctype: "HD Ticket", reference_docname: ticket };

  await agent.call(`${APP}.send_message`, { ...reply, message: "Looking into it" });
  await agent.call(`${APP}.send_message`, { ...reply, message: "Which one?", reply_to: first.name });
  await agent.call(`${APP}.react_to_message`, { message: first.name, emoji: "👍" });

  // stored rows, not Meta's log: the Graph API URL is one site setting other runs may move
  const sent = await whatsAppMessagesOf(api, ticket, ["to", "message", "context_message_id", "reaction"]);
  expect(sent.filter((row) => row.to === first.to && row.message !== first.message)).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ message: "Looking into it", context_message_id: null }),
      expect.objectContaining({ message: "Which one?", context_message_id: first.message_id }),
      expect.objectContaining({ reaction: "👍", context_message_id: first.message_id }),
    ])
  );
  const thread = await agent.call(`${APP}.get_messages`, {
    references: JSON.stringify([["HD Ticket", ticket]]),
  });
  expect(thread).toHaveLength(3);
  expect(thread[0]).toMatchObject({ name: first.name, reactions: [{ emoji: "👍" }] });
  expect(thread[2]).toMatchObject({ reply_to: first.name });
  expect((await agent.call(`${API}.get_conversation`, { ticket })).reply_window_open).toBe(true);
  expect((await api.get("HD Ticket", ticket)).first_responded_on).toBeTruthy();
});

test("sending on an email ticket is refused", async ({ apiAs }) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  const agent = await apiAs("agent");
  const response = await agent.raw(`${APP}.send_message`, {
    to: newWhatsAppNumber(),
    message: "Hi",
    reference_doctype: "HD Ticket",
    reference_docname: ticket.name,
  });
  expect(response.ok()).toBeFalsy();
  expect(await response.text()).toContain("is not a WhatsApp ticket");
});

test("the customer reads their own WhatsApp thread but cannot send, guests get nothing", async ({
  api,
  apiAs,
  baseURL,
}) => {
  const number = newWhatsAppNumber();
  const contact = await api.exists("Contact", { email_id: personas.customer.email });
  const original = (await api.get("Contact", contact!)).phone_nos;
  // replaced, not appended: other specs may leave a primary mobile on the shared persona
  await api.update("Contact", contact!, {
    phone_nos: [{ phone: `+${number}`, is_primary_mobile_no: 1 }],
  });
  try {
    const first = await receiveWhatsApp(api, await makeWhatsAppAccount(api, metaUrl), number);
    const ticket = first.reference_docname;
    const customer = await apiAs("customer");
    const thread = await customer.call(`${API}.get_messages`, { ticket });
    expect(thread.messages.map((message: any) => message.name)).toEqual([first.name]);
    await expectDenied(
      customer.raw(`${APP}.send_message`, {
        to: first.to,
        message: "Hi",
        reference_doctype: "HD Ticket",
        reference_docname: ticket,
      })
    );

    const guest = await request.newContext({ baseURL, extraHTTPHeaders: siteHeader() });
    const response = await guest.post(`/api/method/${API}.get_messages`, { data: { ticket } });
    expect(response.ok()).toBeFalsy();
    await guest.dispose();
  } finally {
    await api.update("Contact", contact!, { phone_nos: original });
  }
});
