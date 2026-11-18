// Usability task test, workflow A: raise a ticket.
// The customer first submits a value the business rule rejects (FR-A3: the
// subject is mandatory, and a subject of spaces is no subject). The test checks
// that the message says what to correct, then corrects it and checks success.
import { customerDetails, emailOf, expect, newTicketForm, test, ticketIdFromUrl } from "../support/app.mjs";

test("task A: a rejected subject is explained, corrected, and the ticket is raised", async ({ app }) => {
  const subject = app.subject("Usability task A");
  const before = await app.ticketCount();
  const page = await app.pageAs("customerA");

  // open the task screen
  await page.goto("/helpdesk/my-tickets/new");
  const form = newTicketForm(page);
  await expect(form.subject).toBeVisible();

  // 1. a value the rule rejects
  await form.subject.fill("   ");
  await form.description.click();
  await page.keyboard.type("The projector in room 4 does not switch on.");
  await form.submit.click();

  // the error names the field to correct, and nothing was created
  const error = page.getByText("Value missing for HD Ticket: Subject");
  await expect(error).toBeVisible();
  await expect(page).toHaveURL(/\/helpdesk\/my-tickets\/new$/);
  expect(await app.ticketCount()).toBe(before);
  // what the customer already typed is still there, so only the subject needs fixing
  await expect(form.description).toContainText("The projector in room 4 does not switch on.");

  // 2. correct the value
  await form.subject.fill(subject);
  await form.submit.click();

  // the expected confirmation: the new ticket's page, open, under the customer's name
  await expect(page).toHaveURL(/\/helpdesk\/my-tickets\/\d+$/);
  await expect(page.getByRole("banner").getByRole("link", { name: subject })).toBeVisible();
  await expect(customerDetails(page)).toContainText(/Status\s*Open/);

  const stored = await app.stored(ticketIdFromUrl(page));
  expect(stored.subject).toBe(subject);
  expect(stored.raised_by).toBe(emailOf("customerA"));
  expect(await app.ticketCount()).toBe(before + 1);
});
