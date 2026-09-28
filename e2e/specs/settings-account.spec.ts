import type { Locator, Page } from "@playwright/test";
import { Api } from "../support/api";
import { expect, skipGettingStarted, test, uid, usePersona } from "../support/fixtures";
import { PASSWORD, personas } from "../support/personas";
import { createThrowawayAgent, openSettings, snapshotSettings } from "../support/settings";

const PIXEL = "e2e/fixtures/pixel.png";

usePersona("admin");

test.describe("my settings", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("an agent renames themselves, sets and removes a photo, and changes their password", async ({
    page,
    api,
    baseURL,
  }) => {
    const email = await loginAsNewAgent(page, api);
    const dialog = await openSettings(page, / Profile$/);

    await dialog.getByText(email.split("@")[0], { exact: true }).locator("xpath=following-sibling::button").click();
    await dialog.getByRole("textbox").fill("Renamed Person");
    await page.keyboard.press("Enter");
    await expect.poll(async () => (await api.get("User", email)).last_name).toBe("Person");
    expect((await api.get("User", email)).first_name).toBe("Renamed");

    const chooser = page.waitForEvent("filechooser");
    await dialog.locator(".group.relative div.cursor-pointer").first().click();
    await (await chooser).setFiles(PIXEL);
    await expect.poll(async () => (await api.get("User", email)).user_image).toContain("/files/");
    await dialog.locator(".group.relative").first().hover();
    await dialog.locator(".group.relative div.\\-top-1").click();
    await expect.poll(async () => (await api.get("User", email)).user_image).toBeFalsy();

    const newPassword = `E2e-Changed-${uid()}!`;
    await dialog.getByRole("button", { name: "Change Password" }).click();
    const change = page.getByRole("dialog", { name: "Change Password" });
    const update = change.getByRole("button", { name: "Update" });
    await change.getByPlaceholder("New Password").fill("short");
    await expect(change.getByText("Password must be at least 8 characters")).toBeVisible();
    await change.getByPlaceholder("New Password").fill(newPassword);
    await change.getByPlaceholder("Confirm Password").fill(`${newPassword}x`);
    await expect(change.getByText("Passwords do not match")).toBeVisible();
    await expect(update).toBeDisabled();
    await change.getByPlaceholder("Confirm Password").fill(newPassword);
    await expect(change.getByText("Passwords match")).toBeVisible();
    await update.click();
    await expect(change).toBeHidden();
    await Api.login(baseURL!, email, newPassword);
  });

  test("an agent sets a signature, and leaving unsaved changes asks first", async ({ page, api }) => {
    const email = await loginAsNewAgent(page, api);
    const dialog = await openSettings(page, / Profile$/);
    await dialog.getByRole("button", { name: "Configure" }).click();

    await dialog.locator(".ProseMirror").fill("Regards from E2E");
    await dialog.getByRole("button", { name: "Update" }).click();
    await expect.poll(async () => (await api.get("User", email)).email_signature).toContain("Regards from E2E");

    await dialog.locator(".ProseMirror").fill("Unsaved signature");
    await dialog.getByRole("button", { name: "Email Settings" }).click();
    await page.getByRole("dialog", { name: "Unsaved changes" }).getByRole("button", { name: "Confirm" }).click();
    await expect(dialog.getByRole("button", { name: "Change Password" })).toBeVisible();
    expect((await api.get("User", email)).email_signature).not.toContain("Unsaved signature");
  });
});

test("the theme preference applies at once and survives a reload", async ({ page }) => {
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Preferences");
  const themes = dialog.getByRole("radiogroup");
  await themes.getByText("Dark", { exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

  const reopened = await openSettings(page, "Preferences");
  await reopened.getByRole("radiogroup").getByText("Light", { exact: true }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("restricting tickets by team needs a restriction option before saving", async ({ page, api }) => {
  const before = await api.get("HD Settings", "HD Settings");
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "General");
  const restrict = settingRow(dialog, "Restrict tickets by team").getByRole("switch");
  await restrict.click();
  await dialog.getByRole("checkbox", { name: "Do not restrict tickets without a team" }).uncheck();
  await dialog.getByRole("checkbox", { name: "Restrict agent assignment to selected team" }).uncheck();
  await expect(dialog.getByText("Disable global saved replies", { exact: true })).toBeVisible();

  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect(page.getByText("Please select at least one restriction option for teams in the settings.")).toBeVisible();
  const after = await api.get("HD Settings", "HD Settings");
  expect(after.restrict_tickets_by_agent_group).toBe(before.restrict_tickets_by_agent_group);

  await restrict.click();
  await dialog.getByRole("checkbox", { name: "Do not restrict tickets without a team" }).waitFor({ state: "detached" });
});

test("ticket automation settings save status updates, auto close and the banner", async ({ page, api }) => {
  const restore = await snapshotSettings(api, [
    "auto_update_status",
    "update_status_to",
    "default_ticket_type",
    "auto_close_tickets",
    "auto_close_status",
    "auto_close_after_days",
    "enable_outside_hours_banner",
    "outside_working_hours_message",
  ]);
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "General");
    await pickFromDropdown(page, settingRow(dialog, "Auto update status"), "Replied");
    await pickFromDropdown(page, settingRow(dialog, "Default ticket type"), "Question");
    await pickFromDropdown(page, settingRow(dialog, "Ticket status"), "Resolved");
    const days = dialog.getByRole("spinbutton", { name: "Auto-close after (Days)" });
    await days.fill("0");
    const dayError = dialog.getByText("The number of days must be 1 or more");
    await expect(dayError).toBeVisible();
    await days.fill("5");
    // The field is debounced; the error clearing shows 5 reached the form.
    await expect(dayError).toBeHidden();

    await settingRow(dialog, "Outside working hours notice").getByRole("switch").click();
    const banner = dialog.getByPlaceholder("Enter Notification Message");
    const defaultMessage = await banner.inputValue();
    expect(defaultMessage).not.toBe("");
    await banner.fill("E2E custom banner");
    await dialog.getByRole("button", { name: "Reset Content" }).click();
    await expect(banner).toHaveValue(defaultMessage);

    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect
      .poll(() => api.get("HD Settings", "HD Settings"))
      .toMatchObject({
        auto_update_status: 1,
        update_status_to: "Replied",
        default_ticket_type: "Question",
        auto_close_tickets: 1,
        auto_close_status: "Resolved",
        auto_close_after_days: 5,
        enable_outside_hours_banner: 1,
      });
  } finally {
    await restore();
  }
});

test("the brand logo uploads and removes, and signup can be disabled", async ({ page, api }) => {
  const restore = await snapshotSettings(api, ["brand_logo"]);
  const signup = (await api.get("Website Settings", "Website Settings")).disable_signup;
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "General");
    const logo = settingRow(dialog, "Logo");
    const chooser = page.waitForEvent("filechooser");
    await logo.getByRole("button", { name: "Upload" }).click();
    await (await chooser).setFiles(PIXEL);
    await expect.poll(async () => (await api.get("HD Settings", "HD Settings")).brand_logo).toContain("/files/");

    await logo.getByRole("button", { name: "Remove" }).click();
    await page.getByRole("dialog", { name: "Remove Logo" }).getByRole("button", { name: "Confirm" }).click();
    await expect.poll(async () => (await api.get("HD Settings", "HD Settings")).brand_logo).toBeFalsy();

    // Signup saves as soon as it is toggled.
    await settingRow(dialog, "Disable signup").getByRole("switch").click();
    await expect
      .poll(async () => (await api.get("Website Settings", "Website Settings")).disable_signup)
      .toBe(signup ? 0 : 1);
  } finally {
    await restore();
    await api.update("Website Settings", "Website Settings", { disable_signup: signup });
  }
});

test("agents can be filtered, re-enabled and promoted to manager", async ({ page, api }) => {
  const email = `e2e-role-${uid()}@example.com`;
  await createThrowawayAgent(api, email);
  await api.update("HD Agent", email, { is_active: 0 });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Agents");

  await dialog.getByRole("button", { name: "Active", exact: true }).click();
  await page.getByRole("menuitem", { name: "Inactive" }).click();
  await dialog.getByRole("textbox", { name: "Search" }).fill(email.split("@")[0]);
  const row = dialog.locator("div.group").filter({ hasText: email });
  await expect(row.getByText("Inactive", { exact: true })).toBeVisible();
  await row.getByRole("button").last().click();
  await page.getByRole("menuitem", { name: "Enable Agent" }).click();
  await expect.poll(async () => (await api.get("HD Agent", email)).is_active).toBe(1);

  await dialog.getByRole("button", { name: "Inactive", exact: true }).click();
  await page.getByRole("menuitem", { name: "All" }).click();
  await row.getByRole("button", { name: "Agent" }).click();
  await page.getByRole("menuitem", { name: "Manager" }).click();
  await expect.poll(() => roles(api, email)).toContain("Agent Manager");
  await row.getByRole("button", { name: "Manager" }).click();
  await page.getByRole("menuitem", { name: "Agent" }).click();
  await expect.poll(() => roles(api, email)).not.toContain("Agent Manager");

  await dialog.getByRole("button", { name: "New", exact: true }).click();
  await expect(dialog.getByRole("heading", { name: "Invite Agents" })).toBeVisible();
});

test("a new team needs a member, can start disabled, and warns before discarding", async ({ page, api }) => {
  const name = `E2E Team ${uid()}`;
  const member = personas.agent2.email;
  try {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Teams");
    await dialog.getByRole("button", { name: "New" }).click();
    await dialog.getByRole("textbox", { name: /Team Name/ }).fill(name);
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect(dialog.getByText("At least one team member is required")).toBeVisible();

    await pickAgent(page, dialog, "Bela E2E");
    await dialog.getByRole("button", { name: member }).locator("svg").last().click();
    await expect(dialog.getByRole("button", { name: member })).toHaveCount(0);
    await pickAgent(page, dialog, "Bela E2E");
    await dialog.getByRole("switch").click();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(async () => (await api.exists("HD Team", { name })) && (await api.get("HD Team", name)).disabled).toBe(1);
    expect((await api.get("HD Team", name)).users.map((row) => row.user)).toEqual([member]);

    await dialog.getByRole("button", { name, exact: true }).click();
    await dialog.getByRole("button", { name: "New" }).click();
    await dialog.getByRole("textbox", { name: /Team Name/ }).fill(`${name} Draft`);
    await dialog.getByRole("button", { name: `${name} Draft` }).click();
    await page.getByRole("dialog", { name: "Unsaved changes" }).getByRole("button", { name: "Confirm" }).click();
    const listed = dialog.getByText(name, { exact: true }).locator("xpath=..");
    await expect(listed.getByText("Disabled", { exact: true })).toBeVisible();
    expect(await api.exists("HD Team", { name: `${name} Draft` })).toBeFalsy();
  } finally {
    if (await api.exists("HD Team", { name })) await api.delete("HD Team", name);
  }
});

async function loginAsNewAgent(page: Page, api: Api) {
  const email = `e2e-profile-${uid()}@example.com`;
  await createThrowawayAgent(api, email, PASSWORD);
  await page.request.post("/api/method/login", { form: { usr: email, pwd: PASSWORD } });
  await skipGettingStarted(page, email);
  await page.goto("/helpdesk/tickets");
  return email;
}

function settingRow(dialog: Locator, label: string) {
  return dialog.getByText(label, { exact: true }).locator("xpath=ancestor::div[.//button][1]");
}

async function pickFromDropdown(page: Page, row: Locator, option: string) {
  await row.getByRole("button").first().click();
  await page.locator("[data-reka-popper-content-wrapper]").getByText(option, { exact: true }).click();
}

async function pickAgent(page: Page, dialog: Locator, agentName: string) {
  await dialog.getByPlaceholder("Type agent name or email").fill(agentName);
  await page.getByRole("option", { name: agentName }).click();
}

async function roles(api: Api, email: string) {
  return (await api.get("User", email)).roles.map((row) => row.role);
}
