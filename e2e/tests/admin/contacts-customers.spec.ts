import { expect, test, uid, usePersona } from "../../helpers/fixtures";

usePersona("manager");

test("create a contact with an invite, then edit its name and phone", async ({
  page,
  api,
}) => {
  const id = uid();
  const email = `e2e-contact-${id}@example.com`;

  await page.goto("/helpdesk/contacts");
  await page.getByRole("button", { name: "Create" }).click();
  const dialog = page.getByRole("dialog", { name: "Create Contact" });
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
  await expect(page).toHaveURL(new RegExp(`/helpdesk/customers/${encodeURIComponent(name)}`));

  const member = await api.insert("Contact", {
    first_name: `Member ${id}`,
    email_ids: [{ email_id: `e2e-member-${id}@example.com`, is_primary: 1 }],
  });
  const doc = await api.get("HD Customer", name);
  await api.update("HD Customer", name, {
    contacts: [...doc.contacts, { contact_name: member.name }],
  });
  const subject = `E2E customer ticket ${id}`;
  await api.insert("HD Ticket", {
    subject,
    description: subject,
    raised_by: `e2e-member-${id}@example.com`,
    customer: name,
  });

  await page.reload();
  await expect(page.getByText(subject)).toBeVisible();
  await page.getByRole("tab", { name: /Contacts/ }).click();
  const card = page.locator("div.rounded-5").filter({ hasText: member.name });
  await card.getByRole("button").click();
  await page.getByRole("menuitem", { name: "Role" }).hover();
  await page.getByRole("menuitem", { name: "Customer Manager" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();

  await expect
    .poll(async () => {
      const customer = await api.get("HD Customer", name);
      return customer.contacts.find((c) => c.contact_name === member.name)?.is_manager;
    })
    .toBe(1);
});
