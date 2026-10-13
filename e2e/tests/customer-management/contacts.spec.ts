import type { Page } from "@playwright/test";
import { expectDenied, type Api } from "../../helpers/api";
import {
  contactUrl,
  createContact,
  createContactWithUser,
  createCustomer,
  pageMenu,
} from "../../helpers/directory";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { pickOption } from "../../helpers/portal";

usePersona("manager");

test("create a contact with an invite, then edit its name and phone", async ({ page, api }) => {
  const email = `e2e-contact-${uid()}@example.com`;
  const dialog = await openNewContact(page);
  await dialog.getByRole("textbox", { name: "First Name" }).fill("Priya");
  await dialog.getByRole("textbox", { name: "Email" }).fill(email);
  await expect(dialog.getByRole("checkbox", { name: "Invite as User" })).toBeChecked();
  await dialog.getByRole("button", { name: "Create" }).click();

  await expect(page).toHaveURL(/\/helpdesk\/contacts\/.+/);
  const contact = await api.exists("Contact", { email_id: email });
  expect(contact).toBeTruthy();
  expect(await api.exists("User Invitation", { email })).toBeTruthy();

  await page.getByRole("button", { name: "Edit" }).click();
  const edit = page.getByRole("dialog");
  await edit.getByRole("textbox", { name: "Last Name" }).fill("Raman");
  await edit.getByRole("button", { name: "Add Phone" }).click();
  await edit.getByRole("textbox").last().fill("9876543210");
  await edit.getByRole("button", { name: "Save" }).click();

  await expect
    .poll(async () => {
      const doc = await api.get("Contact", contact!);
      return [doc.last_name, doc.phone_nos.map((p) => p.phone)];
    })
    .toEqual(["Raman", [expect.stringContaining("9876543210")]]);
});

test("editing a contact makes a newly added email primary", async ({ page, api }) => {
  const contact = await createContact(api, "Emails");
  const second = `e2e-second-${uid()}@example.com`;
  await page.goto(contactUrl(contact.name));

  const dialog = await openEdit(page);
  await dialog.getByRole("button", { name: "Add Email" }).click();
  await dialog.getByPlaceholder("name@example.com").last().fill(second);
  await dialog.getByRole("button", { name: "Set as primary" }).click();
  await dialog.getByRole("button", { name: "Save" }).click();
  await expect(dialog).toHaveCount(0);

  const doc = await api.get("Contact", contact.name);
  expect(doc.email_ids.map((row) => [row.email_id, row.is_primary])).toEqual([
    [contact.email, 0],
    [second, 1],
  ]);
});

test("a contact with a user is linked to a customer from its edit dialog", async ({ page, api }) => {
  const contact = await createContactWithUser(api, "Linked");
  const customer = await createCustomer(api);
  await page.goto(contactUrl(contact.name));

  const dialog = await openEdit(page);
  await pickOption(page, "Select Customer", customer);
  await dialog.getByRole("button", { name: "Save" }).click();
  await expect(dialog).toHaveCount(0);
  const members = (await api.get("HD Customer", customer)).contacts;
  expect(members.map((row) => row.contact_name)).toEqual([contact.name]);

  await page.getByText(customer, { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/helpdesk/customers/${encodeURIComponent(customer)}`));
});

test("a manager edits a contact that has a user", async ({ page, api }) => {
  const contact = await createContactWithUser(api, "Signed");
  await page.goto(contactUrl(contact.name));
  const dialog = await openEdit(page);
  await dialog.getByRole("textbox", { name: "Last Name" }).fill("Up");
  await dialog.getByRole("button", { name: "Save" }).click();
  await expect(dialog).toHaveCount(0);
  expect((await api.get("Contact", contact.name)).last_name).toBe("Up");
});

test("the feedback tab lists a contact's reviews and filters them by rating", async ({ page, api }) => {
  const contact = await createContact(api, "Rater");
  await rate(api, contact, 1, "Loved the quick fix");
  await rate(api, contact, 0.2, "Waited far too long");
  await page.goto(`${contactUrl(contact.name)}#feedback`);

  const loved = page.getByText("Loved the quick fix");
  const waited = page.getByText("Waited far too long");
  await expect(page.getByText("User Reviews")).toBeVisible();
  await expect(loved).toBeVisible();
  await expect(waited).toBeVisible();

  await page.getByRole("radio", { name: "Negative" }).click();
  await expect(loved).toHaveCount(0);
  await expect(waited).toBeVisible();

  await page.getByRole("radio", { name: "Positive" }).click();
  await expect(waited).toHaveCount(0);
  await expect(loved).toBeVisible();
});

test("a contact is invited as a user and the invite resent", async ({ page, api }) => {
  const contact = await createContact(api, "Invitee");
  await page.goto(contactUrl(contact.name));

  await pageMenu(page).click();
  await page.getByRole("menuitem", { name: "Invite as User" }).click();
  await expect(page.getByText("Invitation sent")).toBeVisible();
  await expect(page.getByText("Invited", { exact: true })).toBeVisible();
  expect(await api.exists("User Invitation", { email: contact.email, contact: contact.name })).toBeTruthy();

  await pageMenu(page).click();
  await expect(page.getByRole("menuitem", { name: "Invite as User" })).toHaveCount(0);
  await page.getByRole("menuitem", { name: "Resend Invite" }).click();
  await expect(page.getByText("Invitation email resent successfully")).toBeVisible();
});

test("deleting a contact keeps its tickets and clears their contact", async ({ page, api }) => {
  const contact = await createContact(api, "Leaver");
  const ticket = await api.insert("HD Ticket", { subject: `E2E left ${uid()}`, raised_by: contact.email });
  expect(ticket.contact).toBe(contact.name);
  await page.goto(contactUrl(contact.name));

  await pageMenu(page).click();
  await page.getByRole("menuitem", { name: "Delete" }).click();
  const dialog = page.getByRole("dialog", { name: "Delete" });
  await expect(dialog.getByRole("checkbox", { name: "Delete 1 ticket(s)" })).not.toBeChecked();
  await dialog.getByRole("button", { name: "Delete" }).click();

  await expect(page).toHaveURL(/\/helpdesk\/contacts$/);
  expect(await api.exists("Contact", { name: contact.name })).toBeUndefined();
  expect((await api.get("HD Ticket", ticket.name)).contact).toBeFalsy();
});

test("a contact invited with a customer carries the customer on the invite", async ({ page, api }) => {
  const customer = await createCustomer(api);
  const email = `e2e-invited-${uid()}@example.com`;
  const dialog = await openNewContact(page);
  await dialog.getByRole("textbox", { name: "First Name" }).fill("Noor");
  await dialog.getByRole("textbox", { name: "Email" }).fill(email);
  await dialog.getByRole("button", { name: "Customer", exact: true }).click();
  await pickOption(page, "", customer, { opensItself: true });
  await dialog.getByRole("button", { name: "Create" }).click();

  await expect(page).toHaveURL(/\/helpdesk\/contacts\/.+/);
  const contact = await api.exists("Contact", { email_id: email });
  expect(await api.exists("User Invitation", { email, customer, contact })).toBeTruthy();
});

test.describe("agent", () => {
  usePersona("agent");

  test("an agent reads a contact without the manager actions", async ({ page, api, apiAs }) => {
    const existing = await createContact(api, "Readonly");
    await page.goto(contactUrl(existing.name));
    await expect(page.getByText(existing.email)).toBeVisible();
    await expect(page.getByRole("button", { name: "Edit" })).toHaveCount(0);
    const agent = await apiAs("agent");
    await expectDenied(
      agent.raw("helpdesk.api.contact.edit_contact", { name: existing.name, doc: { first_name: "Changed" } })
    );
    await expectDenied(agent.raw("helpdesk.api.contact.delete_contact", { name: existing.name }));
  });
});

async function openEdit(page: Page) {
  await page.getByRole("button", { name: "Edit" }).click();
  return page.getByRole("dialog");
}

async function openNewContact(page: Page) {
  await page.goto("/helpdesk/contacts");
  await page.getByRole("button", { name: "Create" }).click();
  return page.getByRole("dialog", { name: "Create Contact" });
}

/** A ticket from the contact, rated out of 1. */
async function rate(api: Api, contact: { name: string; email: string }, rating: number, text: string) {
  await api.insert("HD Ticket", {
    subject: `E2E rated ${uid()}`,
    raised_by: contact.email,
    feedback_rating: rating,
    feedback_extra: text,
  });
}
