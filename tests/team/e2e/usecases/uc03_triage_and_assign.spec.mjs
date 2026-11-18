// UC-03 Triage and assign a ticket (actor: Agent, workflow B). Specification: ../USE_CASES.md
import { chooseOption, emailOf, expect, test } from "../support/app.mjs";

test.describe("UC-03 Triage and assign a ticket", () => {
  test("MF: agent opens a ticket from the list and assigns it to themself", async ({ app }) => {
    const subject = app.subject("UC03 MF");
    const name = await app.newTicket(subject);
    const page = await app.pageAs("agent");
    await page.goto("/helpdesk/tickets");
    await page.getByText(subject, { exact: true }).click();
    await expect(page).toHaveURL(new RegExp(`/helpdesk/tickets/${name}$`));

    await page.getByRole("button", { name: /Set Assignee/ }).click();
    await page.getByRole("dialog").getByRole("button", { name: /Asha Agent/ }).click();
    await page.keyboard.press("Escape");

    // result shown
    await expect(page.getByText("Assignees updated successfully.")).toBeVisible();
    await expect(page.getByRole("button", { name: /Asha Agent/ }).last()).toBeVisible();
    await expect(page.getByRole("button", { name: /Set Assignee/ })).toHaveCount(0);

    // postconditions
    expect(await app.assignees(name)).toEqual([emailOf("agent")]);
    expect((await app.stored(name)).status).toBe("Open");
  });

  test("AF1: agent raises the priority", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC03 AF1"));
    const page = await app.pageAs("agent");
    await page.goto(`/helpdesk/tickets/${name}`);

    await chooseOption(page, /Priority/, "High");

    await expect(page.getByText("Ticket updated successfully.")).toBeVisible();
    await expect(page.getByRole("combobox", { name: /Priority/ })).toHaveValue("High");
    expect((await app.stored(name)).priority).toBe("High");
  });

  test("AF2: agent classifies the ticket by type", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC03 AF2"));
    const page = await app.pageAs("agent");
    await page.goto(`/helpdesk/tickets/${name}`);

    await chooseOption(page, /Ticket Type/, "Bug");

    await expect(page.getByText("Ticket updated successfully.")).toBeVisible();
    await expect(page.getByRole("combobox", { name: /Ticket Type/ })).toHaveValue("Bug");
    expect((await app.stored(name)).ticket_type).toBe("Bug");
  });

  test("EF1: another customer who opens the ticket is refused and sent to their own list", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC03 EF1"));
    const before = await app.stored(name);
    const page = await app.pageAs("customerB");

    await page.goto(`/helpdesk/my-tickets/${name}`);

    await expect(page.getByText("Not allowed via controller permission check").first()).toBeVisible();
    await expect(page).toHaveURL(/\/helpdesk\/my-tickets$/);
    await expect(page.getByText(before.subject)).toHaveCount(0);

    expect((await app.stored(name)).modified).toBe(before.modified);
    expect(await app.assignees(name)).toEqual([]);
  });

  test("EF2: a customer who opens the agent's ticket screen gets no agent controls", async ({ app }) => {
    const name = await app.newTicket(app.subject("UC03 EF2"));
    const before = await app.stored(name);
    const page = await app.pageAs("customerA");

    await page.goto(`/helpdesk/tickets/${name}`);
    await page.waitForLoadState("networkidle");

    await expect(page).not.toHaveURL(new RegExp(`/helpdesk/tickets/${name}$`));
    await expect(page.getByRole("button", { name: /Set Assignee/ })).toHaveCount(0);
    await expect(page.getByRole("combobox", { name: /Priority/ })).toHaveCount(0);

    expect((await app.stored(name)).modified).toBe(before.modified);
    expect(await app.assignees(name)).toEqual([]);
  });
});
