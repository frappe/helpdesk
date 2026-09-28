import { expect, test, uid, usePersona } from "../support/fixtures";
import { raiseTicket } from "../support/factories";
import { personas } from "../support/personas";
import {
  addComment,
  comments,
  composer,
  openTicket,
  postComment,
  setHelpdeskSetting,
} from "../support/ticket";

// 1x1 transparent PNG
const PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

usePersona("agent");

test("agent raises a ticket from the new ticket form", async ({ page, api }) => {
  const subject = `Agent raised ${uid()}`;
  await page.goto("/helpdesk/tickets/new");
  await page.getByPlaceholder("A short description").fill(subject);
  await composer(page).click();
  await composer(page).pressSequentially("Printer is on fire");
  await page.getByRole("button", { name: "Submit" }).click();

  await expect(page).toHaveURL(/\/helpdesk\/tickets\/\d+$/);
  await expect(page.getByRole("banner").getByRole("button", { name: subject })).toBeVisible();
  const ticket = await api.get("HD Ticket", page.url().split("/").pop()!);
  expect(ticket.subject).toBe(subject);
  expect(ticket.description).toContain("Printer is on fire");
});

test("email reply with cc and an attachment is sent and stored", async ({ page, api, apiAs }) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  const fileName = `note-${uid()}.txt`;
  await openTicket(page, ticket.name);

  await page.getByRole("button", { name: "Reply", exact: true }).click();
  await page.getByRole("button", { name: "Cc", exact: true }).click();
  await page.getByRole("combobox", { expanded: true }).fill("cc-person@example.com");
  await page.getByRole("option", { name: /cc-person@example.com/ }).click();
  await composer(page).click();
  await composer(page).pressSequentially("We are on it");
  await page.locator("input[type=file]").setInputFiles({
    name: fileName,
    mimeType: "text/plain",
    // unique bytes, or Frappe hands back an older file with the same hash
    buffer: Buffer.from(`attachment ${fileName}`),
  });
  await expect(page.getByText(fileName)).toBeVisible();
  await page.getByRole("button", { name: /^Send/ }).click();

  await expect
    .poll(() =>
      api.list("Communication", {
        fields: ["recipients", "cc", "content"],
        filters: { reference_name: ticket.name, sent_or_received: "Sent" },
      })
    )
    .toEqual([
      expect.objectContaining({
        recipients: personas.customer.email,
        cc: "cc-person@example.com",
        content: expect.stringContaining("We are on it"),
      }),
    ]);
  const [file] = await api.list("File", {
    fields: ["is_private"],
    filters: { attached_to_name: ticket.name, file_name: fileName },
  });
  expect(file.is_private).toBe(1);

  await page.getByRole("tab", { name: "Emails" }).click();
  const emails = page.getByRole("tabpanel", { name: "Emails" });
  await expect(emails.getByText("cc-person@example.com")).toBeVisible();
  await expect(emails.getByRole("button", { name: fileName })).toBeVisible();
});

test("reply editor inserts a table from the slash menu and uploads a pasted image", async ({
  page,
  api,
  apiAs,
}) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  await openTicket(page, ticket.name);
  await page.getByRole("button", { name: "Reply", exact: true }).click();
  const editor = composer(page);

  await editor.click();
  await editor.pressSequentially("/table");
  await page.keyboard.press("Enter");
  await expect(page.getByText("3 × 3")).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(editor.locator("td, th")).toHaveCount(9);
  await editor.locator("td, th").nth(4).click();
  await page.keyboard.type("cell value");

  await editor.evaluate(
    (element, { base64, name }) => {
      const bytes = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0));
      const data = new DataTransfer();
      data.items.add(new File([bytes], name, { type: "image/png" }));
      element.dispatchEvent(
        new ClipboardEvent("paste", { clipboardData: data, bubbles: true, cancelable: true })
      );
    },
    { base64: PNG, name: "pasted.png" }
  );
  await expect(editor.locator(`img[src^="/private/files/"]`)).toHaveCount(1);
  await page.getByRole("button", { name: /^Send/ }).click();

  await expect
    .poll(async () => {
      const [sent] = await api.list("Communication", {
        fields: ["content"],
        filters: { reference_name: ticket.name, sent_or_received: "Sent" },
      });
      return sent?.content || "";
    })
    .toMatch(/<table[\s\S]*cell value[\s\S]*<img[^>]+src="\/private\/files\/[\s\S]*<\/table>/);
});

test("comments post once, edit, delete and survive leaving the ticket", async ({ page, api, apiAs }) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  const rowWith = (text: string) => page.locator(".activity", { hasText: text });
  const first = `First note ${uid()}`;
  await openTicket(page, ticket.name);

  await postComment(page, first);
  await expect(rowWith(first)).toHaveCount(1);
  await expect(rowWith(first).locator("div.uppercase").first()).toHaveText("A");

  // leaving and coming back must not leave a pending copy behind
  await page.getByRole("banner").getByRole("link", { name: "Tickets" }).click();
  await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
  await page.goBack();
  const second = `Second note ${uid()}`;
  await postComment(page, second);
  await expect(rowWith(second)).toHaveCount(1);
  await expect(rowWith(first)).toHaveCount(1);
  await expect(rowWith(second).locator("div.uppercase").first()).toHaveText("A");
  await expect.poll(async () => (await comments(api, ticket.name)).length).toBe(2);

  await rowWith(first).getByRole("button").first().click();
  await page.getByRole("menuitem", { name: "Edit" }).click();
  const edited = `Edited note ${uid()}`;
  await rowWith(first).locator(".ProseMirror").fill(edited);
  await rowWith(edited).getByRole("button", { name: "Save" }).click();
  await expect(rowWith(edited)).toHaveCount(1);
  await expect(rowWith(edited).locator("div.uppercase").first()).toHaveText("A");
  await expect
    .poll(async () => (await comments(api, ticket.name)).map((c) => c.content).join())
    .toContain(edited);

  await rowWith(edited).getByRole("button").first().click();
  await page.getByRole("menuitem", { name: "Delete" }).click();
  await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
  await expect(page.getByText("Comment deleted")).toBeVisible();
  await expect(rowWith(edited)).toHaveCount(0);
  await expect.poll(async () => (await comments(api, ticket.name)).length).toBe(1);
});

test("an @mention notifies the agent and the notification opens the comment", async ({
  page,
  api,
  apiAs,
  pageAs,
}) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  const note = `Need eyes ${uid()}`;
  await openTicket(page, ticket.name);
  await page.getByRole("button", { name: "Comment", exact: true }).click();
  await composer(page).click();
  await composer(page).pressSequentially("@Bel");
  await page.getByRole("button", { name: "Bela E2E" }).click();
  await composer(page).pressSequentially(` ${note}`);
  await page.getByRole("button", { name: /^Comment \(/ }).click();

  await expect
    .poll(() =>
      api.list("Notification Log", {
        filters: { for_user: personas.agent2.email, document_name: ticket.name, type: "Mention" },
      })
    )
    .toHaveLength(1);
  const [comment] = await comments(api, ticket.name);

  const agent2 = await pageAs("agent2");
  await agent2.goto("/helpdesk/home");
  await agent2.getByRole("button", { name: "Notifications" }).click();
  await agent2.getByText(note).click();

  await expect(agent2).toHaveURL(new RegExp(`/helpdesk/tickets/${ticket.name}#activity$`));
  await expect(agent2.locator(`[id="comment:${comment.name}"]`)).toBeInViewport();
});

test.describe("reactions", () => {
  let restore: () => Promise<unknown>;
  test.beforeAll(async ({ api }) => {
    restore = await setHelpdeskSetting(api, "enable_comment_reactions", 1);
  });
  test.afterAll(async () => restore?.());

  test("reactions roll up into one notification for the author", async ({ api, apiAs, pageAs }) => {
    const agentApi = await apiAs("agent");
    const ticket = await raiseTicket(await apiAs("customer"));
    const name = await addComment(agentApi, ticket.name, `React to me ${uid()}`);
    const reactionLogs = () =>
      api.list("Notification Log", {
        fields: ["subject"],
        filters: { for_user: personas.agent.email, type: "Reaction", source_name: name },
      });

    const agent2 = await pageAs("agent2");
    await openTicket(agent2, ticket.name);
    const row = agent2.locator(`[id="comment:${name}"]`);
    await row.getByRole("button").last().click();
    await agent2.getByRole("button", { name: "👍" }).click();
    await expect(row.getByRole("button", { name: "👍 1" })).toBeVisible();

    const manager = await apiAs("manager");
    await manager.call("helpdesk.api.comment.toggle_reaction", { comment: name, emoji: "❤️" });
    await expect.poll(reactionLogs).toEqual([{ subject: "2 people reacted to your comment" }]);

    await row.getByRole("button", { name: "👍 1" }).click();
    await expect.poll(reactionLogs).toEqual([{ subject: "1 person reacted to your comment" }]);
  });
});
