import { createHmac } from "node:crypto";
import { request } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { openTicket } from "../../../helpers/ticket";
import { FakeMeta, makeWhatsAppAccount, newWhatsAppNumber } from "../../../helpers/whatsapp";
import { siteHeader } from "../../../helpers/site";

// An account connected with Meta gets its webhooks from Central, signed with the account's own
// webhook secret in X-Frappe-Central-Signature. Central is faked here: the test signs the body.
usePersona("agent");

const WEBHOOK = "/api/method/whatsapp.whatsapp.webhook.handler";

const meta = new FakeMeta();
let metaUrl: string;

test.beforeAll(async () => {
  metaUrl = await meta.start();
});
test.afterAll(() => meta.stop());

/** A Meta-connected account: its WABA ID and webhook secret, as the Connect with Meta flow stores them. */
async function connectedAccount(api: Api, secret: string) {
  const account = await makeWhatsAppAccount(api, metaUrl);
  await api.update("WA Account", account, { webhook_secret: secret, connected_with_meta: 1 });
  const { phone_id, business_id } = await api.get("WA Account", account);
  return { phone_id, business_id };
}

/** Post a customer's message as Central relays it, signed with `secret`; return the HTTP status. */
async function relay(account: { phone_id: string; business_id: string }, secret: string, text: string) {
  const id = `wamid.${uid()}`;
  const from = newWhatsAppNumber();
  const value = {
    metadata: { phone_number_id: account.phone_id },
    contacts: [{ profile: { name: "E2E Relay" }, wa_id: from }],
    messages: [{ from, id, timestamp: "0", type: "text", text: { body: text } }],
  };
  const body = JSON.stringify({
    object: "whatsapp_business_account",
    entry: [{ id: account.business_id, changes: [{ field: "messages", value }] }],
  });
  const signature = createHmac("sha256", secret).update(body).digest("hex");
  const guest = await request.newContext({
    baseURL: process.env.BASE_URL || "http://localhost:8000",
    extraHTTPHeaders: {
      ...siteHeader(),
      "content-type": "application/json",
      "X-Frappe-Central-Signature": `sha256=${signature}`,
    },
    storageState: { cookies: [], origins: [] },
  });
  const response = await guest.post(WEBHOOK, { data: body });
  const status = response.status();
  await guest.dispose();
  return { status, id };
}

async function storedMessage(api: Api, id: string) {
  const [stored] = await api.list("WA Message", {
    fields: ["name", "reference_docname"],
    filters: { message_id: id },
  });
  return stored;
}

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test.describe(`at ${viewport.width}px`, () => {
    test.use({ viewport });

    test("a message relayed by Central opens a ticket the agent can read", async ({ page, api }) => {
      const secret = `secret-${uid()}`;
      const account = await connectedAccount(api, secret);
      const text = `Relayed order ${uid()} is late`;

      const { status, id } = await relay(account, secret, text);
      expect(status).toBe(200);

      const stored = await storedMessage(api, id);
      expect(stored.reference_docname).toBeTruthy();
      // the first message becomes the ticket's subject
      await openTicket(page, stored.reference_docname);
      await expect(page.getByText(text).first()).toBeVisible();
    });

    test("a relayed message signed with another account's secret is refused", async ({ api }) => {
      const account = await connectedAccount(api, `secret-${uid()}`);
      const other = `secret-${uid()}`;
      await connectedAccount(api, other);

      const { status, id } = await relay(account, other, `Forged ${uid()}`);
      expect(status).toBe(403);
      expect(await storedMessage(api, id)).toBeUndefined();
    });

    test("a message relayed for a WABA no account here uses is gone", async ({ api }) => {
      // Central drops its route for this WABA and site when the site answers 410
      const gone = { phone_id: `phone-${uid()}`, business_id: `waba-gone-${uid()}` };

      const { status, id } = await relay(gone, `secret-${uid()}`, `Gone ${uid()}`);
      expect(status).toBe(410);
      expect(await storedMessage(api, id)).toBeUndefined();
    });
  });
}
