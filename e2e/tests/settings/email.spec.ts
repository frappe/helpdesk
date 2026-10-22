import type { Locator, Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { PASSWORD } from "../../helpers/personas";
import { createThrowawayAgent, openSettings, snapshotSettings } from "../../helpers/settings";

const ACCOUNT = "Email Account";

usePersona("admin");

test("a new custom account goes back to the tiles from its form, submits with Enter, needs its servers, and one it cannot reach is not saved", async ({ page, api }) => {
  const name = `E2E Add ${uid()}`;
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Email Accounts");
  await dialog.getByRole("button", { name: "New", exact: true }).click();
  const create = dialog.getByRole("button", { name: "Create" });

  const custom = dialog.getByRole("button", { name: "Custom email", exact: true });
  const back = dialog.getByRole("button", { name: "Back: New custom email account" });
  await custom.click();
  await expect(back).toBeFocused();
  await back.click();
  await expect(custom).toBeFocused();
  await custom.click();
  await dialog.getByRole("textbox", { name: "Account name" }).fill(name);
  await dialog.getByRole("textbox", { name: "Email address" }).fill(`e2e-add-${uid()}@example.com`);
  await dialog.getByLabel("Password").fill("secret");
  await dialog.getByRole("textbox", { name: "Account name" }).press("Enter");
  await expect(dialog.getByRole("alert")).toHaveText("Pick an email domain or enter the server settings");
  await expect(dialog.getByRole("combobox", { name: "Email domain" })).toBeFocused();

  await dialog.getByRole("textbox", { name: "Incoming server (IMAP)" }).fill("imap.e2e.invalid");
  await dialog.getByRole("spinbutton", { name: "Incoming port" }).fill("993");
  await dialog.getByRole("textbox", { name: "Outgoing server (SMTP)" }).fill("smtp.e2e.invalid");
  await dialog.getByRole("spinbutton", { name: "Outgoing port" }).fill("587");
  await create.click();
  await expect(dialog.getByRole("alert")).toBeVisible();
  expect(await api.exists(ACCOUNT, { email_account_name: name })).toBeFalsy();

  await back.click();
  await confirmUnsaved(page);
  await dialog.getByRole("button", { name: "Back: New email account" }).click();
  await expect(dialog.getByRole("heading", { name: "Email accounts" })).toBeVisible();
});

test("going back from a typed new account form asks first, and confirming starts the next form blank", async ({ page }) => {
  const name = `E2E Draft ${uid()}`;
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Email Accounts");
  await dialog.getByRole("button", { name: "New", exact: true }).click();
  const gmail = dialog.getByRole("button", { name: "Gmail", exact: true });
  const back = dialog.getByRole("button", { name: "Back: New Gmail account" });
  const accountName = dialog.getByRole("textbox", { name: "Account name" });
  const confirm = unsavedDialog(page);
  await gmail.click();
  await accountName.fill(name);

  await back.click();
  await expect(confirm).toContainText("Are you sure you want to go back? Unsaved changes will be lost.");
  await confirm.getByRole("button", { name: "Cancel" }).click();
  await expect(confirm).toBeHidden();
  await expect(back).toBeFocused();
  await expect(accountName).toHaveValue(name);

  await back.click();
  await page.keyboard.press("Escape");
  await expect(confirm).toBeHidden();
  await expect(back).toBeFocused();
  await expect(accountName).toHaveValue(name);

  await back.click();
  await confirmUnsaved(page);
  await expect(gmail).toBeFocused();
  await expect(dialog.getByText("Unsaved", { exact: true })).toBeHidden();
  await gmail.click();
  await expect(accountName).toHaveValue("");
});

test("an unsaved new account keeps Settings open, and switching to another screen asks first", async ({ page }) => {
  const name = `E2E Leave ${uid()}`;
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Email Accounts");
  await dialog.getByRole("button", { name: "New", exact: true }).click();
  await dialog.getByRole("button", { name: "Gmail", exact: true }).click();
  const accountName = dialog.getByRole("textbox", { name: "Account name" });
  await accountName.fill(name);

  await page.keyboard.press("Escape");
  await page.mouse.click(10, 10);
  await expect(accountName).toHaveValue(name);

  const teams = dialog.getByRole("button", { name: "Teams", exact: true });
  // SettingsModal's always-mounted confirm stays under the aria-hidden that opening Settings set.
  const confirm = page.getByRole("dialog", { name: "Unsaved changes", includeHidden: true });
  await teams.click();
  await expect(confirm).toContainText("Are you sure you want to change tabs? Unsaved changes will be lost.");
  await page.keyboard.press("Escape");
  await expect(confirm).toBeHidden();
  await expect(accountName).toHaveValue(name);

  await dialog.getByRole("button", { name: "Email Accounts", exact: true }).click();
  await expect(confirm).toBeHidden();
  await expect(accountName).toHaveValue(name);

  await teams.click();
  await confirm.getByRole("button", { name: "Confirm", includeHidden: true }).click();
  await expect(confirm).toBeHidden();
  await expect(dialog.getByRole("heading", { name: "Teams" })).toBeVisible();
  await dialog.getByRole("button", { name: "Email Accounts", exact: true }).click();
  await expect(dialog.getByRole("heading", { name: "Email accounts" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
});

test("an email account is edited and renamed, keeps sending off when the server rejects it, and going back with unsaved edits asks first", async ({ page, api }) => {
  const name = `E2E Edit ${uid()}`;
  const renamed = `${name} Renamed`;
  await api.insert(ACCOUNT, {
    email_account_name: name,
    email_id: `e2e-edit-${uid()}@example.com`,
    email_server: "imap.e2e.invalid",
    smtp_server: "smtp.e2e.invalid",
    incoming_port: "993",
    smtp_port: "587",
    enable_incoming: 0,
    enable_outgoing: 0,
  });
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Email Accounts");
    await expect(accountRow(dialog, name).getByText("Disabled", { exact: true })).toBeVisible();
    await accountRow(dialog, name).click();

    const save = dialog.getByRole("button", { name: "Save", exact: true });
    await expect(save).toBeDisabled();
    await dialog.getByRole("spinbutton", { name: "Outgoing port" }).fill("2525");
    await save.click();
    await expect.poll(async () => (await api.get(ACCOUNT, name)).smtp_port).toBe("2525");

    await accountRow(dialog, name).click();
    await dialog.getByRole("textbox", { name: "Account name" }).fill(renamed);
    await save.click();
    await expect.poll(() => api.exists(ACCOUNT, { name: renamed })).toBeTruthy();
    await expect(accountRow(dialog, renamed)).toBeFocused();

    await accountRow(dialog, renamed).click();
    await dialog.getByRole("switch", { name: "Send email" }).click();
    await save.click();
    await expect(dialog.getByRole("alert")).toBeVisible();
    await expect.poll(async () => (await api.get(ACCOUNT, renamed)).enable_outgoing).toBe(0);

    await dialog.getByRole("button", { name: `Back: ${renamed}` }).click();
    await confirmUnsaved(page);
    await expect(accountRow(dialog, renamed)).toBeFocused();
    await accountRow(dialog, renamed).click();
    await expect(dialog.getByRole("switch", { name: "Send email" })).not.toBeChecked();
  } finally {
    for (const account of [name, renamed]) {
      if (await api.exists(ACCOUNT, { name: account })) await api.delete(ACCOUNT, account);
    }
  }
});

test("the default outgoing account is picked once for the whole list, and a change says so", async ({ page, api }) => {
  const seeded = (await api.list(ACCOUNT, { filters: { default_outgoing: 1 }, fields: ["name"] }))[0]?.name;
  expect(seeded).toBeTruthy();
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Email Accounts");
    await expect(accountRow(dialog, seeded).getByText("Outgoing only", { exact: true })).toBeVisible();
    const outgoing = dialog.getByRole("combobox", { name: "Default outgoing" });
    await outgoing.click();
    await page.getByRole("option", { name: "None" }).click();
    await expect(outgoing).toBeFocused();
    await expect(page.getByText("Default outgoing account cleared", { exact: true })).toBeVisible();
    await expect.poll(async () => (await api.get(ACCOUNT, seeded)).default_outgoing).toBe(0);

    await outgoing.click();
    await page.getByRole("option", { name: seeded, exact: true }).click();
    await expect(page.getByText("Default outgoing account updated", { exact: true })).toBeVisible();
    await expect.poll(async () => (await api.get(ACCOUNT, seeded)).default_outgoing).toBe(1);
  } finally {
    await api.update(ACCOUNT, seeded, { default_outgoing: 1 });
  }
});

const NOTIFICATIONS = [
  { label: "Reply from contact", enabled: "enable_reply_email_to_agent", content: "reply_email_to_agent_content" },
  { label: "Reply from agent", enabled: "enable_reply_email_via_agent", content: "reply_via_agent_email_content" },
  { label: "Share feedback", enabled: "enable_email_ticket_feedback", content: "feedback_email_content" },
];

test("each notification saves its content and switch, and share feedback its status", async ({ page, api }) => {
  const fields = NOTIFICATIONS.flatMap((n) => [n.enabled, n.content]);
  const restore = await snapshotSettings(api, [...fields, "send_email_feedback_on_status"]);
  const before = await api.get("HD Settings", "HD Settings");
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Email Notifications");
    for (const notification of NOTIFICATIONS) {
      const content = `<p>E2E ${notification.label} ${uid()}</p>`;
      await openNotification(dialog, notification.label);
      if (notification.label === "Share feedback") {
        await dialog.getByRole("combobox", { name: /On ticket status/ }).click();
        await page.getByRole("option", { name: "Resolved" }).click();
      }
      await dialog.getByRole("textbox", { name: /Email Content/ }).fill(content);
      await dialog.getByRole("switch", { name: "Enabled" }).click();
      await dialog.getByRole("button", { name: "Save", exact: true }).click();
      await expect.poll(() => setting(api, notification.content)).toBe(content);
      expect(await setting(api, notification.enabled)).toBe(before[notification.enabled] ? 0 : 1);
      await dialog.getByRole("button", { name: "back to email event list" }).click();
    }
    expect(await setting(api, "send_email_feedback_on_status")).toBe("Resolved");
  } finally {
    await restore();
  }
});

test("notification content resets to the default, and leaving unsaved edits asks first", async ({ page, api }) => {
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Email Notifications");
  await openNotification(dialog, "Reply from agent");
  const content = dialog.getByRole("textbox", { name: /Email Content/ });
  const reset = dialog.getByRole("button", { name: "Reset Content" });
  await content.fill("<p>E2E draft that is never saved</p>");
  await expect(dialog.getByText("Unsaved", { exact: true })).toBeVisible();

  await reset.click();
  await page.getByRole("dialog", { name: "Reset content" }).getByRole("button", { name: "Confirm" }).click();
  await expect(reset).toBeDisabled();
  await expect(content).not.toHaveValue("<p>E2E draft that is never saved</p>");

  await content.fill("<p>E2E second draft</p>");
  await dialog.getByRole("button", { name: "back to email event list" }).click();
  await confirmUnsaved(page);
  await expect(dialog.getByRole("heading", { name: "Reply from agent", level: 2 })).toBeVisible();
  expect(await setting(api, "reply_via_agent_email_content")).not.toContain("E2E second draft");
});

test("an admin links and unlinks an outgoing email account", async ({ page, api }) => {
  const before = (await api.get("User", "Administrator")).user_emails;
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, / Profile$/);
    await dialog.getByRole("button", { name: "Configure" }).click();
    await linkEmailAccount(page, dialog);
    await expect.poll(() => linkedAccounts(api, "Administrator")).toContain("E2E Support");

    await dialog.getByText("E2E Support", { exact: true }).locator("xpath=..").getByRole("button", { name: "Remove" }).click();
    await dialog.getByRole("button", { name: "Update" }).click();
    await expect.poll(() => linkedAccounts(api, "Administrator")).not.toContain("E2E Support");
  } finally {
    await api.update("User", "Administrator", { user_emails: before });
  }
});

test.fixme("a plain agent links an outgoing email account", async ({ page, api }) => {
  // User.user_emails is permlevel 1, so an Agent's save silently drops the row.
  const email = `e2e-link-${uid()}@example.com`;
  await createThrowawayAgent(api, email, PASSWORD);
  await page.context().clearCookies();
  await page.request.post("/api/method/login", { form: { usr: email, pwd: PASSWORD } });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, / Profile$/);
  await dialog.getByRole("button", { name: "Configure" }).click();
  await linkEmailAccount(page, dialog);
  await expect.poll(() => linkedAccounts(api, email)).toEqual(["E2E Support"]);
});

async function linkEmailAccount(page: Page, dialog: Locator) {
  await dialog.getByRole("button", { name: "Add Email" }).click();
  await page.getByRole("option", { name: /E2E Support/ }).click();
  await dialog.getByRole("button", { name: "Update" }).click();
}

async function linkedAccounts(api: Api, user: string) {
  return (await api.get("User", user)).user_emails.map((row) => row.email_account);
}

function unsavedDialog(page: Page) {
  return page.getByRole("dialog", { name: "Unsaved changes" });
}

async function confirmUnsaved(page: Page) {
  const confirm = unsavedDialog(page);
  await confirm.getByRole("button", { name: "Confirm" }).click();
  await expect(confirm).toBeHidden();
}

function accountRow(dialog: Locator, name: string) {
  return dialog.getByRole("button").filter({ hasText: name });
}

async function openNotification(dialog: Locator, label: string) {
  await dialog.getByRole("listitem").filter({ hasText: label }).click();
  await expect(dialog.getByRole("heading", { name: label, level: 1 })).toBeVisible();
}

async function setting(api: Api, field: string) {
  return (await api.get("HD Settings", "HD Settings"))[field];
}

