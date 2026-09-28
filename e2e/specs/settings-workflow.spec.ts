import {
  expect,
  skipGettingStarted,
  test,
  uid,
  usePersona,
} from "../support/fixtures";
import {
  createThrowawayAgent,
  openSettings,
  snapshotSettings,
} from "../support/settings";
import { PASSWORD, personas } from "../support/personas";
import type { Locator, Page } from "@playwright/test";
import type { Api } from "../support/api";

const SLA = "HD Service Level Agreement";
const HOLIDAYS = "HD Service Holiday List";

usePersona("admin");

test("an SLA policy is created with targets and working hours, then made default", async ({ page, api }) => {
  const name = `E2E SLA ${uid()}`;
  const previousDefault = await api.exists(SLA, { default_sla: 1 });
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "SLA Policies");
    await dialog.getByRole("button", { name: "New" }).click();
    await dialog.getByRole("textbox", { name: /^Name/ }).fill(name);
    await dialog.getByRole("button", { name: "Save", exact: true }).click();

    await expect.poll(() => api.exists(SLA, { name })).toBeTruthy();
    const sla = await api.get(SLA, name);
    expect(sla.priorities.map((row) => row.priority).sort()).toEqual(["High", "Low", "Medium", "Urgent"]);
    expect(sla.support_and_resolution).toHaveLength(5);

    await dialog.getByRole("checkbox", { name: "Set as default SLA" }).check();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(async () => (await api.get(SLA, name)).default_sla).toBe(1);
    if (previousDefault) expect((await api.get(SLA, previousDefault)).default_sla).toBe(0);
  } finally {
    if (previousDefault) await api.update(SLA, previousDefault, { default_sla: 1 });
    if (await api.exists(SLA, { name })) await api.delete(SLA, name);
  }
});

test("a business holiday list is created with a holiday", async ({ page, api }) => {
  const name = `E2E Holidays ${uid()}`;
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Business Holidays");
    await dialog.getByRole("button", { name: "New" }).click();
    await dialog.getByRole("textbox", { name: /^Name/ }).fill(name);
    await pickDate(dialog.getByRole("combobox", { name: "From date" }), "2027-01-01");
    await pickDate(dialog.getByRole("combobox", { name: "To date" }), "2027-12-31");

    await dialog.getByRole("button", { name: "Add Holiday" }).click();
    const modal = page.getByRole("dialog", { name: "Add Holiday" });
    await pickDate(modal.getByRole("combobox"), "2027-01-26");
    await modal.getByPlaceholder("National holiday, etc.").fill("Republic Day");
    await modal.getByRole("button", { name: "Add Holiday" }).click();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();

    await expect.poll(() => api.exists(HOLIDAYS, { name })).toBeTruthy();
    const list = await api.get(HOLIDAYS, name);
    expect([list.from_date, list.to_date]).toEqual(["2027-01-01", "2027-12-31"]);
    expect(list.holidays.map((row) => row.holiday_date)).toContain("2027-01-26");
  } finally {
    if (await api.exists(HOLIDAYS, { name })) await api.delete(HOLIDAYS, name);
  }
});

test("an assignment rule for a team auto-assigns and notifies", async ({ page, api }) => {
  const team = `E2E Rule Team ${uid()}`;
  const rule = `E2E Rule ${uid()}`;
  await api.insert("HD Team", { team_name: team, users: [{ user: personas.agent.email }] });
  let ticket: { name: string } | undefined;
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Assignment Rules");
    await dialog.getByRole("button", { name: "New" }).click();
    await dialog.getByRole("textbox", { name: /^Name/ }).fill(rule);
    await dialog.getByRole("textbox", { name: /^Description/ }).fill("Route E2E team tickets");
    await dialog.getByText("Add a condition").first().click();
    await dialog.getByRole("button", { name: "Field", exact: true }).click();
    await page.getByRole("option", { name: "Team", exact: true }).click();
    await dialog.getByRole("combobox", { name: "condition" }).fill(team);
    await page.getByRole("option", { name: team }).click();
    await dialog.getByRole("button", { name: "Add Assignee" }).click();
    await page.getByPlaceholder("Search").last().fill("Bela");
    await page.getByRole("option", { name: /Bela E2E/ }).click();
    await expect(dialog.first().getByRole("button", { name: "Bela E2E" })).toBeVisible();
    await dialog.first().getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(() => api.exists("Assignment Rule", { name: rule })).toBeTruthy();

      ticket = await api.insert("HD Ticket", { subject: `Routed ${uid()}`, description: "x", agent_group: team });
    await expect
      .poll(async () => (await assignees(api, ticket!.name)) || "")
      .toContain(personas.agent2.email);
    await expect
      .poll(() => api.exists("Notification Log", { for_user: personas.agent2.email, document_name: ticket!.name }))
      .toBeTruthy();
  } finally {
    if (await api.exists("Assignment Rule", { name: rule })) await api.delete("Assignment Rule", rule);
    if (ticket) await api.delete("HD Ticket", ticket.name);
    await api.delete("HD Team", team);
  }
});

test("a field dependency narrows the child field on the new ticket form", async ({ page, api }) => {
  const template = `E2E FD ${uid()}`;
  const script = "Field Dependency-priority-ticket_type";
  await api.insert("HD Ticket Template", {
    template_name: template,
    fields: [{ fieldname: "priority" }, { fieldname: "ticket_type" }],
  });
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Field Dependencies");
    await dialog.getByRole("button", { name: "New" }).click();
    await pickOption(page, dialog.getByRole("combobox", { name: "Select option" }).first(), "Priority");
    await pickOption(page, dialog.getByRole("combobox", { name: "Select option" }).nth(1), "Ticket Type");
    await dialog.getByRole("listitem").filter({ hasText: /^Urgent$/ }).click();
    await dialog.getByRole("listitem").filter({ hasText: /^Bug$/ }).getByRole("checkbox").check();
    // Leave the visibility and mandatory rules off so HD Ticket's schema stays untouched.
    for (const rule of [/^Show Ticket Type if/, /^Make Ticket Type mandatory if/]) {
      await dialog.getByText(rule).locator("xpath=ancestor::div[.//button[@role='switch']][1]").getByRole("switch").click();
    }
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(() => api.exists("HD Form Script", { name: script })).toBeTruthy();

    await page.goto(`/helpdesk/tickets/new/${encodeURIComponent(template)}`);
    await pickOption(page, templateField(page, "Priority"), "Urgent");
    await templateField(page, "Ticket Type").click();
    await expect(page.getByRole("option")).toHaveText(["Bug"]);
  } finally {
    if (await api.exists("HD Form Script", { name: script })) await api.delete("HD Form Script", script);
    await api.delete("HD Ticket Template", template);
  }
});

test("saved replies are created and deleting one removes only that row", async ({ page, api }) => {
  const [keep, drop] = [`E2E Keep ${uid()}`, `E2E Drop ${uid()}`];
  await api.insert("HD Saved Reply", { title: keep, message: "<p>keep</p>", scope: "Personal" });
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Saved Replies");
    await dialog.getByRole("button", { name: "New" }).click();
    await dialog.getByRole("textbox", { name: /^Name/ }).fill(drop);
    await dialog.locator("[contenteditable=true]").fill("Thanks for waiting.");
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(() => api.exists("HD Saved Reply", { title: drop })).toBeTruthy();

    await dialog.getByRole("button", { name: drop }).click();
    const row = dialog.locator("div.grid").filter({ hasText: drop });
    await row.getByRole("button").click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
    await expect.poll(() => api.exists("HD Saved Reply", { title: drop })).toBeFalsy();
    expect(await api.exists("HD Saved Reply", { title: keep })).toBeTruthy();
  } finally {
    for (const title of [keep, drop]) {
      const name = await api.exists("HD Saved Reply", { title });
      if (name) await api.delete("HD Saved Reply", name);
    }
  }
});

test("the email account form validates, and notifications can be toggled", async ({ page, api }) => {
  const restore = await snapshotSettings(api, ["send_acknowledgement_email"]);
  const before = (await api.get("HD Settings", "HD Settings")).send_acknowledgement_email;
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Email Notifications");
    await dialog.getByRole("listitem").filter({ hasText: "Acknowledgement" }).click();
    await dialog.getByRole("switch").click();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect
      .poll(async () => (await api.get("HD Settings", "HD Settings")).send_acknowledgement_email)
      .toBe(before ? 0 : 1);

    await dialog.getByRole("button", { name: "Email Accounts", exact: true }).click();
    await dialog.getByRole("button", { name: "New" }).click();
    await dialog.getByText("Custom", { exact: true }).click();
    await dialog.getByRole("button", { name: "Create" }).click();
    await expect(dialog.getByText("Account name is required")).toBeVisible();
  } finally {
    await restore();
  }
});

test("general settings update the brand name and ticket toggles", async ({ page, api }) => {
  const restore = await snapshotSettings(api, ["brand_name", "is_feedback_mandatory", "enable_comment_reactions"]);
  const brand = `E2E Desk ${uid()}`;
  const before = await api.get("HD Settings", "HD Settings");
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "General");
    await dialog.getByRole("textbox", { name: "Brand name" }).fill(brand);
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(() => setting(api, "brand_name")).toBe(brand);

    // Toggles save on change, one at a time.
    await settingSwitch(dialog, "Make feedback mandatory").click();
    await expect.poll(() => setting(api, "is_feedback_mandatory")).toBe(before.is_feedback_mandatory ? 0 : 1);
    await settingSwitch(dialog, "Enable comment reactions").click();
    await expect.poll(() => setting(api, "enable_comment_reactions")).toBe(before.enable_comment_reactions ? 0 : 1);

    await page.reload();
    await expect(page.getByRole("button", { name: new RegExp(`^${brand} `) })).toBeVisible();
  } finally {
    await restore();
  }
});

// Regression: a second toggle during the first save used to fail with a 417.
test("toggling two general settings quickly saves both", async ({ page, api }) => {
  const restore = await snapshotSettings(api, ["is_feedback_mandatory", "enable_comment_reactions"]);
  const before = await api.get("HD Settings", "HD Settings");
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "General");
    await settingSwitch(dialog, "Make feedback mandatory").click();
    await settingSwitch(dialog, "Enable comment reactions").click();
    await expect.poll(() => setting(api, "enable_comment_reactions")).toBe(before.enable_comment_reactions ? 0 : 1);
    expect(await setting(api, "is_feedback_mandatory")).toBe(before.is_feedback_mandatory ? 0 : 1);
  } finally {
    await restore();
  }
});

test.describe("preferences", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("language and timezone preferences persist", async ({ page, api }) => {
    const email = `e2e-prefs-${uid()}@example.com`;
    await createThrowawayAgent(api, email, PASSWORD);
    await page.request.post("/api/method/login", { form: { usr: email, pwd: PASSWORD } });
    await skipGettingStarted(page, email);

    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Preferences");
    await dialog.getByRole("button", { name: "Select language" }).click();
    await page.getByRole("option", { name: "Svenska" }).click();
    await dialog.locator("button", { hasText: /\w+\/\w+/ }).click();
    await page.getByRole("combobox").or(page.getByPlaceholder(/Search/)).last().fill("Europe/Berlin");
    await page.getByRole("option", { name: "Europe/Berlin" }).click();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();

    await expect.poll(async () => (await api.get("User", email)).time_zone).toBe("Europe/Berlin");
    expect((await api.get("User", email)).language).toBe("sv");
  });
});

async function pickDate(input: Locator, isoDate: string) {
  await input.fill(isoDate);
  await input.press("Enter");
}

async function pickOption(page: Page, combobox: Locator, option: string) {
  await combobox.click();
  await page.getByRole("option", { name: option, exact: true }).click();
}

function settingSwitch(dialog: Locator, label: string) {
  return dialog.getByText(label, { exact: true }).locator("xpath=ancestor::div[.//button[@role='switch']][1]").getByRole("switch");
}

function templateField(page: Page, label: string) {
  return page
    .getByText(label, { exact: true })
    .locator("xpath=ancestor::div[.//*[@role='combobox']][1]")
    .getByRole("combobox");
}

async function setting(api: Api, field: string) {
  return (await api.get("HD Settings", "HD Settings"))[field];
}

// REST reads drop `_assign`, so ask for the column directly.
async function assignees(api: Api, ticket: string): Promise<string | undefined> {
  const value = await api.call("frappe.client.get_value", {
    doctype: "HD Ticket",
    filters: { name: ticket },
    fieldname: "_assign",
  });
  return value._assign;
}
