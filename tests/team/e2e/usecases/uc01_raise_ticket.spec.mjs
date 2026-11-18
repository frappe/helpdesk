// UC-01 Raise a ticket (actor: Customer, workflow A). Specification: ../USE_CASES.md
import { customerDetails, emailOf, expect, newTicketForm, test, ticketIdFromUrl } from "../support/app.mjs";

const TICKET_PAGE = /\/helpdesk\/my-tickets\/\d+$/;

test.describe("UC-01 Raise a ticket", () => {
  test("MF: customer raises a ticket from the ticket list", async ({ app }) => {
    const subject = app.subject("UC01 MF printer jam");
    const page = await app.pageAs("customerA");
    await page.goto("/helpdesk/my-tickets");
    await page.getByRole("link", { name: "Create" }).click();
    const form = newTicketForm(page);

    await form.subject.fill(subject);
    await form.description.click();
    await page.keyboard.type("Paper is stuck in tray 1.");
    await form.submit.click();

    // result shown
    await expect(page).toHaveURL(TICKET_PAGE);
    await expect(page.getByRole("banner").getByRole("link", { name: subject })).toBeVisible();
    await expect(customerDetails(page)).toContainText(/Status\s*Open/);
    await expect(customerDetails(page)).toContainText(/Priority\s*Medium/);
    await expect(page.getByRole("button", { name: "Close", exact: true })).toBeVisible();

    // postconditions
    const stored = await app.stored(ticketIdFromUrl(page));
    expect(stored.subject).toBe(subject);
    expect(stored.status).toBe("Open");
    expect(stored.raised_by).toBe(emailOf("customerA"));
    expect(stored.resolution_date ?? null).toBeNull();
    expect(await app.ticketsWithSubject(subject)).toHaveLength(1);
  });

  test("AF1: customer opens the form by its address and uses the longest allowed subject", async ({ app }) => {
    const subject = app.subject("UC01 AF1").padEnd(140, "x");
    const page = await app.pageAs("customerA");
    await page.goto("/helpdesk/my-tickets/new");
    const form = newTicketForm(page);

    await form.subject.fill(subject);
    await form.description.click();
    await page.keyboard.type("Subject is exactly 140 characters.");
    await form.submit.click();

    await expect(page).toHaveURL(TICKET_PAGE);
    const stored = await app.stored(ticketIdFromUrl(page));
    expect(stored.subject).toBe(subject);
    expect(stored.subject).toHaveLength(140);
  });

  test("AF2: customer discards the first description and writes another", async ({ app }) => {
    const subject = app.subject("UC01 AF2 discard");
    const page = await app.pageAs("customerA");
    await page.goto("/helpdesk/my-tickets/new");
    const form = newTicketForm(page);

    await form.subject.fill(subject);
    await form.description.click();
    await page.keyboard.type("First draft, to be thrown away.");
    await form.discard.click();
    await expect(form.description).toHaveText("");
    await expect(form.submit).toBeDisabled();
    expect(await app.ticketsWithSubject(subject)).toHaveLength(0);

    await form.description.click();
    await page.keyboard.type("Second draft, the one to send.");
    await form.submit.click();

    await expect(page).toHaveURL(TICKET_PAGE);
    await expect(customerDetails(page)).toContainText(/Status\s*Open/);
    const [name] = await app.ticketsWithSubject(subject);
    const stored = await app.stored(name);
    expect(stored.description).toContain("Second draft, the one to send.");
    expect(stored.description).not.toContain("First draft");
    expect(await app.ticketsWithSubject(subject)).toHaveLength(1);
  });

  test("EF1: without a subject the form asks for one and offers nothing to submit", async ({ app }) => {
    const before = await app.ticketCount();
    const page = await app.pageAs("customerA");
    await page.goto("/helpdesk/my-tickets/new");
    const form = newTicketForm(page);

    await expect(form.subject).toHaveValue("");
    await expect(form.prompt).toBeVisible();
    await expect(form.submit).toHaveCount(0);
    await expect(form.discard).toHaveCount(0);

    expect(page.url()).toMatch(/\/helpdesk\/my-tickets\/new$/);
    expect(await app.ticketCount()).toBe(before);
  });

  test("EF2: a subject without a description cannot be submitted", async ({ app }) => {
    const subject = app.subject("UC01 EF2 no description");
    const page = await app.pageAs("customerA");
    await page.goto("/helpdesk/my-tickets/new");
    const form = newTicketForm(page);

    await form.subject.fill(subject);

    await expect(form.submit).toBeVisible();
    await expect(form.submit).toBeDisabled();
    expect(page.url()).toMatch(/\/helpdesk\/my-tickets\/new$/);
    expect(await app.ticketsWithSubject(subject)).toHaveLength(0);
  });

  test("EF3: a subject longer than 140 characters is cut at the limit", async ({ app }) => {
    const tooLong = app.subject("UC01 EF3").padEnd(141, "y");
    const page = await app.pageAs("customerA");
    await page.goto("/helpdesk/my-tickets/new");
    const form = newTicketForm(page);

    await form.subject.pressSequentially(tooLong, { delay: 0 });

    await expect(form.subject).toHaveAttribute("maxlength", "140");
    await expect(form.subject).toHaveValue(tooLong.slice(0, 140));
    expect(await app.ticketsWithSubject(tooLong)).toHaveLength(0);
  });
});
