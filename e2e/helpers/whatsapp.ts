import { execFileSync } from "node:child_process";
import { createHash, createHmac } from "node:crypto";
import { createServer, type Server, type ServerResponse } from "node:http";
import type { AddressInfo } from "node:net";
import { resolve } from "node:path";
import { expect, request } from "@playwright/test";
import type { Api } from "./api";
import { uid } from "./factories";
import { siteHeader } from "./site";

/** Meta's display number for every fake Business Number. */
export const FAKE_DISPLAY_NUMBER = "+1 555-010-0199";

const WEBHOOK = "/api/method/whatsapp.whatsapp.webhook.handler";
const SETTINGS = "WA Settings";

/** Stands in for Meta's Graph API: records every message sent, uploads media and answers number lookups. */
export class FakeMeta {
  sent: Record<string, any>[] = [];
  private server: Server = createServer((incoming, response) => {
    let body = "";
    incoming.on("data", (chunk) => (body += chunk));
    incoming.on("end", () => {
      response.setHeader("content-type", "application/json");
      response.end(JSON.stringify(this.reply(incoming.method, incoming.url, body)));
    });
  });

  private reply(method = "GET", url = "", body: string) {
    if (method === "GET") return { display_phone_number: FAKE_DISPLAY_NUMBER };
    if (!url.endsWith("/messages")) return { id: uid() };
    this.sent.push(JSON.parse(body || "{}"));
    return { messages: [{ id: `wamid.${uid()}` }] };
  }

  async start(): Promise<string> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    return `http://127.0.0.1:${(this.server.address() as AddressInfo).port}`;
  }

  stop() {
    this.server.close();
  }
}

/** A Business Number that creates tickets; the whatsapp app sends every account's Graph API calls to `url`. */
export async function makeWhatsAppAccount(api: Api, url: string): Promise<string> {
  await api.update(SETTINGS, SETTINGS, { whatsapp_api_url: url });
  const account = await api.insert("WA Account", {
    account_name: `E2E ${uid()}`,
    phone_id: uid(),
    business_id: uid(),
    status: "Active",
    access_token: "e2e-token",
    append_actions: [{ append_to: "HD Ticket", trigger_on: "Incoming" }],
  });
  return account.name;
}

/**
 * Post a customer's message to the webhook as Guest, the way Meta does, and return the stored WA Message.
 * `message` is the text; other values are Meta message fields, such as `type` and `interactive`.
 */
export async function receiveWhatsApp(
  api: Api,
  account: string,
  from: string,
  { message = `Order ${uid()} is late`, ...values }: Record<string, any> = {}
) {
  const id = `wamid.${uid()}`;
  const { phone_id } = await api.get("WA Account", account);
  const value = {
    metadata: { phone_number_id: phone_id },
    contacts: [{ profile: { name: "E2E WhatsApp" }, wa_id: from }],
    messages: [{ from, id, timestamp: "0", type: "text", text: { body: message }, ...values }],
  };
  await postToWebhook(api, JSON.stringify({ entry: [{ changes: [{ field: "messages", value }] }] }));
  const [stored] = await api.list("WA Message", {
    fields: ["name", "reference_docname", "message", "message_id", "to"],
    filters: { message_id: id },
  });
  return stored;
}

/** Press a button on the latest Closed-Ticket Prompt sent on `ticket`, and return the stored answer. */
export async function pressPromptButton(
  api: Api,
  account: string,
  from: string,
  ticket: string,
  buttonId: "helpdesk_new_ticket" | "helpdesk_no_ticket"
) {
  const [prompt] = await api.list("WA Message", {
    fields: ["name"],
    filters: { reference_docname: ticket, direction: "Outgoing", owner: "Guest" },
    limit: 1,
  });
  const { message_id, interactive_buttons } = await api.get("WA Message", prompt.name);
  const { title } = interactive_buttons.find((button: any) => button.button_id === buttonId);
  return receiveWhatsApp(api, account, from, {
    message: "",
    type: "interactive",
    interactive: { type: "button_reply", button_reply: { id: buttonId, title } },
    context: { id: message_id },
  });
}

/** Post Meta's delivery status for a sent message, such as "read", or "failed" with Meta's errors. */
export async function updateWhatsAppStatus(
  api: Api,
  account: string,
  message: string,
  status: "sent" | "delivered" | "read" | "failed",
  errors: Record<string, unknown>[] = []
) {
  const [{ phone_id }, { message_id }] = await Promise.all([
    api.get("WA Account", account),
    api.get("WA Message", message),
  ]);
  const value = {
    metadata: { phone_number_id: phone_id },
    statuses: [{ id: message_id, status, timestamp: "0", errors }],
  };
  await postToWebhook(api, JSON.stringify({ entry: [{ changes: [{ field: "messages", value }] }] }));
}

/** Approve a WA Template the way Meta's review does, through the template status webhook. */
export async function approveTemplate(api: Api, template: string) {
  const { whatsapp_template_id } = await api.get("WA Template", template);
  const value = { message_template_id: whatsapp_template_id, event: "APPROVED", status: "APPROVED" };
  await postToWebhook(
    api,
    JSON.stringify({ entry: [{ changes: [{ field: "message_template_status_update", value }] }] })
  );
}

/** Sign the body with the site's webhook secret when it has one, as Meta does. */
async function postToWebhook(api: Api, body: string) {
  const secret = (await api.get(SETTINGS, SETTINGS)).webhook_secret;
  const headers: Record<string, string> = { ...siteHeader(), "content-type": "application/json" };
  if (secret) {
    headers["X-Hub-Signature-256"] = `sha256=${createHmac("sha256", secret).update(body).digest("hex")}`;
  }
  const baseURL = process.env.BASE_URL || "http://localhost:8000";
  // the runner hands every new context the spec's persona session, so clear it to post as Guest
  const guest = await request.newContext({
    baseURL,
    extraHTTPHeaders: headers,
    storageState: { cookies: [], origins: [] },
  });
  const response = await guest.post(WEBHOOK, { data: body });
  expect(response.ok(), await response.text()).toBeTruthy();
  await guest.dispose();
}

/** A fresh WhatsApp number, so every test gets its own contact and ticket. */
export const newWhatsAppNumber = () => `9196${Date.now().toString().slice(-8)}`;

/** The WA Messages stored on a ticket. */
export function whatsAppMessagesOf(api: Api, ticket: string, fields: string[]) {
  return api.list("WA Message", {
    fields,
    filters: { reference_doctype: "HD Ticket", reference_docname: ticket },
  });
}

/**
 * Stands in for Frappe Cloud in Meta's sign-in: the site's Pilot, which passes central.api.oauth.*
 * on to Central, and Meta's sign-in page, which sends the browser back to the site with a code.
 * The next sign-in relays `account`.
 */
export class FakeCentral {
  readonly token = `e2e-${uid()}`;
  url = "";
  account = { waba_id: "", phone_id: "" };
  /** central.api.oauth methods the site called, in order */
  asked: string[] = [];
  private signIns = new Map<string, { returnUrl: string; challenge: string }>();
  private codes = new Map<string, string>();
  private server: Server = createServer((incoming, response) => {
    let body = "";
    incoming.on("data", (chunk) => (body += chunk));
    incoming.on("end", () => {
      const url = new URL(incoming.url ?? "/", this.url);
      if (url.pathname === "/dialog/oauth") return this.signInPage(url, response);
      const method = url.pathname.match(/\/central\/central\.api\.oauth\.(\w+)$/)?.[1];
      let status = 404;
      let reply: unknown = { error: "not_found" };
      if (method && incoming.headers.authorization !== `Bearer ${this.token}`) {
        [status, reply] = [401, { error: "unauthorized" }];
      } else if (method) {
        this.asked.push(method);
        [status, reply] = this.answer(method, JSON.parse(body || "{}"));
      }
      response.writeHead(status, { "content-type": "application/json" });
      response.end(JSON.stringify(reply));
    });
  });

  private answer(method: string, data: Record<string, any>): [number, unknown] {
    if (method === "get_active_providers") return [200, { meta: null }];
    if (method === "start") {
      this.signIns.set(data.state, {
        returnUrl: data.return_url,
        challenge: data.code_challenge,
      });
      const link = `${this.url}/dialog/oauth?${new URLSearchParams({ state: data.state })}`;
      return [200, { authorize_url: link, client_id: "e2e-app", scopes: [] }];
    }
    if (method === "relay_token") {
      const challenge = this.codes.get(data.code);
      this.codes.delete(data.code);
      // PKCE: only the site that started this sign-in has the verifier of its challenge
      const verified = createHash("sha256")
        .update(data.code_verifier ?? "")
        .digest("base64url");
      if (!challenge || verified !== challenge) return [400, { error: "invalid_grant" }];
      return [
        200,
        {
          access_token: `e2e-token-${uid()}`,
          app_id: "e2e-app",
          ...this.account,
          pin: "123456",
          webhook_secret: `e2e-secret-${uid()}`,
        },
      ];
    }
    if (method === "disconnect") return [200, null];
    return [404, { error: "not_found" }];
  }

  /** Meta's sign-in. Continue goes back to the site, the way Central's callback sends it. */
  private signInPage(url: URL, response: ServerResponse) {
    const state = url.searchParams.get("state") ?? "";
    const signIn = this.signIns.get(state);
    if (!signIn) {
      response.writeHead(400).end("Unknown sign-in");
      return;
    }
    const code = uid();
    this.codes.set(code, signIn.challenge);
    const back = new URL(signIn.returnUrl);
    back.search = new URLSearchParams({ state, code }).toString();
    response.writeHead(200, { "content-type": "text/html" });
    response.end(`<h1>Meta sign-in</h1><a href="${back.href}">Continue</a>`);
  }

  async start(): Promise<string> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.url = `http://127.0.0.1:${(this.server.address() as AddressInfo).port}`;
    return this.url;
  }

  stop() {
    this.server.close();
  }
}

/**
 * Make the test site a Frappe Cloud v2 site whose Pilot is `central`, and return what makes it a
 * self-hosted site again. Both wait until the web server sees the change: it caches the site
 * config for up to a minute. Other specs that run on the site meanwhile see a v2 site.
 */
export async function becomeFrappeCloudSite(api: Api, central: FakeCentral) {
  setSiteConfig({
    pilot_endpoint: central.url,
    pilot_auth_token: central.token,
  });
  await waitForFrappeCloud(api, true);
  return async () => {
    // "None" removes the key
    setSiteConfig({ pilot_endpoint: "None", pilot_auth_token: "None" });
    await waitForFrappeCloud(api, false);
  };
}

function setSiteConfig(values: Record<string, string>) {
  const site = process.env.SITE_NAME;
  if (!site) throw new Error("SITE_NAME names the bench site to change");
  const bench = process.env.BENCH_PATH || resolve(__dirname, "../../../..");
  for (const [key, value] of Object.entries(values)) {
    execFileSync("bench", ["--site", site, "set-config", key, value], {
      cwd: bench,
      stdio: "pipe",
    });
  }
}

function waitForFrappeCloud(api: Api, on: boolean) {
  return expect
    .poll(() => api.call<boolean>("whatsapp.whatsapp.oauth.can_connect_with_meta"), {
      timeout: 90_000,
      intervals: [2_000],
    })
    .toBe(on);
}
