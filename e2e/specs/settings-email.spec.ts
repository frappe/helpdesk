import type { Locator, Page } from "@playwright/test";
import type { Api } from "../support/api";
import { expect, test, uid, usePersona } from "../support/fixtures";
import { PASSWORD } from "../support/personas";
import { createThrowawayAgent, openSettings, snapshotSettings } from "../support/settings";

const ACCOUNT = "Email Account";

usePersona("admin");

test("the new email account form validates each provider and reports a bad server", async ({ page, api }) => {
  const name = `E2E Add ${uid()}`;
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Email Accounts");
  await dialog.getByRole("button", { name: "New" }).click();
  const create = dialog.getByRole("button", { name: "Create" });

  await dialog.getByText("GMail", { exact: true }).click();
  await create.click();
  await expect(dialog.getByText("Account name is required")).toBeVisible();
  await dialog.getByRole("textbox", { name: "Account name" }).fill(name);
  await create.click();
  await expect(dialog.getByText("Email ID is required")).toBeVisible();
  await dialog.getByRole("textbox", { name: "Email ID" }).fill("not-an-email");
  await create.click();
  await expect(dialog.getByText("Invalid email ID")).toBeVisible();
  await dialog.getByRole("textbox", { name: "Email ID" }).fill(`e2e-add-${uid()}@helpdesk.test`);
  await create.click();
  await expect(dialog.getByText("Password is required")).toBeVisible();

  await dialog.getByText("Frappe Mail", { exact: true }).click();
  await create.click();
  await expect(dialog.getByText("API Key is required")).toBeVisible();

  await dialog.getByText("Custom", { exact: true }).click();
  await create.click();
  await expect(dialog.getByText("Email Domain or manual server settings are required")).toBeVisible();
  await fillServers(dialog, "993", "587");
  await dialog.getByRole("textbox", { name: "Password" }).fill("secret");
  await create.click();
  await expect(dialog.getByText("Failed to create email account, Invalid credentials")).toBeVisible();
  expect(await api.exists(ACCOUNT, { email_account_name: name })).toBeFalsy();

  await dialog.getByRole("button", { name: "Back" }).click();
  await expect(dialog.getByRole("heading", { name: "Email Accounts" })).toBeVisible();
});

test("an email account is edited, renamed, and rejects outgoing mail without a password", async ({ page, api }) => {
  const name = `E2E Edit ${uid()}`;
  const renamed = `${name} Renamed`;
  await api.insert(ACCOUNT, {
    email_account_name: name,
    email_id: `e2e-edit-${uid()}@helpdesk.test`,
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
    const card = accountCard(dialog, name);
    await expect(card.getByText("Inbox", { exact: true })).toBeVisible();
    await card.click();

    const update = dialog.getByRole("button", { name: "Update Account" });
    await expect(update).toHaveCount(0);
    await dialog.getByRole("textbox", { name: "Outgoing Port" }).fill("2525");
    await update.click();
    await expect.poll(async () => (await api.get(ACCOUNT, name)).smtp_port).toBe("2525");

    await accountCard(dialog, name).click();
    await dialog.getByRole("textbox", { name: "Account name" }).fill(renamed);
    await update.click();
    await expect.poll(() => api.exists(ACCOUNT, { name: renamed })).toBeTruthy();

    await accountCard(dialog, renamed).click();
    await dialog.getByRole("checkbox", { name: "Enable Outgoing" }).check();
    await update.click();
    await expect(dialog.getByText("Failed to update email account, Invalid credentials")).toBeVisible();
    expect((await api.get(ACCOUNT, renamed)).enable_outgoing).toBe(0);
  } finally {
    for (const account of [name, renamed]) {
      if (await api.exists(ACCOUNT, { name: account })) await api.delete(ACCOUNT, account);
    }
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
  await page.getByRole("dialog", { name: "Unsaved changes" }).getByRole("button", { name: "Confirm" }).click();
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

function accountCard(dialog: Locator, name: string) {
  return dialog.getByText(name, { exact: true }).locator("xpath=ancestor::div[contains(@class, 'cursor-pointer')][1]");
}

async function fillServers(dialog: Locator, incomingPort: string, outgoingPort: string) {
  await dialog.getByRole("textbox", { name: "Incoming Server (IMAP/POP)" }).fill("imap.e2e.invalid");
  await dialog.getByRole("textbox", { name: "Incoming Port" }).fill(incomingPort);
  await dialog.getByRole("textbox", { name: "Outgoing Server (SMTP)" }).fill("smtp.e2e.invalid");
  await dialog.getByRole("textbox", { name: "Outgoing Port" }).fill(outgoingPort);
}

async function openNotification(dialog: Locator, label: string) {
  await dialog.getByRole("listitem").filter({ hasText: label }).click();
  await expect(dialog.getByRole("heading", { name: label, level: 1 })).toBeVisible();
}

async function setting(api: Api, field: string) {
  return (await api.get("HD Settings", "HD Settings"))[field];
}

