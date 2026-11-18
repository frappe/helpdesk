// Shared fixture for the browser tests.
//
// `app.pageAs(role)` gives a browser page logged in as a seeded account; this is
// what the user does. `app.api` is a separate channel used only to arrange a
// starting condition (e.g. "a resolved ticket exists") and to check a
// postcondition in the stored record, as the agent would see it.
import { test as base, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import { SEED } from "./global-setup.mjs";

const ENV = Object.fromEntries(
  fs.readFileSync(new URL("../../.env", import.meta.url), "utf8")
    .split("\n")
    .filter((line) => line.includes("=") && !line.startsWith("#"))
    .map((line) => [line.slice(0, line.indexOf("=")), line.slice(line.indexOf("=") + 1).trim()])
);
const ACCOUNTS = { customerA: "SQE_CUSTOMER_A", customerB: "SQE_CUSTOMER_B", agent: "SQE_AGENT" };
// route fixture traffic through the passive proxy too when one is configured
const PROXY = process.env.SQE_PROXY ? { proxy: { server: process.env.SQE_PROXY, bypass: "" } } : {};
const NEW = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new";
const ASSIGNEES = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_assignees";

export const emailOf = (role) => ENV[`${ACCOUNTS[role]}_EMAIL`];
const credentials = (role) => ({ usr: emailOf(role), pwd: ENV[`${ACCOUNTS[role]}_PASSWORD`] });

export const test = base.extend({
  app: async ({ browser, playwright, baseURL }, use) => {
    const disposables = [];

    const apiAs = async (role) => {
      const context = await playwright.request.newContext({ baseURL, ...PROXY });
      const response = await context.post("/api/method/login", { data: credentials(role) });
      expect(response.status(), `API login as ${role}`).toBe(200);
      disposables.push(() => context.dispose());
      return context;
    };
    const api = { customerA: await apiAs("customerA"), agent: await apiAs("agent") };

    const app = {
      /** A page logged in as `role`; pass null for a visitor who is not logged in. */
      async pageAs(role) {
        const context = await browser.newContext({ baseURL, ...PROXY });
        disposables.push(() => context.close());
        if (role) {
          const response = await context.request.post("/api/method/login", { data: credentials(role) });
          expect(response.status(), `browser login as ${role}`).toBe(200);
        }
        return context.newPage();
      },

      /** Unique, recognisable subject for one test. */
      subject(label) {
        return `${label} ${Date.now().toString(36)}`;
      },

      // --- arrange ---------------------------------------------------------
      async newTicket(subject, description = "<p>Paper is stuck in tray 1.</p>") {
        const response = await api.customerA.post(NEW, { data: { doc: { subject, description } } });
        expect(response.status()).toBe(200);
        return (await response.json()).message.name;
      },
      async setStatus(name, status) {
        const response = await api.agent.put(`/api/resource/HD Ticket/${name}`, { data: { status } });
        expect(response.status()).toBe(200);
      },
      /** A sent agent reply (the desk needs a mail account to send one; the test site has none). */
      agentReply(name) {
        execFileSync("bash", [SEED, "agent-reply", "--ticket", String(name)], { stdio: "pipe" });
      },
      async resolvedTicketWithReply(subject) {
        const name = await app.newTicket(subject);
        app.agentReply(name);
        await app.setStatus(name, "Resolved");
        return name;
      },

      // --- postconditions --------------------------------------------------
      async stored(name) {
        const response = await api.agent.get(`/api/resource/HD Ticket/${name}`);
        expect(response.status()).toBe(200);
        return (await response.json()).data;
      },
      async ticketsWithSubject(subject) {
        const filters = JSON.stringify([["subject", "=", subject]]);
        const response = await api.agent.get(`/api/resource/HD Ticket?filters=${encodeURIComponent(filters)}`);
        expect(response.status()).toBe(200);
        return (await response.json()).data.map((row) => row.name);
      },
      /** Number of messages in the ticket's conversation, as the agent sees it. */
      async messageCount(name) {
        const response = await api.agent.get(
          `/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one?name=${name}`
        );
        expect(response.status()).toBe(200);
        return (await response.json()).message.communications.length;
      },
      async ticketCount() {
        const response = await api.agent.get("/api/resource/HD Ticket?limit_page_length=100000");
        return (await response.json()).data.length;
      },
      async assignees(name) {
        const response = await api.agent.get(`${ASSIGNEES}?ticket=${name}`);
        expect(response.status()).toBe(200);
        return (await response.json()).message.map((row) => row.name);
      },
    };

    await use(app);
    for (const dispose of disposables.reverse()) await dispose();
  },
});

export { expect };

// --- screen helpers ------------------------------------------------------------

export const newTicketForm = (page) => ({
  subject: page.getByRole("textbox", { name: "A short description" }),
  description: page.locator('[contenteditable="true"]').first(),
  submit: page.getByRole("button", { name: "Submit" }),
  discard: page.getByRole("button", { name: "Discard" }),
  prompt: page.getByRole("heading", { name: "Please enter a subject to continue" }),
});

export const ticketIdFromUrl = (page) => page.url().split("/").pop();

/** The "Ticket details" panel on the customer's ticket page, as one line of text. */
export const customerDetails = (page) => page.locator("body");

export const agentStatusButton = (page, status) =>
  page.getByRole("banner").getByRole("button", { name: status, exact: true });

/** Pick `option` from the combobox labelled `label`. The box filters its list by
 *  the text it holds (initially the current value), so the wanted value is typed. */
export async function chooseOption(page, label, option) {
  const box = page.getByRole("combobox", { name: label });
  await box.click();
  await box.fill(option);
  await page.getByRole("option", { name: option, exact: true }).click();
}

export async function agentChangeStatus(page, from, to) {
  await agentStatusButton(page, from).click();
  await page.getByRole("menuitem", { name: to, exact: true }).click();
}
