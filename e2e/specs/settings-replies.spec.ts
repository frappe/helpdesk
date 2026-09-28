import type { Locator, Page } from "@playwright/test";
import { raiseTicket } from "../support/factories";
import { expect, test, uid, usePersona } from "../support/fixtures";
import { personas } from "../support/personas";
import { openSettings } from "../support/settings";

const REPLY = "HD Saved Reply";

usePersona("admin");

let titles: string[];

test.beforeEach(() => {
  titles = [];
});

test.afterEach(async ({ api }) => {
  for (const title of titles) {
    for (const name of [await api.exists(REPLY, { title }), await api.exists(REPLY, { title: `${title} (Copy)` })]) {
      if (name) await api.delete(REPLY, name);
    }
  }
});

test("a new reply takes field placeholders and actions, and refuses an empty action value", async ({ page, api }) => {
  const title = track(`E2E Actions ${uid()}`);
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Saved Replies");
  await dialog.getByRole("button", { name: "New" }).click();
  await dialog.getByRole("textbox", { name: /^Name/ }).fill(title);

  const editor = dialog.locator("[contenteditable=true]");
  await editor.click();
  await page.keyboard.type("About {{subj");
  await expect(page.getByRole("button", { name: "Subject", exact: true })).toBeVisible();
  await page.keyboard.press("Enter");
  await page.keyboard.type("we are on it");
  await expect(editor).toHaveText("About {{ subject }} we are on it");

  await addAction(page, dialog, "Set priority");
  await actionRow(dialog, "Set priority").getByRole("combobox").click();
  await page.getByRole("option", { name: "High", exact: true }).click();
  await addAction(page, dialog, "Assign to me");
  // Only one assignment action is allowed per reply.
  await dialog.getByRole("button", { name: "Add action" }).click();
  await expect(page.getByRole("menuitem", { name: "Assign agent" })).toHaveCount(0);
  await page.getByRole("menuitem", { name: "Add comment" }).click();

  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect(dialog.getByText("Values can't be empty")).toBeVisible();
  expect(await api.exists(REPLY, { title })).toBeFalsy();

  await actionRow(dialog, "Add comment").getByRole("button", { name: "Row actions" }).click();
  await page.getByRole("menuitem", { name: "Delete" }).click();
  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect.poll(() => api.exists(REPLY, { title })).toBeTruthy();

  const saved = await api.get(REPLY, (await api.exists(REPLY, { title }))!);
  expect(saved.message).toContain("{{ subject }}");
  expect(actionsOf(saved)).toEqual([
    { action_type: "Set Priority", value: "High" },
    { action_type: "Assign to Me", value: "" },
  ]);
});

test("clicking a field suggestion inserts its placeholder", async ({ page }) => {
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Saved Replies");
  await dialog.getByRole("button", { name: "New" }).click();
  await dialog.locator("[contenteditable=true]").click();
  await page.keyboard.type("About {{subj");
  await page.getByRole("button", { name: "Subject", exact: true }).click();
  await expect(dialog.locator("[contenteditable=true]")).toHaveText("About {{ subject }} ");
});

test("the preview renders a reply's placeholders against a chosen ticket", async ({ page, api, apiAs }) => {
  const title = track(`E2E Preview ${uid()}`);
  await api.insert(REPLY, { title, message: "<p>Re: {{ subject }}</p>", scope: "Personal" });
  const ticket = await raiseTicket(await apiAs("customer"));

  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Saved Replies");
  await openReply(dialog, title);
  await dialog.getByRole("button", { name: "Preview", exact: true }).first().click();

  const preview = page.getByRole("dialog", { name: "Preview" });
  await preview.getByRole("button", { name: "Select ticket to preview" }).click();
  await page.getByRole("combobox", { name: "Search ticket" }).fill(ticket.subject);
  await page.getByRole("option", { name: new RegExp(ticket.subject) }).click();
  await expect(preview.getByText(`Re: ${ticket.subject}`)).toBeVisible();
});

test("the list searches, filters by scope and duplicates a reply", async ({ page, api }) => {
  const title = track(`E2E Listed ${uid()}`);
  await api.insert(REPLY, { title, message: "<p>Listed</p>", scope: "Global" });

  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Saved Replies");
  // The list opens on Personal replies, so a global one needs the scope filter.
  await dialog.getByPlaceholder("Search").fill(title);
  await expect(dialog.getByText("No saved replies found")).toBeVisible();
  await dialog.getByRole("button", { name: "Personal" }).click();
  await page.getByRole("menuitem", { name: "Global" }).click();
  await expect(replyRow(dialog, title)).toBeVisible();
  await dialog.getByRole("button", { name: "Global" }).click();
  await page.getByRole("menuitem", { name: "All" }).click();
  await expect(replyRow(dialog, title)).toBeVisible();
  await expect(page.getByRole("menu")).toHaveCount(0);

  await replyRow(dialog, title).getByRole("button").last().click();
  await page.getByRole("menuitem", { name: "Duplicate" }).click();
  const duplicate = page.getByRole("dialog", { name: "Duplicate Saved reply" });
  await expect(duplicate.getByRole("textbox")).toHaveValue(`${title} (Copy)`);
  await duplicate.getByRole("button", { name: "Duplicate" }).click();
  await expect.poll(() => api.exists(REPLY, { title: `${title} (Copy)` })).toBeTruthy();
  expect(await api.exists(REPLY, { title })).toBeTruthy();
});

test("a reply is renamed and restricted to a team only once a team is picked", async ({ page, api }) => {
  const title = track(`E2E Scoped ${uid()}`);
  const renamed = track(`${title} Renamed`);
  const team = `E2E Reply Team ${uid()}`;
  await api.insert("HD Team", { team_name: team, users: [{ user: personas.agent.email }] });
  await api.insert(REPLY, { title, message: "<p>Scoped</p>", scope: "Personal" });
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Saved Replies");
    await openReply(dialog, title);
    await dialog.getByRole("textbox", { name: /^Name/ }).fill(renamed);
    await dialog.getByRole("combobox", { name: /^Visibility/ }).click();
    await page.getByRole("option", { name: "Team", exact: true }).click();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect(dialog.getByText("At least one team is required")).toBeVisible();

    await dialog.getByRole("button", { name: "Select teams" }).click();
    await page.getByRole("option", { name: team }).click();
    await page.keyboard.press("Escape");
    await dialog.getByRole("button", { name: "Save", exact: true }).click();

    await expect.poll(() => api.exists(REPLY, { title: renamed })).toBeTruthy();
    const saved = await api.get(REPLY, (await api.exists(REPLY, { title: renamed }))!);
    expect(saved.scope).toBe("Team");
    expect(saved.teams.map((row: { team: string }) => row.team)).toEqual([team]);
  } finally {
    const name = await api.exists(REPLY, { title: renamed });
    if (name) await api.delete(REPLY, name);
    await api.delete("HD Team", team);
  }
});

function track(title: string) {
  titles.push(title);
  return title;
}

async function openReply(dialog: Locator, title: string) {
  await dialog.getByPlaceholder("Search").fill(title);
  await replyRow(dialog, title).getByText(title, { exact: true }).click();
}

function replyRow(dialog: Locator, title: string) {
  return dialog.locator("div.grid-cols-12").filter({ has: dialog.page().getByText(title, { exact: true }) });
}

async function addAction(page: Page, dialog: Locator, label: string) {
  await dialog.getByRole("button", { name: "Add action" }).click();
  await page.getByRole("menuitem", { name: label }).click();
}

function actionRow(dialog: Locator, label: string) {
  return dialog.locator("div.grid.items-start").filter({ has: dialog.page().getByRole("button", { name: label }) });
}

function actionsOf(reply: Record<string, any>) {
  const actions = typeof reply.actions === "string" ? JSON.parse(reply.actions) : reply.actions;
  return actions.map(({ action_type, value }: { action_type: string; value: string }) => ({
    action_type,
    value: value ?? "",
  }));
}
