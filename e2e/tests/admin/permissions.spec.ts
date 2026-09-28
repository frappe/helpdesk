import type { APIResponse, Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { raiseTicket } from "../../helpers/factories";
import { PASSWORD, personas } from "../../helpers/personas";
import type { Api } from "../../helpers/api";
import { loginContext, openTicketInList } from "../../helpers/portal";

test.describe("plain agent", () => {
  usePersona("agent");

  test("cannot delete tickets, create agents or see admin settings", async ({
    page,
    api,
    apiAs,
    ticket,
  }) => {
    const agent = await apiAs("agent");

    await expectDenied(agent.raw("frappe.client.delete", { doctype: "HD Ticket", name: ticket.name }));
    await expectDenied(
      agent.raw("frappe.client.insert", {
        doc: { doctype: "HD Agent", user: personas.agent2.email, agent_name: "Nope" },
      })
    );

    await page.goto(`/helpdesk/tickets/${ticket.name}`);
    await page.locator("#app-header").getByRole("button").filter({ hasNotText: /\S/ }).last().click();
    await expect(page.getByRole("menuitem", { name: "Merge Ticket" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: "Delete" })).toHaveCount(0);
    await page.keyboard.press("Escape");

    await selectRow(page, api, personas.agent.email, ticket.name);
    await openSelectionMenu(page);
    await expect(page.getByRole("menuitem", { name: "Edit" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: "Delete" })).toHaveCount(0);
    await page.keyboard.press("Escape");

    await openSettings(page);
    const settings = page.getByRole("dialog");
    await expect(settings.getByText("Preferences")).toBeVisible();
    for (const tab of ["Email Accounts", "General", "Agents", "SLA Policies"]) {
      await expect(settings.getByText(tab, { exact: true })).toHaveCount(0);
    }
  });
});

test.describe("agent manager", () => {
  usePersona("manager");

  test("bulk deletes tickets from the list", async ({ page, api, ticket }) => {
    await selectRow(page, api, personas.manager.email, ticket.name);
    await openSelectionMenu(page);
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
    await expect.poll(() => api.exists("HD Ticket", { name: ticket.name })).toBeUndefined();
  });
});

test.describe("customer", () => {
  const secret = () => `internal note ${uid()}`;
  const spoofed = personas.customerManager.email;

  test("cannot read internal comments through any API", async ({ apiAs }) => {
    const customer = await apiAs("customer");
    const ticket = await raiseTicket(customer);
    const note = secret();
    await addComment(await apiAs("agent"), ticket.name, `<p>${note}</p>`);

    const reads = [
      customer.raw("frappe.desk.form.load.getdoc", { doctype: "HD Ticket", name: ticket.name }),
      customer.raw("frappe.desk.form.load.get_docinfo", { doctype: "HD Ticket", name: ticket.name }),
      customer.raw("helpdesk.api.timeline.get_comment_extras", { ticket: ticket.name }),
      customer.raw("helpdesk.helpdesk.doctype.hd_ticket.api.get_one", {
        name: ticket.name,
        is_customer_portal: true,
      }),
      customer.raw("frappe.client.get_list", {
        doctype: "Comment",
        filters: { reference_name: ticket.name },
        fields: ["content"],
      }),
      customer.raw("frappe.client.get", { doctype: "HD Ticket", name: ticket.name }),
    ];
    for (const response of await Promise.all(reads)) {
      expect(await response.text(), response.url()).not.toContain(note);
    }
  });

  test("cannot add a comment through the API", async ({ api, apiAs }) => {
    const customer = await apiAs("customer");
    const ticket = await raiseTicket(customer);
    const note = secret();

    await expectDenied(addComment(customer, ticket.name, note, true));
    await expectDenied(
      customer.raw("frappe.desk.form.utils.add_comment", {
        reference_doctype: "HD Ticket",
        reference_name: ticket.name,
        content: note,
        comment_email: personas.customer.email,
        comment_by: "Cora",
      })
    );
    const comments = await api.list("Comment", {
      filters: { reference_name: ticket.name, comment_type: "Comment" },
      fields: ["content"],
    });
    expect(comments.map((c) => c.content).join()).not.toContain(note);
  });

  test("cannot open a private file attached to an internal comment", async ({
    baseURL,
    apiAs,
    ticket,
  }) => {
    const agentContext = await loginContext(baseURL!, personas.agent.email, PASSWORD);
    // unique bytes: Frappe dedupes files by content, sharing one URL across owners
    const upload = await agentContext.post("/api/method/upload_file", {
      multipart: {
        file: {
          name: `internal-${uid()}.txt`,
          mimeType: "text/plain",
          buffer: Buffer.from(`internal ${uid()}`),
        },
        is_private: "1",
        doctype: "HD Ticket",
        docname: ticket.name,
      },
    });
    const fileUrl = (await upload.json()).message.file_url;
    await (await apiAs("agent")).call("run_doc_method", {
      dt: "HD Ticket",
      dn: ticket.name,
      method: "new_comment",
      args: { content: "<p>see attached</p>", attachments: [{ file_url: fileUrl }] },
    });

    const customerContext = await loginContext(baseURL!, personas.customer.email, PASSWORD);
    expect((await agentContext.get(fileUrl)).status()).toBe(200);
    expect((await customerContext.get(fileUrl)).status()).toBe(403);
  });

  test("portal ticket creation ignores a spoofed raised_by", async ({ apiAs }) => {
    const ticket = await (await apiAs("customer")).call(
      "helpdesk.helpdesk.doctype.hd_ticket.api.new",
      { doc: { subject: `Spoof ${uid()}`, description: "spoof", raised_by: spoofed } }
    );
    expect(ticket.raised_by).toBe(personas.customer.email);
  });
});

function addComment(api: Api, ticket: string, content: string, raw = false) {
  const args = { dt: "HD Ticket", dn: ticket, method: "new_comment", args: { content } };
  return raw ? api.raw("run_doc_method", args) : api.call("run_doc_method", args);
}

async function expectDenied(pending: Promise<APIResponse>) {
  const response = await pending;
  const body = await response.text();
  expect(response.ok(), body).toBeFalsy();
  expect(body).toMatch(/PermissionError|not permitted|Insufficient Permission/i);
}

async function selectRow(page: Page, api: Api, user: string, ticket: string) {
  await openTicketInList(page, api, user, ticket);
  await page.getByRole("link", { name: new RegExp(`^${ticket} `) }).getByRole("checkbox").check();
}

async function openSelectionMenu(page: Page) {
  await page
    .locator("div")
    .filter({ has: page.getByText(/row selected/) })
    .filter({ has: page.getByRole("button", { name: "Select all" }) })
    .last()
    .getByRole("button")
    .filter({ hasNotText: /\S/ })
    .first()
    .click();
}

async function openSettings(page: Page) {
  await page.getByRole("button", { name: /^Helpdesk / }).click();
  await page.getByRole("menuitem", { name: "Settings" }).click();
}
