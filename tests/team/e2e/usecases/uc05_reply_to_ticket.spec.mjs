// UC-05 Reply to a ticket (actor: Customer, workflow B). Specification: ../USE_CASES.md
import { customerDetails, expect, test } from "../support/app.mjs";

const messageBox = (page) => page.getByText("Type a message");
const send = (page) => page.getByRole("button", { name: "Send", exact: true });

async function writeReply(page, text) {
  await messageBox(page).click();
  await page.locator('[contenteditable="true"]').last().click();
  await page.keyboard.type(text);
}

test.describe("UC-05 Reply to a ticket", () => {
  test("MF: customer answers a ticket that was waiting on them and it reopens", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC05 MF"));
    await app.setStatus(name, "Replied");
    const messagesBefore = await app.messageCount(name);
    const page = await app.pageAs("customerA");
    await page.goto(`/helpdesk/my-tickets/${name}`);
    await expect(customerDetails(page)).toContainText(/Status\s*Awaiting Response/);

    await writeReply(page, "It still jams after a restart.");
    await send(page).click();

    // result shown
    await expect(customerDetails(page)).toContainText(/Status\s*Open/);
    await expect(messageBox(page)).toBeVisible(); // the editor closed again

    // postconditions
    const stored = await app.stored(name);
    expect(stored.status).toBe("Open");
    expect(stored.status_category).toBe("Open");
    expect(await app.messageCount(name)).toBe(messagesBefore + 1);
  });

  test("AF1: customer adds a message to a ticket that is already open", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC05 AF1"));
    const messagesBefore = await app.messageCount(name);
    const page = await app.pageAs("customerA");
    await page.goto(`/helpdesk/my-tickets/${name}`);

    await writeReply(page, "One more detail: it is tray 2 as well.");
    await send(page).click();

    await expect(messageBox(page)).toBeVisible();
    await expect(customerDetails(page)).toContainText(/Status\s*Open/);
    expect((await app.stored(name)).status).toBe("Open");
    expect(await app.messageCount(name)).toBe(messagesBefore + 1);
  });

  test("AF2: customer answers a resolved ticket and it reopens without a resolution date", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC05 AF2"));
    await app.setStatus(name, "Resolved");
    expect((await app.stored(name)).resolution_date).toBeTruthy();
    const page = await app.pageAs("customerA");
    await page.goto(`/helpdesk/my-tickets/${name}`);
    await expect(customerDetails(page)).toContainText(/Status\s*Resolved/);

    await writeReply(page, "The problem is back this morning.");
    await send(page).click();

    await expect(customerDetails(page)).toContainText(/Status\s*Open/);
    const stored = await app.stored(name);
    expect(stored.status).toBe("Open");
    expect(stored.resolution_date ?? null).toBeNull(); // BR3: leaving Resolved clears it
  });

  test("EF1: an empty message cannot be sent", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC05 EF1"));
    await app.setStatus(name, "Replied");
    const messagesBefore = await app.messageCount(name);
    const page = await app.pageAs("customerA");
    await page.goto(`/helpdesk/my-tickets/${name}`);

    await messageBox(page).click();

    await expect(send(page)).toBeVisible();
    await expect(send(page)).toBeDisabled();
    expect((await app.stored(name)).status).toBe("Replied");
    expect(await app.messageCount(name)).toBe(messagesBefore);
  });

  test("EF2: a closed ticket offers no message box", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC05 EF2"));
    await app.setStatus(name, "Closed");
    const before = await app.stored(name);
    const messagesBefore = await app.messageCount(name);
    const page = await app.pageAs("customerA");

    await page.goto(`/helpdesk/my-tickets/${name}`);

    await expect(customerDetails(page)).toContainText(/Status\s*Closed/);
    await expect(messageBox(page)).toHaveCount(0);
    await expect(send(page)).toHaveCount(0);
    const stored = await app.stored(name);
    expect(stored.status).toBe("Closed");
    expect(stored.modified).toBe(before.modified);
    expect(await app.messageCount(name)).toBe(messagesBefore);
  });

  test("EF2 when the status list arrives late: a closed ticket still offers no message box [DEF-35]", async ({ app }) => {
    test.fail(true, "DEF-35: if the ticket loads before the status list, a closed ticket is shown as open");
    const name = await app.newTicket(app.subject("UC05 EF2 late list"));
    await app.setStatus(name, "Closed");
    const page = await app.pageAs("customerA", { responseOrder: "ticket-first" });

    await page.goto(`/helpdesk/my-tickets/${name}`);

    await expect(customerDetails(page)).toContainText(/Status\s*Closed/, { timeout: 5_000 });
    await expect(messageBox(page)).toHaveCount(0);
  });
});
