// UC-04 Resolve and reopen a ticket (actor: Agent, workflow B). Specification: ../USE_CASES.md
import { agentChangeStatus, agentStatusButton, customerDetails, expect, test } from "../support/app.mjs";

test.describe("UC-04 Resolve and reopen a ticket", () => {
  test("MF: agent resolves an open ticket and the customer sees it resolved", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC04 MF"));
    const page = await app.pageAs("agent");
    await page.goto(`/helpdesk/tickets/${name}`);

    await agentChangeStatus(page, "Open", "Resolved");

    // result shown
    await expect(page.getByText("Ticket updated successfully.")).toBeVisible();
    await expect(agentStatusButton(page, "Resolved")).toBeVisible();
    await expect(page.getByText(/changed Status\s*Open\s*→\s*Resolved/)).toBeVisible();

    // postconditions: the shared record, and what the other role now sees
    const stored = await app.stored(name);
    expect(stored.status).toBe("Resolved");
    expect(stored.status_category).toBe("Resolved");
    expect(stored.resolution_date).toBeTruthy();
    const customer = await app.pageAs("customerA");
    await customer.goto(`/helpdesk/my-tickets/${name}`);
    await expect(customerDetails(customer)).toContainText(/Status\s*Resolved/);
  });

  test("AF1: agent marks the ticket as replied, waiting for the customer", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC04 AF1"));
    const page = await app.pageAs("agent");
    await page.goto(`/helpdesk/tickets/${name}`);

    await agentChangeStatus(page, "Open", "Replied");

    await expect(page.getByText("Ticket updated successfully.")).toBeVisible();
    await expect(agentStatusButton(page, "Replied")).toBeVisible();
    const stored = await app.stored(name);
    expect(stored.status).toBe("Replied");
    expect(stored.status_category).toBe("Paused");
    expect(stored.resolution_date ?? null).toBeNull();
  });

  test("AF2: agent reopens a resolved ticket and the resolution date is cleared", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC04 AF2"));
    await app.setStatus(name, "Resolved");
    expect((await app.stored(name)).resolution_date).toBeTruthy();
    const page = await app.pageAs("agent");
    await page.goto(`/helpdesk/tickets/${name}`);

    await agentChangeStatus(page, "Resolved", "Open");

    await expect(page.getByText("Ticket updated successfully.")).toBeVisible();
    await expect(agentStatusButton(page, "Open")).toBeVisible();
    const stored = await app.stored(name);
    expect(stored.status).toBe("Open");
    expect(stored.resolution_date ?? null).toBeNull();
  });

  test("EF1: opening a ticket that does not exist reports that it was not found", async ({ app }) => {
    const before = await app.ticketCount();
    const page = await app.pageAs("agent");

    await page.goto("/helpdesk/tickets/999999");

    await expect(page.getByText("HD Ticket 999999 not found").first()).toBeVisible();
    await expect(page.getByRole("button", { name: /Set Assignee/ })).toHaveCount(0);
    expect(await app.ticketCount()).toBe(before);
  });

  test("EF2: a visitor who is not signed in is sent to the sign-in page", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC04 EF2"));
    const before = await app.stored(name);
    const page = await app.pageAs(null);

    await page.goto(`/helpdesk/tickets/${name}`);

    await expect(page).toHaveURL(/\/login\?redirect-to=/);
    await expect(page.getByRole("heading", { name: "Sign In" })).toBeVisible();
    await expect(page.getByText(before.subject)).toHaveCount(0);
    expect((await app.stored(name)).modified).toBe(before.modified);
  });
});
