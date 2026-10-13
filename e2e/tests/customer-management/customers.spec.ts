import type { Page } from "@playwright/test";
import { expectDenied, type Api } from "../../helpers/api";
import {
  createContact,
  createContactWithUser,
  createCustomer,
  customerUrl,
  pageMenu,
} from "../../helpers/directory";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";

usePersona("manager");

test("create a customer with a primary contact, promote a member, list its tickets", async ({
  page,
  api,
}) => {
  const id = uid();
  const name = `E2E Customer ${id}`;
  await page.goto("/helpdesk/customers");
  await page.getByRole("button", { name: "Create" }).click();
  const dialog = page.getByRole("dialog", { name: "Create Customer" });
  await dialog.getByRole("textbox", { name: "Name (required)" }).fill(name);
  await dialog.getByRole("textbox", { name: "First Name", exact: true }).fill("Omar");
  await dialog.getByRole("textbox", { name: "Email", exact: true }).fill(`e2e-primary-${id}@example.com`);
  await dialog.getByRole("button", { name: "Create" }).click();
  await expect(page).toHaveURL(new RegExp(customerUrl(name)));

  const member = await createContact(api, "Member");
  const doc = await api.get("HD Customer", name);
  await api.update("HD Customer", name, {
    contacts: [...doc.contacts, { contact_name: member.name }],
  });
  const subject = `E2E customer ticket ${id}`;
  await api.insert("HD Ticket", { subject, description: subject, raised_by: member.email, customer: name });

  await page.reload();
  await expect(page.getByText(subject)).toBeVisible();
  await page.getByRole("tab", { name: /Contacts/ }).click();
  await openCardMenu(page, member.name);
  await page.getByRole("menuitem", { name: "Role" }).hover();
  await page.getByRole("menuitem", { name: "Customer Manager" }).click();
  await confirm(page);

  await expect.poll(async () => (await memberRow(api, name, member.name))?.is_manager).toBe(1);
});

test("a manager edits a customer's domain, then renames it", async ({ page, api }) => {
  const name = await createCustomer(api);
  const renamed = `${name} Renamed`;
  await page.goto(customerUrl(name));

  await page.getByRole("button", { name: "Edit" }).click();
  await page.getByRole("dialog").getByRole("textbox", { name: "Domain" }).fill("e2e.example.com");
  await page.getByRole("dialog").getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("e2e.example.com")).toBeVisible();
  expect((await api.get("HD Customer", name)).domain).toBe("e2e.example.com");

  await page.getByRole("button", { name: "Edit" }).click();
  await page.getByRole("dialog").getByRole("textbox", { name: /^Name/ }).fill(renamed);
  await page.getByRole("dialog").getByRole("button", { name: "Save" }).click();
  await expect(page).toHaveURL(new RegExp(customerUrl(renamed)));
  expect(await api.exists("HD Customer", { name: renamed })).toBe(renamed);
  expect(await api.exists("HD Customer", { name })).toBeUndefined();
});

test("inviting adds an existing user at once and keeps a new email pending until revoked", async ({
  page,
  api,
}) => {
  const existing = await createContactWithUser(api, "Uma");
  const newcomer = `e2e-newcomer-${uid()}@example.com`;
  const name = await createCustomer(api);

  await page.goto(`${customerUrl(name)}#contacts`);
  await page.getByRole("button", { name: "Invite" }).click();
  const dialog = page.getByRole("dialog", { name: "Invite Contact" });
  const input = dialog.getByPlaceholder("Enter email address");
  for (const email of [existing.email, newcomer]) {
    await input.fill(email);
    await input.press("Enter");
  }
  // Escape closes the open suggestions without blurring, so the picker's delayed refocus can't reopen them
  await input.press("Escape");
  await expect(page.getByRole("listbox")).toHaveCount(0);
  await dialog.getByRole("button", { name: "Invite", exact: true }).click();

  await expect(card(page, existing.name)).toBeVisible();
  expect(await memberRow(api, name, existing.name)).toBeTruthy();
  const pending = dialog.locator("div.justify-between").filter({ hasText: newcomer });
  await expect(pending).toBeVisible();
  expect(await invitationStatus(api, newcomer)).toBe("Pending");

  await pending.getByRole("button").click();
  await pending.getByRole("button", { name: "Confirm" }).click();
  await expect(pending).toHaveCount(0);
  expect(await invitationStatus(api, newcomer)).toBe("Cancelled");
});

test("contact cards set the primary contact, revoke manager access and remove a contact", async ({
  page,
  api,
}) => {
  const lead = await createContact(api, "Lead");
  const deputy = await createContact(api, "Deputy");
  const name = await createCustomer(api, [{ name: lead.name, isManager: true }, { name: deputy.name }]);
  await page.goto(`${customerUrl(name)}#contacts`);

  await openCardMenu(page, deputy.name);
  await page.getByRole("menuitem", { name: "Set as Primary" }).click();
  await confirm(page);
  await expect(card(page, deputy.name).getByLabel("Primary")).toBeVisible();
  expect((await api.get("HD Customer", name)).primary_contact).toBe(deputy.name);

  await openCardMenu(page, lead.name);
  await page.getByRole("menuitem", { name: "Role" }).hover();
  await page.getByRole("menuitem", { name: "Customer", exact: true }).click();
  await confirm(page);
  await expect.poll(async () => (await memberRow(api, name, lead.name))?.is_manager).toBe(0);

  await openCardMenu(page, lead.name);
  await page.getByRole("menuitem", { name: "Remove Contact" }).click();
  await confirm(page);
  await expect(card(page, lead.name)).toHaveCount(0);
  expect(await memberRow(api, name, lead.name)).toBeUndefined();
});

test("deleting a customer keeps its tickets and clears their customer", async ({ page, api }) => {
  const member = await createContact(api, "Keeper");
  const name = await createCustomer(api, [{ name: member.name }]);
  const ticket = await api.insert("HD Ticket", {
    subject: `E2E kept ${uid()}`,
    raised_by: member.email,
    customer: name,
  });
  await page.goto(customerUrl(name));

  await pageMenu(page).click();
  await page.getByRole("menuitem", { name: "Delete" }).click();
  const dialog = page.getByRole("dialog", { name: "Delete Customer" });
  await expect(dialog.getByRole("checkbox", { name: "Delete 1 ticket(s)" })).not.toBeChecked();
  await dialog.getByRole("button", { name: "Delete" }).click();

  await expect(page).toHaveURL(/\/helpdesk\/customers$/);
  expect(await api.exists("HD Customer", { name })).toBeUndefined();
  expect((await api.get("HD Ticket", ticket.name)).customer).toBeFalsy();
});

test.describe("agent", () => {
  usePersona("agent");

  test("an agent reads customers but gets none of the manager actions", async ({ page, api, apiAs }) => {
    const member = await createContact(api, "Viewer");
    const name = await createCustomer(api, [{ name: member.name }]);

    await page.goto(`${customerUrl(name)}#contacts`);
    await expect(card(page, member.name)).toBeVisible();
    await expect(page.getByRole("button", { name: "Edit" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Invite" })).toHaveCount(0);
    await expect(card(page, member.name).getByRole("button")).toHaveCount(0);

    const agent = await apiAs("agent");
    await expectDenied(
      agent.raw("frappe.client.set_value", { doctype: "HD Customer", name, fieldname: "domain", value: "x.io" })
    );
    await expectDenied(agent.raw("helpdesk.api.customer.create_customer", { customer: { customer_name: `${name} 2` } }));
  });
});

function card(page: Page, contact: string) {
  return page.locator("div.rounded-5").filter({ hasText: contact });
}

async function openCardMenu(page: Page, contact: string) {
  await card(page, contact).getByRole("button").click();
}

function confirm(page: Page) {
  return page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();
}

async function memberRow(api: Api, customer: string, contact: string) {
  const doc = await api.get("HD Customer", customer);
  return doc.contacts.find((row: { contact_name: string }) => row.contact_name === contact);
}

async function invitationStatus(api: Api, email: string) {
  const [invite] = await api.list("User Invitation", { fields: ["status"], filters: { email } });
  return invite?.status;
}
