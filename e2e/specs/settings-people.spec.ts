import { expect, test, uid, usePersona } from "../support/fixtures";
import { personas } from "../support/personas";
import {
  createThrowawayAgent,
  openSettings,
} from "../support/settings";
import type { Locator, Page } from "@playwright/test";
import type { Api } from "../support/api";

usePersona("admin");

test("every settings tab opens without errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("response", (response) => {
    if (response.url().includes("/api/") && response.status() >= 500) {
      errors.push(`${response.status()} ${response.url()}`);
    }
  });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Preferences");
  const tabs = dialog.getByRole("navigation").getByRole("button");
  expect(await tabs.count()).toBeGreaterThan(10);

  for (const tab of await tabs.all()) {
    await tab.click();
    await expect(dialog.getByRole("heading", { level: 1 }).nth(1)).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("inviting an agent shows it pending, and accepting creates the agent", async ({ page, api }) => {
  const [cancelled, accepted] = [`e2e-cancel-${uid()}@example.com`, `e2e-invite-${uid()}@example.com`];
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Invite Agents");

  await dialog.getByRole("textbox", { name: /Invite by email/ }).fill(`${cancelled}, ${accepted}`);
  // The textarea's v-model is debounced by 100ms.
  await page.waitForTimeout(300);
  await dialog.getByRole("button", { name: "Send Invites" }).click();
  const pending = dialog.getByRole("listitem");
  await expect(pending.filter({ hasText: cancelled })).toBeVisible();
  await expect(pending.filter({ hasText: accepted })).toBeVisible();

  await pending.filter({ hasText: cancelled }).getByRole("button").click();
  await expect(pending.filter({ hasText: cancelled })).toHaveCount(0);
  expect(await invitationStatus(api, cancelled)).toBe("Cancelled");

  const key = await invitationKey(api, accepted);
  const response = await page.request.get(
    `/api/method/frappe.core.api.user_invitation.accept_invitation?key=${key}`,
    { maxRedirects: 0 }
  );
  expect(response.status()).toBeLessThan(400);
  expect(await invitationStatus(api, accepted)).toBe("Accepted");
  expect(await api.exists("HD Agent", { user: accepted })).toBeTruthy();
});

test("inviting an agent ticks the invite onboarding step", async ({ page, api }) => {
  const steps = [{ name: "invite_agents", completed: false }];
  await api.call("frappe.onboarding.update_user_onboarding_status", {
    steps: JSON.stringify(steps),
    appName: "helpdesk",
  });
  await page.addInitScript(() => localStorage.clear());
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Invite Agents");
  await dialog.getByRole("textbox", { name: /Invite by email/ }).fill(`e2e-step-${uid()}@example.com`);
  await page.waitForTimeout(300);
  await dialog.getByRole("button", { name: "Send Invites" }).click();
  await expect
    .poll(async () => {
      const status = await api.call("frappe.onboarding.get_onboarding_status");
      return status.helpdesk_onboarding_status?.find((step) => step.name === "invite_agents")?.completed;
    })
    .toBe(true);
});

test("a disabled agent disappears from the assignee list", async ({ page, api }) => {
  const email = `e2e-disable-${uid()}@example.com`;
  const agent = await createThrowawayAgent(api, email);
  const ticket = await api.insert("HD Ticket", { subject: `Disable check ${uid()}`, description: "x" });

  await page.goto(`/helpdesk/tickets/${ticket.name}`);
  await expect(await assigneeOption(page, agent.agent_name)).toBeVisible();

  const dialog = await openSettings(page, "Agents");
  await dialog.getByRole("textbox", { name: "Search" }).fill(email);
  const row = dialog.locator("div.group").filter({ hasText: email });
  await row.getByRole("button").last().click();
  await page.getByRole("menuitem", { name: "Disable Agent" }).click();
  await expect.poll(async () => (await api.get("HD Agent", email)).is_active).toBe(0);

  await page.goto(`/helpdesk/tickets/${ticket.name}`);
  await expect(await assigneeOption(page, agent.agent_name)).toHaveCount(0);
});

test("teams can be created, staffed, renamed, disabled and deleted", async ({ page, api }) => {
  const name = `E2E Team ${uid()}`;
  const renamed = `${name} Renamed`;
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Teams");

  await dialog.getByRole("button", { name: "New" }).click();
  await dialog.getByRole("textbox", { name: /Team Name/ }).fill(name);
  await pickAgent(page, dialog, "Bela E2E");
  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect.poll(() => teamUsers(api, name)).toEqual([personas.agent2.email]);

  await pickAgent(page, dialog, "Arjun E2E");
  await dialog.getByRole("button", { name: "Add Member" }).click();
  await expect
    .poll(() => teamUsers(api, name))
    .toEqual([personas.agent2.email, personas.agent.email].sort());

  await teamMenu(page, dialog, "Rename");
  const rename = page.getByRole("dialog", { name: "Rename team" });
  await rename.getByRole("textbox", { name: "Title" }).fill(renamed);
  await rename.getByRole("button", { name: "Confirm" }).click();
  await expect.poll(() => api.exists("HD Team", { name: renamed })).toBeTruthy();

  await dialog.getByText(renamed, { exact: true }).click();
  await dialog.getByRole("switch").click();
  await expect.poll(async () => (await api.get("HD Team", renamed)).disabled).toBe(1);

  await teamMenu(page, dialog, "Delete");
  await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
  await expect.poll(() => api.exists("HD Team", { name: renamed })).toBeFalsy();
});

async function pickAgent(page: Page, dialog: Locator, agentName: string) {
  await dialog.getByPlaceholder("Type agent name or email").fill(agentName);
  await page.getByRole("option", { name: agentName }).click();
}

async function teamMenu(page: Page, dialog: Locator, item: string) {
  const header = dialog.getByText("Enabled", { exact: true }).locator("xpath=../..");
  await header.getByRole("button").click();
  await page.getByRole("menuitem", { name: item }).click();
}

async function teamUsers(api: Api, name: string) {
  if (!(await api.exists("HD Team", { name }))) return [];
  const team = await api.get("HD Team", name);
  return team.users.map((row) => row.user).sort();
}

async function assigneeOption(page: Page, agentName: string) {
  const field = page
    .getByText("Assignee", { exact: true })
    .locator("xpath=ancestor::div[.//button][1]");
  await field.getByRole("button").click();
  const search = page.getByRole("textbox", { name: "Search agents..." });
  await search.fill(agentName);
  return page.getByRole("dialog").getByRole("button", { name: agentName });
}

async function invitationStatus(api: Api, email: string) {
  const [invitation] = await api.list("User Invitation", {
    fields: ["status"],
    filters: { email },
  });
  return invitation?.status;
}

// The raw key only exists in the invitation email, so read it from the queue.
async function invitationKey(api: Api, email: string) {
  const [mail] = await api.list("Email Queue", {
    fields: ["message"],
    filters: [["Email Queue Recipient", "recipient", "=", email]],
  });
  const body = mail.message.replace(/=\r?\n/g, "").replace(/=3D/g, "=");
  return body.match(/accept_invitation\?key=(\w+)/)?.[1];
}
