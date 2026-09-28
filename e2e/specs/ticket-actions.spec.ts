import type { Page } from "@playwright/test";
import type { Api } from "../support/api";
import { expect, test, uid, usePersona } from "../support/fixtures";
import { raiseTicket } from "../support/factories";
import { addComment, openTicket, runTicketMethod } from "../support/ticket";

usePersona("agent");

const communications = (api: Api, ticket: string) =>
  api.list("Communication", {
    fields: ["name", "content"],
    filters: { reference_doctype: "HD Ticket", reference_name: ticket },
  });

/** Merge `source` into `target` through the ticket's More menu. */
async function mergeFromUi(page: Page, source: { name: string }, target: { name: string; subject: string }) {
  await openTicket(page, source.name);
  await page.getByRole("banner").getByRole("button").last().click();
  await page.getByRole("menuitem", { name: "Merge Ticket" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "Ticket", exact: true }).click();
  await page.getByRole("combobox", { name: "Select Ticket" }).fill(target.subject);
  await page.getByRole("option", { name: `${target.subject} ${target.name},` }).click();
  const opened = page.context().waitForEvent("page");
  await dialog.getByRole("button", { name: `Merge with ticket #${target.name}` }).click();
  await expect(page.getByText("Ticket merged successfully.")).toBeVisible();
  return opened;
}

test("a ticket merges into another from the same customer", async ({ page, api, apiAs }) => {
  const customer = await apiAs("customer");
  const target = await raiseTicket(customer);
  const source = await raiseTicket(customer);

  const opened = await mergeFromUi(page, source, target);
  expect((await opened).url()).toContain(`/helpdesk/tickets/${target.name}`);
  expect(await api.get("HD Ticket", source.name)).toMatchObject({
    is_merged: 1,
    merged_with: target.name,
    status: "Closed",
  });
});

test("merging carries the source emails over to the target", async ({ page, api, apiAs }) => {
  const customer = await apiAs("customer");
  const target = await raiseTicket(customer);
  const source = await raiseTicket(customer);

  await mergeFromUi(page, source, target);
  const moved = (await communications(api, target.name)).map((c) => c.content).join();
  expect(moved).toContain(`${source.subject} description`);
});

test("a later email splits off into a new ticket", async ({ page, api, apiAs }) => {
  const customer = await apiAs("customer");
  const ticket = await raiseTicket(customer);
  await runTicketMethod(customer, ticket.name, "create_communication_via_contact", {
    message: "<p>Also, a separate problem</p>",
  });
  const followUp = (await communications(api, ticket.name)).find((c) =>
    c.content.includes("separate problem")
  )!;
  const subject = `Split off ${uid()}`;
  await openTicket(page, ticket.name);

  const row = page.locator(`[id="email:${followUp.name}"]`);
  await row.getByRole("button").last().click();
  await page.getByRole("menuitem", { name: "Split Ticket" }).click();
  const dialog = page.getByRole("dialog", { name: "Split ticket" });
  await dialog.getByPlaceholder("Add a subject for the new ticket").fill(subject);
  await dialog.getByRole("button", { name: "Split into new ticket" }).click();

  await expect.poll(() => api.exists("HD Ticket", { subject })).toBeTruthy();
  const split = await api.exists("HD Ticket", { subject });
  expect((await communications(api, split!)).map((c) => c.name)).toEqual([followUp.name]);
  expect((await communications(api, ticket.name)).map((c) => c.name)).not.toContain(followUp.name);
});

test("next and previous ticket show that ticket's own timeline", async ({ api, apiAs, pageAs }) => {
  const page = await pageAs("agent2");
  const agent = await apiAs("agent");
  const customer = await apiAs("customer");
  const notes = new Map<string, string>();
  for (const ticket of [await raiseTicket(customer), await raiseTicket(customer)]) {
    notes.set(ticket.name, `Timeline of ${ticket.name} ${uid()}`);
    await addComment(agent, ticket.name, notes.get(ticket.name)!);
  }
  // the newest ticket heads the default view, so it has a next one
  const start = [...notes.keys()].at(-1)!;
  const feed = page.getByRole("tabpanel", { name: "Activity" });
  await openTicket(page, start);
  await expect(feed.getByText(notes.get(start)!)).toBeVisible();

  const runCommand = async (title: string) => {
    // Desktop Chrome's user agent is Windows, where Mod is Control
    await page.keyboard.press("Control+k");
    await page.getByRole("combobox", { name: /Search commands/ }).fill(title);
    await page.getByRole("option", { name: new RegExp(`^${title}`) }).click();
  };
  await runCommand("Next ticket");
  await expect(page).not.toHaveURL(new RegExp(`/tickets/${start}$`));
  const next = page.url().split("/").pop()!;
  const nextComments = await api.list("Comment", {
    fields: ["content"],
    filters: { reference_name: next, comment_type: "Comment" },
  });
  for (const comment of nextComments) {
    await expect(feed.getByText(comment.content.replace(/<[^>]+>/g, ""))).toBeVisible();
  }
  await expect(feed.getByText(notes.get(start)!)).toHaveCount(0);

  await runCommand("Previous ticket");
  await expect(page).toHaveURL(new RegExp(`/tickets/${start}$`));
  await expect(feed.getByText(notes.get(start)!)).toBeVisible();
  if (!notes.has(next)) return;
  await expect(feed.getByText(notes.get(next)!)).toHaveCount(0);
});

test("activity, emails, comments and analytics tabs render", async ({ page, apiAs }) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  const note = `Tab note ${uid()}`;
  await addComment(await apiAs("agent"), ticket.name, note);
  await openTicket(page, ticket.name);

  await page.getByRole("tab", { name: "Emails" }).click();
  await expect(page).toHaveURL(/#email$/);
  const emails = page.getByRole("tabpanel", { name: "Emails" });
  await expect(emails.getByText("Cora E2E")).toBeVisible();
  await expect(emails.getByText(note)).toHaveCount(0);

  await page.getByRole("tab", { name: "Comments" }).click();
  await expect(page).toHaveURL(/#comment$/);
  await expect(page.getByRole("tabpanel", { name: "Comments" }).getByText(note)).toBeVisible();

  await page.getByRole("tab", { name: "Analytics" }).click();
  const analytics = page.getByRole("tabpanel", { name: "Analytics" });
  await expect(analytics.getByRole("heading", { name: "Ticket Timeline" })).toBeVisible();
  await expect(analytics.getByRole("heading", { name: "Conversation Summary" })).toBeVisible();

  await page.getByRole("tab", { name: "Activity" }).click();
  await expect(page.getByRole("tabpanel", { name: "Activity" }).getByText(note)).toBeVisible();
});

test.describe("deleting", () => {
  test("agents are not offered delete", async ({ page, apiAs }) => {
    const ticket = await raiseTicket(await apiAs("customer"));
    await openTicket(page, ticket.name);
    await page.getByRole("banner").getByRole("button").last().click();
    await expect(page.getByRole("menuitem", { name: "Merge Ticket" })).toBeVisible();
    await expect(page.getByRole("menuitem", { name: "Delete" })).toHaveCount(0);
  });

  test("an admin deletes a ticket", async ({ api, apiAs, pageAs }) => {
    const ticket = await raiseTicket(await apiAs("customer"));
    const admin = await pageAs("admin");
    await openTicket(admin, ticket.name);
    await admin.getByRole("banner").getByRole("button").last().click();
    await admin.getByRole("menuitem", { name: "Delete" }).click();
    await admin.getByRole("dialog").getByRole("button", { name: "Delete" }).click();

    await expect(admin.getByText("Ticket deleted successfully.")).toBeVisible();
    await expect(admin).toHaveURL(/\/helpdesk\/tickets$/);
    expect(await api.exists("HD Ticket", { name: ticket.name })).toBeUndefined();
  });
});
