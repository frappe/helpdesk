// UC-02 Close and rate a ticket (actor: Customer, workflow B). Specification: ../USE_CASES.md
import { customerDetails, expect, test } from "../support/app.mjs";

const ratingDialog = (page) => page.getByRole("dialog", { name: "Rate this ticket" });

async function openRatingDialog(app, subject) {
  const name = await app.resolvedTicketWithReply(subject);
  const before = await app.stored(name);
  const page = await app.pageAs("customerA");
  await page.goto(`/helpdesk/my-tickets/${name}`);
  await expect(customerDetails(page)).toContainText(/Status\s*Resolved/);
  await page.getByRole("button", { name: "Close", exact: true }).click();
  await expect(ratingDialog(page)).toBeVisible();
  return { name, before, page, dialog: ratingDialog(page) };
}

test.describe("UC-02 Close and rate a ticket", () => {
  test("MF: customer rates a resolved ticket and closes it", async ({ app }) => {
    const { name, before, page, dialog } = await openRatingDialog(app, app.subject("UC02 MF"));

    await dialog.getByRole("radio", { name: "4 of 5" }).click();
    await dialog.getByRole("button", { name: "Prompt, informative support" }).click();
    await dialog.getByRole("button", { name: "Submit" }).click();

    // result shown
    await expect(dialog).toBeHidden();
    await expect(customerDetails(page)).toContainText(/Status\s*Closed/);
    await expect(customerDetails(page)).toContainText("Prompt, informative support");
    await expect(page.getByRole("button", { name: "Close", exact: true })).toHaveCount(0);

    // postconditions
    const stored = await app.stored(name);
    expect(stored.status).toBe("Closed");
    expect(stored.feedback).toBe("Prompt, informative support");
    expect(stored.feedback_rating).toBe(0.8);
    expect(stored.resolution_date).toBe(before.resolution_date); // closing keeps the resolution date
  });

  test("AF1: customer closes a ticket no agent has answered, without rating", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC02 AF1"));
    const page = await app.pageAs("customerA");
    await page.goto(`/helpdesk/my-tickets/${name}`);

    await page.getByRole("button", { name: "Close", exact: true }).click();
    const confirm = page.getByRole("dialog", { name: "Close Ticket" });
    await expect(confirm).toBeVisible();
    await confirm.getByRole("button", { name: "Confirm" }).click();

    await expect(page.getByText("Ticket closed successfully.")).toBeVisible();
    await expect(customerDetails(page)).toContainText(/Status\s*Closed/);

    const stored = await app.stored(name);
    expect(stored.status).toBe("Closed");
    expect(stored.resolution_date).toBeTruthy();
    expect(stored.feedback ?? null).toBeNull();
  });

  test("AF2: customer adds a written comment to the rating", async ({ app }) => {
    const { name, page, dialog } = await openRatingDialog(app, app.subject("UC02 AF2"));

    await dialog.getByRole("radio", { name: "5 of 5" }).click();
    await dialog.getByRole("button").filter({ hasText: /help|experience/i }).first().click();
    await dialog.getByRole("textbox", { name: "Tell us more" }).fill("Fixed in one visit, thank you.");
    await dialog.getByRole("button", { name: "Submit" }).click();

    await expect(dialog).toBeHidden();
    await expect(customerDetails(page)).toContainText(/Status\s*Closed/);

    const stored = await app.stored(name);
    expect(stored.status).toBe("Closed");
    expect(stored.feedback_rating).toBe(1);
    expect(stored.feedback_extra).toBe("Fixed in one visit, thank you.");
  });

  test("EF1: the rating cannot be submitted until a rating and a reason are chosen", async ({ app }) => {
    const { name, dialog } = await openRatingDialog(app, app.subject("UC02 EF1"));
    const submit = dialog.getByRole("button", { name: "Submit" });

    await expect(dialog.getByText("Select a rating")).toBeVisible();
    await expect(submit).toBeDisabled();

    await dialog.getByRole("radio", { name: "2 of 5" }).click();
    await expect(dialog.getByText("Pick an option")).toBeVisible();
    await expect(submit).toBeDisabled();

    const stored = await app.stored(name);
    expect(stored.status).toBe("Resolved");
    expect(stored.feedback ?? null).toBeNull();
  });

  test("EF2: customer dismisses the rating dialog and the ticket stays resolved", async ({ app }) => {
    const { name, before, page, dialog } = await openRatingDialog(app, app.subject("UC02 EF2"));

    await dialog.getByRole("radio", { name: "3 of 5" }).click();
    await dialog.getByRole("button", { name: "Close" }).click();

    await expect(dialog).toBeHidden();
    await expect(customerDetails(page)).toContainText(/Status\s*Resolved/);
    await expect(page.getByRole("button", { name: "Close", exact: true })).toBeVisible();

    const stored = await app.stored(name);
    expect(stored.status).toBe("Resolved");
    expect(stored.feedback ?? null).toBeNull();
    expect(stored.resolution_date).toBe(before.resolution_date);
  });

  test("EF3: a closed ticket offers the customer no way to close or change it", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC02 EF3"));
    await app.setStatus(name, "Closed");
    const before = await app.stored(name);
    const page = await app.pageAs("customerA");

    await page.goto(`/helpdesk/my-tickets/${name}`);

    await expect(customerDetails(page)).toContainText(/Status\s*Closed/);
    await expect(page.getByRole("button", { name: "Close", exact: true })).toHaveCount(0);

    const stored = await app.stored(name);
    expect(stored.status).toBe("Closed");
    expect(stored.modified).toBe(before.modified);
  });
});
