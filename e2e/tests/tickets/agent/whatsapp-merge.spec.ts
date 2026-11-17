import type { Api } from "../../../helpers/api";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { openTicket } from "../../../helpers/ticket";
import { FakeMeta, makeWhatsAppAccount, newWhatsAppNumber, receiveWhatsApp } from "../../../helpers/whatsapp";

usePersona("agent");

const MERGE = "helpdesk.helpdesk.doctype.hd_ticket.api.merge_ticket";
const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

/** Open a WhatsApp Ticket the way the webhook does, by receiving a message. */
async function receiveMessage(api: Api): Promise<string> {
  const account = await makeWhatsAppAccount(api, metaUrl);
  const message = await receiveWhatsApp(api, account, newWhatsAppNumber(), {
    message: `WhatsApp merge ${uid()}`,
  });
  return message.reference_docname;
}

test("a WhatsApp ticket offers no merge and the server refuses one", async ({ page, api }) => {
  const ticket = await receiveMessage(api);
  const other = await receiveMessage(api);

  await openTicket(page, ticket);
  // Merge is an agent's only header action, so without it the menu is gone
  await expect(page.getByRole("banner").getByRole("button", { name: "More actions" })).toHaveCount(0);

  await expect(api.call(MERGE, { source: ticket, target: other })).rejects.toThrow(
    "WhatsApp tickets cannot be merged"
  );
  expect((await api.get("HD Ticket", ticket)).is_merged).toBe(0);
});
