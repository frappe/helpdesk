import type { Browser, BrowserContext, Locator, Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expectDenied } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { PASSWORD } from "../../helpers/personas";
import { loginContext } from "../../helpers/portal";
import { snapshotSettings } from "../../helpers/settings";
import { siteHeader } from "../../helpers/site";

// The portal's settings dialog (`kb_settings`), driven as throwaway customers so the shared personas never change.

const PIXEL = "e2e/fixtures/pixel.png";
const PORTAL_TOGGLES = [
  "allow_customer_managers_to_invite",
  "allow_customer_managers_to_change_roles",
  "allow_customer_managers_to_remove_members",
  "allow_customer_managers_to_edit_organization",
];

interface Person {
  email: string;
  contact: string;
  fullName: string;
}

const contexts: BrowserContext[] = [];
test.afterEach(async () => {
  await Promise.all(contexts.splice(0).map((context) => context.close()));
});

async function newPerson(api: Api, domain: string, roles = ["HD Customer"], label = "Person"): Promise<Person> {
  const id = uid();
  const email = `${label.toLowerCase()}-${id}@${domain}`;
  await api.insert("User", {
    email,
    first_name: label,
    last_name: id,
    send_welcome_email: 0,
    user_type: "Website User",
    new_password: PASSWORD,
    roles: roles.map((role) => ({ role })),
  });
  const contact = await api.insert("Contact", {
    first_name: label,
    last_name: id,
    email_id: email,
    user: email,
    email_ids: [{ email_id: email, is_primary: 1 }],
  });
  return { email, contact: contact.name, fullName: `${label} ${id}` };
}

/** An organization with an owner, a manager and a member, on its own domain. */
async function newOrg(api: Api) {
  const domain = `org-${uid()}.test`;
  const owner = await newPerson(api, domain, ["HD Customer", "HD Customer Manager"], "Owner");
  const manager = await newPerson(api, domain, ["HD Customer", "HD Customer Manager"], "Manager");
  const member = await newPerson(api, domain, ["HD Customer"], "Member");
  const org = await api.insert("HD Customer", {
    customer_name: `E2E Org ${uid()}`,
    domain,
    country: "India",
    primary_contact: owner.contact,
    contacts: [
      { contact_name: owner.contact, is_manager: 1 },
      { contact_name: manager.contact, is_manager: 1 },
      { contact_name: member.contact, is_manager: 0 },
    ],
  });
  return { name: org.name as string, domain, owner, manager, member };
}

async function pageOf(browser: Browser, baseURL: string, email: string, password = PASSWORD, viewport?: { width: number; height: number }) {
  const context = await browser.newContext({ baseURL, extraHTTPHeaders: siteHeader(), viewport });
  contexts.push(context);
  const response = await context.request.post("/api/method/login", { form: { usr: email, pwd: password } });
  expect(response.ok(), `login ${email}`).toBeTruthy();
  return context.newPage();
}

async function openSettingsAt(page: Page, hash = "settings/profile") {
  await page.goto(`/help#${hash}`);
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await expect(dialog).toBeVisible();
  return dialog;
}

async function openOrgScreen(page: Page, org: string) {
  const dialog = await openSettingsAt(page, `settings/members/${org}`);
  await expect(dialog.getByText(org, { exact: true })).toBeVisible();
  return dialog;
}

function memberRows(dialog: Locator) {
  return dialog.locator("div.min-h-13");
}

function memberRow(dialog: Locator, text: string) {
  return memberRows(dialog).filter({ hasText: text });
}

function toast(page: Page, text: string | RegExp) {
  return page.getByText(text).first();
}

/** frappe-ui's Select is a listbox button, not a native select. */
async function choose(page: Page, select: Locator, option: string) {
  await select.click();
  await page.getByRole("option", { name: option, exact: true }).click();
}

async function confirm(page: Page, title: string, button: string) {
  const dialog = page.getByRole("dialog", { name: title });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: button, exact: true }).click();
}

test.describe("dialog", () => {
  usePersona("customerManager");

  test("S1 opens from the menu, follows each screen in the hash, and closes", async ({ page }) => {
    await page.goto("/help");
    await page.getByRole("button", { name: /Helpdesk/ }).first().click();
    await page.getByRole("menuitem", { name: "Settings" }).click();
    const dialog = page.getByRole("dialog", { name: "Settings" });
    await expect(dialog.getByRole("heading", { name: "Profile" })).toBeVisible();
    await expect(page).toHaveURL(/#settings\/profile$/);

    await dialog.getByRole("tab", { name: "Manage Organization" }).click();
    await expect(page).toHaveURL(/#settings\/members\/E2E%20Customer%20Org$/);
    await page.goBack();
    await expect(page).toHaveURL(/#settings\/profile$/);
    await expect(dialog.getByRole("heading", { name: "Profile" })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(page).not.toHaveURL(/#settings/);

    await openSettingsAt(page);
    await page.mouse.click(5, 300);
    await expect(dialog).toBeHidden();
    await expect(page).not.toHaveURL(/#settings/);
  });

  test("S4 a customer's hash for an admin tab shows nothing broken", async ({ page }) => {
    const dialog = await openSettingsAt(page, "settings/knowledge-base");
    await expect(dialog.getByRole("tab", { name: "Knowledge Base" })).toHaveCount(0);
    await expect(dialog.getByText("Make knowledge base public")).toHaveCount(0);
    await page.screenshot({ path: `${process.env.WALK_SHOTS || "test-results"}/walkthrough-S4-kb-hash.png` });
    // The admin tab stays selected but hidden, so the content pane is blank.
    await expect.soft(dialog.getByRole("heading", { name: "Profile" }), "a tab you cannot see falls back to Profile").toBeVisible();
    await openSettingsAt(page, "settings/portal-permissions");
    await expect(dialog.getByText("Allow member invites")).toHaveCount(0);
    await page.screenshot({ path: `${process.env.WALK_SHOTS || "test-results"}/walkthrough-S4-perm-hash.png` });
  });
});

test.describe("guest", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("S3 a settings hash on the public knowledge base", async ({ page }) => {
    await page.goto("/help#settings/profile");
    await page.waitForTimeout(2500);
    await page.screenshot({ path: `${process.env.WALK_SHOTS || "test-results"}/walkthrough-S3-guest.png` });
    // The hash opens an empty profile (with rename and photo buttons) plus "Could not load settings".
    await expect.soft(page.getByRole("dialog"), "a guest gets no settings dialog").toHaveCount(0);
  });
});

test.describe("profile", () => {
  test("S5–S12 rename, photo, preferences, theme, layout and password", async ({ api, browser, baseURL }) => {
    const person = await newPerson(api, "example.com", ["HD Customer"], "Profile");
    const page = await pageOf(browser, baseURL!, person.email);
    const dialog = await openSettingsAt(page);

    // S5 rename, Esc cancels
    await dialog.getByRole("button", { name: "Edit name" }).click();
    await dialog.getByRole("textbox").fill("Ignored Name");
    await page.keyboard.press("Escape");
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText(person.fullName, { exact: true })).toBeVisible();
    await dialog.getByRole("button", { name: "Edit name" }).click();
    await dialog.getByRole("textbox").fill("Renamed Walker Person");
    await page.keyboard.press("Enter");
    await expect(toast(page, "Profile updated")).toBeVisible();
    await expect.poll(async () => (await api.get("User", person.email)).first_name).toBe("Renamed");
    expect((await api.get("User", person.email)).last_name).toBe("Walker Person");

    // S6 photo, failing upload first
    const profileSaves: string[] = [];
    page.on("request", (request) => request.url().includes("update_profile") && profileSaves.push(request.postData() || ""));
    await page.route("**/api/method/upload_file", (route) => route.fulfill({ status: 500, body: "{}" }));
    const failing = page.waitForEvent("filechooser");
    await dialog.getByRole("button", { name: "Upload photo" }).click();
    await (await failing).setFiles(PIXEL);
    await expect(toast(page, "Could not upload the image")).toBeVisible();
    await page.unroute("**/api/method/upload_file");
    // `pickImage` catches into `toast.error(...)`, whose id is truthy, so a failed upload still saves `{}` and says "Photo updated".
    expect.soft(profileSaves, "a failed upload saves nothing").toEqual([]);
    const chooser = page.waitForEvent("filechooser");
    await dialog.getByRole("button", { name: "Upload photo" }).click();
    await (await chooser).setFiles(PIXEL);
    await expect(toast(page, "Photo updated")).toBeVisible();
    await expect.poll(async () => (await api.get("User", person.email)).user_image).toContain("/files/");
    const self = await loginContext(baseURL!, person.email, PASSWORD);
    const linked = await self.post("/api/method/helpdesk.api.auth.update_profile", { data: { image: "https://example.com/x.png" } });
    expect(linked.ok()).toBeFalsy();
    expect(await linked.text()).toContain("Please upload the picture");

    // S7 remove photo
    await expect(dialog.getByRole("button", { name: "Change photo" })).toBeVisible();
    await dialog.getByRole("button", { name: "Change photo" }).hover();
    await dialog.getByRole("button", { name: "Remove photo" }).click();
    await expect(toast(page, "Photo removed")).toBeVisible();
    await expect.poll(async () => (await api.get("User", person.email)).user_image).toBeFalsy();

    // S9 timezone
    await dialog.getByRole("button", { name: /Asia\/Kolkata|Select timezone/ }).click();
    await page.getByRole("combobox").last().fill("Europe/Berlin");
    await page.getByRole("option", { name: "Europe/Berlin" }).click();
    await expect(toast(page, "Preferences updated")).toBeVisible();
    await expect.poll(async () => (await api.get("User", person.email)).time_zone).toBe("Europe/Berlin");

    // S8 language
    await dialog.getByRole("button", { name: "Select language" }).click();
    await page.getByRole("combobox").last().fill("Deutsch");
    await page.getByRole("option", { name: /Deutsch/ }).first().click();
    await expect.poll(async () => (await api.get("User", person.email)).language).toBe("de");
    await page.screenshot({ path: `${process.env.WALK_SHOTS || "test-results"}/walkthrough-S8-german.png` });
    const german = page.getByRole("dialog", { name: "Einstellungen" });
    await expect(german.getByRole("heading", { name: "Profil", exact: true })).toBeVisible();
    await german.getByRole("button", { name: /Deutsch/ }).click();
    await page.getByRole("combobox").last().fill("English");
    await page.getByRole("option", { name: "English", exact: true }).click();
    await expect.poll(async () => (await api.get("User", person.email)).language).toBe("en");
    await expect(dialog.getByRole("heading", { name: "Profile" })).toBeVisible();

    // S10 theme
    await choose(page, dialog.getByRole("combobox").first(), "Dark");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await choose(page, dialog.getByRole("combobox").first(), "Light");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");

    // S11 conversation layout
    await choose(page, dialog.getByRole("combobox").nth(1), "Chat");
    expect(await page.evaluate(() => localStorage.getItem("kb:conversation-layout"))).toBe("chat");

    // S12 password
    await dialog.getByRole("button", { name: "Change password" }).click();
    const change = page.getByRole("dialog", { name: "Change Password" });
    const update = change.getByRole("button", { name: "Update" });
    await change.getByPlaceholder("New Password").fill("short");
    await expect(change.getByText("Password must be at least 8 characters")).toBeVisible();
    const fresh = `E2e-Walk-${uid()}!`;
    await change.getByPlaceholder("New Password").fill(fresh);
    await change.getByPlaceholder("Confirm Password").fill(`${fresh}x`);
    await expect(change.getByText("Passwords do not match")).toBeVisible();
    await expect(update).toBeDisabled();
    await change.getByPlaceholder("Confirm Password").fill(fresh);
    await expect(change.getByText("Passwords match")).toBeVisible();
    await update.click();
    await expect(toast(page, "Password updated successfully.")).toBeVisible();
    const relogin = await (await loginContext(baseURL!, person.email, fresh)).get("/api/method/frappe.auth.get_logged_user");
    expect((await relogin.json()).message).toBe(person.email);
  });

  test("H7 the header theme toggle switches at once and keeps it", async ({ api, browser, baseURL }) => {
    const person = await newPerson(api, "example.com", ["HD Customer"], "Theme");
    const page = await pageOf(browser, baseURL!, person.email);
    await page.goto("/help");
    const before = await page.locator("html").getAttribute("data-theme");
    await page.getByRole("button", { name: "Toggle theme" }).click();
    const after = before === "dark" ? "light" : "dark";
    await expect(page.locator("html")).toHaveAttribute("data-theme", after);
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", after);
  });
});

test.describe("organization", () => {
  let restore: () => Promise<unknown>;
  test.beforeAll(async ({ baseURL }) => {
    const { Api } = await import("../../helpers/api");
    const admin = await Api.login(baseURL!, "Administrator", process.env.ADMIN_PASSWORD || "admin");
    restore = await snapshotSettings(admin, PORTAL_TOGGLES);
  });
  test.afterAll(async () => restore?.());

  async function setToggles(api: Api, on: boolean) {
    await api.update("HD Settings", "HD Settings", Object.fromEntries(PORTAL_TOGGLES.map((field) => [field, on ? 1 : 0])));
  }

  test("S13 the organization group follows membership and role", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    const loner = await newPerson(api, "example.com", ["HD Customer"], "Loner");

    const lonerPage = await pageOf(browser, baseURL!, loner.email);
    const lonerDialog = await openSettingsAt(lonerPage);
    await expect(lonerDialog.getByText("Organization", { exact: true })).toHaveCount(0);

    const memberDialog = await openSettingsAt(await pageOf(browser, baseURL!, org.member.email));
    await expect(memberDialog.getByRole("tab", { name: "View Organization" })).toBeVisible();

    const managerDialog = await openSettingsAt(await pageOf(browser, baseURL!, org.manager.email));
    await expect(managerDialog.getByRole("tab", { name: "Manage Organization" })).toBeVisible();
  });

  test("S14–S16 one organization opens directly; several give a searchable grid", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    const page = await pageOf(browser, baseURL!, org.member.email);
    let dialog = await openSettingsAt(page);
    await dialog.getByRole("tab", { name: "View Organization" }).click();
    await expect(dialog.getByText(org.name, { exact: true })).toBeVisible();
    // S16 identity: email • domain • country, name not editable
    await expect(dialog.getByText(org.domain, { exact: true })).toBeVisible();
    await expect(dialog.getByText("India")).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Edit name" })).toHaveCount(0);
    // S14 no back chevron
    await expect(dialog.locator('[data-component-id="kb_settings-organization-back"]')).toBeHidden();

    // S15 a second organization
    const second = await api.insert("HD Customer", {
      customer_name: `E2E Org ${uid()}`,
      domain: `second-${uid()}.test`,
      contacts: [{ contact_name: org.member.contact, is_manager: 0 }],
    });
    dialog = await openSettingsAt(page, "settings/members");
    await expect(dialog.getByRole("button", { name: new RegExp(org.name) })).toBeVisible();
    const secondCard = dialog.getByRole("button", { name: new RegExp(second.name) });
    await expect(secondCard).toContainText("Member");
    await expect(secondCard).toContainText("0 tickets");
    await expect(secondCard).toContainText("1 member");
    await dialog.getByPlaceholder("Search").fill(second.domain);
    await expect(dialog.getByRole("button", { name: new RegExp(org.name) })).toHaveCount(0);
    await dialog.getByPlaceholder("Search").fill("zzz-nothing");
    await expect(dialog.getByText("No organizations found")).toBeVisible();
    await dialog.getByPlaceholder("Search").fill("");
    await dialog.getByRole("button", { name: new RegExp(org.name) }).press("Enter");
    await expect(page).toHaveURL(new RegExp(`#settings/members/${encodeURIComponent(org.name)}$`));
    await dialog.locator('[data-component-id="kb_settings-organization-back"]').click();
    await expect(dialog.getByRole("button", { name: new RegExp(second.name) })).toBeVisible();
  });

  test("S17 logo edits follow the setting and the manager role", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, false);
    const managerPage = await pageOf(browser, baseURL!, org.manager.email);
    let dialog = await openOrgScreen(managerPage, org.name);
    await expect(dialog.getByRole("button", { name: "Upload photo" })).toHaveCount(0);
    const managerApi = await loginContext(baseURL!, org.manager.email, PASSWORD);
    const refused = await managerApi.post("/api/method/helpdesk.api.organization.update_organization_image", { data: { customer: org.name, image: "" } });
    expect(await refused.text()).toContain("does not allow customers to change their organization");

    await setToggles(api, true);
    dialog = await openOrgScreen(managerPage, org.name);
    const chooser = managerPage.waitForEvent("filechooser");
    await dialog.getByRole("button", { name: "Upload photo" }).click();
    await (await chooser).setFiles(PIXEL);
    await expect(toast(managerPage, "Logo updated")).toBeVisible();
    await expect.poll(async () => (await api.get("HD Customer", org.name)).image).toContain("/files/");
    await dialog.getByRole("button", { name: "Change photo" }).hover();
    await dialog.getByRole("button", { name: "Remove photo" }).click();
    await expect(toast(managerPage, "Logo removed")).toBeVisible();
    await expect.poll(async () => (await api.get("HD Customer", org.name)).image).toBeFalsy();

    const memberApi = await loginContext(baseURL!, org.member.email, PASSWORD);
    const notManager = await memberApi.post("/api/method/helpdesk.api.organization.update_organization_image", { data: { customer: org.name, image: "" } });
    expect(await notManager.text()).toContain(`Only a manager of ${org.name} can do this`);
    const memberDialog = await openOrgScreen(await pageOf(browser, baseURL!, org.member.email), org.name);
    await expect(memberDialog.getByRole("button", { name: "Upload photo" })).toHaveCount(0);
  });

  test("S18 S19 S27 member list: order, search, filters, last seen, member view", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, true);
    const page = await pageOf(browser, baseURL!, org.manager.email);
    const dialog = await openOrgScreen(page, org.name);
    const names = await dialog.locator("div.grid div.text-base-medium").allInnerTexts();
    expect(names.map((name) => name.split("\n")[0].replace(/You$/, "").trim())).toEqual([
      org.owner.fullName,
      org.manager.fullName,
      org.member.fullName,
    ]);
    await expect(memberRow(dialog, org.manager.email)).toContainText("You");
    // S19 last seen: managers only, "Never" for someone who never signed in
    await expect(dialog.getByText("Last seen")).toBeVisible();
    await expect(memberRow(dialog, org.owner.email)).toContainText("Never");

    await dialog.getByPlaceholder("Search").fill(org.member.email);
    await expect(memberRows(dialog)).toHaveCount(1);
    await expect(memberRows(dialog)).toContainText(org.member.email);
    await dialog.getByPlaceholder("Search").fill("zzz-nobody");
    await expect(dialog.getByText("No members match this filter.")).toBeVisible();
    await dialog.getByPlaceholder("Search").fill("");
    const roleFilter = dialog.getByRole("combobox").last();
    await roleFilter.click();
    await expect(page.getByRole("option")).toHaveText(["All", "Manager", "Member"]);
    await page.getByRole("option", { name: "Manager", exact: true }).click();
    // The owner is its own role, so the Manager filter leaves it out.
    await expect(memberRows(dialog)).toHaveCount(1);
    await expect(memberRows(dialog)).toContainText(org.manager.email);
    await expect(memberRow(dialog, org.member.email)).toHaveCount(0);

    // S19 a phone drops the Last seen column
    const phone = await pageOf(browser, baseURL!, org.manager.email, PASSWORD, { width: 390, height: 844 });
    const phoneDialog = await openOrgScreen(phone, org.name);
    await expect(memberRows(phoneDialog)).toHaveCount(3);
    await expect(phoneDialog.getByText("Last seen")).toBeHidden();
    await phone.screenshot({ path: `${process.env.WALK_SHOTS || "test-results"}/walkthrough-S19-phone.png` });
    // Not asserted: frappe-ui's SettingsDialog is `w-screen` inside Dialog's `px-4` wrapper, so a phone
    // loses its right 16px on the desk too. Upstream fix; assert the dialog's right edge <= 390 once it lands.

    // S27 member view
    const memberPage = await pageOf(browser, baseURL!, org.member.email);
    const memberDialog = await openOrgScreen(memberPage, org.name);
    await expect(memberRows(memberDialog)).toHaveCount(3);
    await expect(memberDialog.getByRole("button", { name: "Invite people" })).toHaveCount(0);
    await expect(memberDialog.getByRole("button", { name: "Member actions" })).toHaveCount(0);
    await expect(memberDialog.getByText("Last seen")).toHaveCount(0);
    await expect(memberDialog.locator("button").filter({ hasText: /^Manager$/ })).toHaveCount(0);
    const memberApi = await loginContext(baseURL!, org.member.email, PASSWORD);
    for (const [method, args] of [
      ["invite_members", { emails: [`x-${uid()}@${org.domain}`], role: "HD Customer" }],
      ["update_member_role", { contact: org.manager.contact, is_manager: 0 }],
      ["remove_member", { contact: org.manager.contact }],
    ] as const) {
      const response = await memberApi.post(`/api/method/helpdesk.api.organization.${method}`, { data: { customer: org.name, ...args } });
      expect(await response.text(), method).toContain(`Only a manager of ${org.name} can do this`);
    }
  });

  test("S20 S21 role changes and removal", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, false);
    const page = await pageOf(browser, baseURL!, org.manager.email);
    let dialog = await openOrgScreen(page, org.name);
    await expect(memberRow(dialog, org.member.email).getByRole("button")).toHaveCount(0);
    await expect(dialog.getByRole("button", { name: "Member actions" })).toHaveCount(0);

    await setToggles(api, true);
    dialog = await openOrgScreen(page, org.name);
    // never for the owner or yourself
    await expect(memberRow(dialog, org.owner.email).getByRole("button")).toHaveCount(0);
    await expect(memberRow(dialog, org.manager.email).getByRole("button")).toHaveCount(0);

    await memberRow(dialog, org.member.email).getByRole("button", { name: "Member", exact: true }).click();
    await page.getByRole("menuitem", { name: "Manager" }).click();
    await confirm(page, "Grant manager access", "Confirm");
    await expect(toast(page, "Role updated")).toBeVisible();
    await expect
      .poll(async () => (await api.get("User", org.member.email)).roles.map((row: any) => row.role))
      .toContain("HD Customer Manager");
    await memberRow(dialog, org.member.email).getByRole("button", { name: "Manager", exact: true }).click();
    await page.getByRole("menuitem", { name: "Member" }).click();
    await confirm(page, "Revoke manager access", "Confirm");
    await expect
      .poll(async () => (await api.get("User", org.member.email)).roles.map((row: any) => row.role))
      .not.toContain("HD Customer Manager");

    const managerApi = await loginContext(baseURL!, org.manager.email, PASSWORD);
    for (const contact of [org.owner.contact, org.manager.contact]) {
      const response = await managerApi.post("/api/method/helpdesk.api.organization.remove_member", { data: { customer: org.name, contact } });
      expect(response.ok(), contact).toBeFalsy();
    }

    await memberRow(dialog, org.member.email).getByRole("button", { name: "Member actions" }).click();
    await page.getByRole("menuitem", { name: "Remove from organization" }).click();
    await confirm(page, "Remove member", "Remove");
    await expect(toast(page, "Member removed")).toBeVisible();
    await expect(memberRow(dialog, org.member.email)).toHaveCount(0);
    const contacts = (await api.get("HD Customer", org.name)).contacts.map((row: any) => row.contact_name);
    expect(contacts).not.toContain(org.member.contact);
  });

  test("S22–S26 invites: screen, suggestions, errors, pending rows, cancel", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    // S23 a login-holding contact on the domain who is not a member
    const outsider = await newPerson(api, org.domain, ["HD Customer"], "Outsider");
    await setToggles(api, true);
    const page = await pageOf(browser, baseURL!, org.manager.email);
    const dialog = await openOrgScreen(page, org.name);

    await dialog.getByRole("button", { name: "Invite people" }).click();
    await expect(page).toHaveURL(/\/invite$/);
    await expect(dialog.getByText("Invite by email")).toBeVisible();
    // S24 no emails
    await dialog.getByRole("button", { name: "Send Invite" }).click();
    await expect(toast(page, "Please enter an email address")).toBeVisible();
    // S23 suggestion
    const input = dialog.getByPlaceholder("Separate multiple emails with commas");
    await input.click();
    await input.pressSequentially("Outsider");
    await expect(page.getByRole("option", { name: new RegExp(outsider.fullName) })).toBeVisible();
    await input.fill("");
    // S22 comma and semicolon split into chips
    const first = `invitee-a-${uid()}@${org.domain}`;
    const second = `invitee-b-${uid()}@${org.domain}`;
    await input.pressSequentially(`${first},`);
    await page.keyboard.type(`${second};`);
    await expect(dialog.getByText(first)).toBeVisible();
    await expect(dialog.getByText(second)).toBeVisible();
    await choose(page, dialog.locator('[data-component-id="kb_settings-invite-role"]'), "Manager");
    await dialog.getByRole("button", { name: "Send Invite" }).click();
    await expect(page.getByText(/Invitations sent|Invitations created, but the emails could not be sent/).first()).toBeVisible();
    const invitations = await api.list("User Invitation", { filters: { customer: org.name }, fields: ["email", "status"] });
    expect(invitations.map((row) => row.email).sort()).toEqual([first, second].sort());
    await expect(page).not.toHaveURL(/\/invite$/);

    // S25 pending rows
    const row = memberRow(dialog, first);
    await expect(row).toContainText("by you");
    await expect(row).toContainText("Pending");
    await expect(row).toContainText("Manager");
    // S26 no resend
    await expect(dialog.getByRole("button", { name: /resend/i })).toHaveCount(0);
    await dialog.getByRole("combobox").last().click();
    await expect(page.getByRole("option", { name: "Invited" })).toBeVisible();
    await page.keyboard.press("Escape");
    await row.getByRole("button", { name: "Cancel invitation" }).click();
    await confirm(page, "Cancel invitation", "Cancel invitation");
    await expect(page.getByText(/Invitation cancelled/).first()).toBeVisible();
    await expect(dialog.getByText(first)).toHaveCount(0);

    // S22 the back chevron cancels the invite screen
    await dialog.getByRole("button", { name: "Invite people" }).click();
    await expect(page).toHaveURL(/\/invite$/);
    await dialog.locator('[data-component-id="kb_settings-invite-back"]').click();
    await expect(page).not.toHaveURL(/\/invite$/);

    // S24 more than 20
    const managerApi = await loginContext(baseURL!, org.manager.email, PASSWORD);
    const tooMany = Array.from({ length: 21 }, (_, n) => `many-${n}-${uid()}@${org.domain}`);
    const response = await managerApi.post("/api/method/helpdesk.api.organization.invite_members", {
      data: { customer: org.name, emails: tooMany, role: "HD Customer" },
    });
    expect(await response.text()).toContain("You can invite up to 20 people at a time");

    // S23 a shared mail domain suggests no one
    await api.update("HD Customer", org.name, { domain: "gmail.com" });
    const suggestions = await managerApi.get(`/api/method/helpdesk.api.organization.get_invitable_contacts?customer=${encodeURIComponent(org.name)}`);
    expect((await suggestions.json()).message).toEqual([]);
  });

  test("S2 a deep link opens the invite screen", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, true);
    const page = await pageOf(browser, baseURL!, org.manager.email);
    await page.goto(`/help#settings/members/${org.name}/invite`);
    const dialog = page.getByRole("dialog", { name: "Settings" });
    await expect(dialog.getByText("Invite by email")).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Send Invite" })).toBeVisible();
  });

  test("S24 invites are rate limited per user", async ({ api, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, true);
    const managerApi = await loginContext(baseURL!, org.manager.email, PASSWORD);
    const statuses: number[] = [];
    for (let n = 0; n < 11; n++) {
      const response = await managerApi.post("/api/method/helpdesk.api.organization.invite_members", {
        data: { customer: org.name, emails: [`rate-${n}-${uid()}@${org.domain}`], role: "HD Customer" },
      });
      statuses.push(response.status());
    }
    expect(statuses.slice(0, 10).every((status) => status !== 429)).toBeTruthy();
    expect(statuses[10]).toBe(429);
  });

  test("S28 tickets tab: newest first, search, open, member sees own only", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    const managerApi = await loginContext(baseURL!, org.manager.email, PASSWORD);
    const memberApi = await loginContext(baseURL!, org.member.email, PASSWORD);
    const raise = async (context: typeof managerApi, subject: string) => {
      const response = await context.post("/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new", {
        data: { doc: { subject, description: `<p>${subject}</p>`, customer: org.name } },
      });
      expect(response.ok(), await response.text()).toBeTruthy();
      return (await response.json()).message;
    };
    const mine = await raise(managerApi, `Org manager ticket ${uid()}`);
    const theirs = await raise(memberApi, `Org member ticket ${uid()}`);
    for (const ticket of [mine, theirs]) await api.update("HD Ticket", ticket.name, { customer: org.name });

    const page = await pageOf(browser, baseURL!, org.manager.email);
    const dialog = await openOrgScreen(page, org.name);
    await dialog.getByRole("tab", { name: "Tickets" }).click();
    const links = dialog.getByRole("link");
    await expect(links).toHaveCount(2);
    await expect(links.first()).toContainText(`#${theirs.name}`);
    await dialog.getByPlaceholder("Search").last().fill("member ticket");
    await expect(links).toHaveCount(1);
    await dialog.getByPlaceholder("Search").last().fill("zzz-none");
    await expect(dialog.getByText("No tickets match your search.")).toBeVisible();
    await dialog.getByPlaceholder("Search").last().fill("");
    await links.first().click();
    await expect(page).toHaveURL(new RegExp(`/help/tickets/${theirs.name}$`));

    const memberDialog = await openOrgScreen(await pageOf(browser, baseURL!, org.member.email), org.name);
    await memberDialog.getByRole("tab", { name: "Tickets" }).click();
    await expect(memberDialog.getByRole("link")).toHaveCount(1);
    await expect(memberDialog.getByRole("link")).toContainText(`#${theirs.name}`);

    const empty = await newOrg(api);
    const emptyDialog = await openOrgScreen(await pageOf(browser, baseURL!, empty.member.email), empty.name);
    await emptyDialog.getByRole("tab", { name: "Tickets" }).click();
    await expect(emptyDialog.getByText("No tickets from this organization yet.")).toBeVisible();
  });
});

test.describe("app settings", () => {
  test("S29 the App Settings group shows only to settings editors", async ({ browser, baseURL, pageAs }) => {
    for (const [key, shown] of [
      ["admin", true],
      ["manager", true],
      ["agent", false],
      ["customer", false],
      ["customerManager", false],
    ] as const) {
      const page = await pageAs(key);
      const dialog = await openSettingsAt(page);
      await expect(dialog.getByRole("tab", { name: "Portal Permissions" }), key).toHaveCount(shown ? 1 : 0);
    }
  });

  test("S36 portal permission toggles save at once", async ({ api, pageAs }) => {
    const restore = await snapshotSettings(api, PORTAL_TOGGLES);
    const signup = (await api.get("Website Settings", "Website Settings")).disable_signup;
    try {
      const page = await pageAs("admin");
      const dialog = await openSettingsAt(page, "settings/portal-permissions");
      await expect(dialog.getByText("Disable signup")).toBeVisible();
      const labels = ["Allow member invites", "Allow role changes", "Allow member removal", "Allow organization edits"];
      for (const [index, label] of labels.entries()) {
        const row = dialog.locator("div.flex.items-center.justify-between").filter({ hasText: label });
        const before = (await api.get("HD Settings", "HD Settings"))[PORTAL_TOGGLES[index]];
        await row.getByRole("switch").click();
        await expect(toast(page, "Settings updated")).toBeVisible();
        await expect.poll(async () => (await api.get("HD Settings", "HD Settings"))[PORTAL_TOGGLES[index]]).toBe(before ? 0 : 1);
      }
      const managerDialog = await openSettingsAt(await pageAs("manager"), "settings/portal-permissions");
      await expect(managerDialog.getByText("Allow member invites")).toBeVisible();
      await expect(managerDialog.getByText("Disable signup")).toHaveCount(0);
    } finally {
      await restore();
      await api.update("Website Settings", "Website Settings", { disable_signup: signup });
    }
  });

  test("S35 leaving the Knowledge Base tab with unsaved changes asks first", async ({ api, pageAs }) => {
    const before = await api.get("HD Settings", "HD Settings");
    const page = await pageAs("admin");
    const dialog = await openSettingsAt(page, "settings/knowledge-base");
    const row = dialog.locator("div").filter({ hasText: /^Allow guests to vote/ }).last();
    await dialog.getByRole("switch").nth(1).click();
    await expect(dialog.getByText("Unsaved", { exact: true })).toBeVisible();
    // closing is blocked while dirty
    await page.keyboard.press("Escape");
    await expect(dialog).toBeVisible();
    await dialog.getByRole("tab", { name: /Profile/ }).click();
    await confirm(page, "Unsaved changes", "Confirm");
    await expect(dialog.getByRole("heading", { name: "Profile" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    const after = await api.get("HD Settings", "HD Settings");
    expect(after.allow_anonymous_article_voting).toBe(before.allow_anonymous_article_voting);
    expect(after.public_knowledge_base).toBe(before.public_knowledge_base);
    void row;
  });

  test("S37 an agent in an organization sees it and counts as its manager", async ({ api, browser, baseURL }) => {
    const restore = await snapshotSettings(api, PORTAL_TOGGLES);
    try {
      const org = await newOrg(api);
      const agent = await newPerson(api, org.domain, ["Agent"], "Agent");
      await api.update("User", agent.email, { user_type: "System User" });
      await api.insert("HD Agent", { user: agent.email, agent_name: agent.fullName, is_active: 1 });
      const plain = await newPerson(api, "example.com", ["Agent"], "Plainagent");
      await api.update("User", plain.email, { user_type: "System User" });
      await api.insert("HD Agent", { user: plain.email, agent_name: plain.fullName, is_active: 1 });
      const customer = await api.get("HD Customer", org.name);
      await api.update("HD Customer", org.name, {
        contacts: [...customer.contacts.map((row: any) => ({ contact_name: row.contact_name, is_manager: row.is_manager })), { contact_name: agent.contact, is_manager: 0 }],
      });
      await api.update("HD Settings", "HD Settings", { allow_customer_managers_to_invite: 1 });

      const page = await pageOf(browser, baseURL!, agent.email);
      const dialog = await openSettingsAt(page);
      const tab = dialog.getByRole("tab", { name: /Organization/ });
      await expect(tab).toBeVisible();
      await tab.click();
      await expect(dialog.getByText(org.name, { exact: true })).toBeVisible();
      // A plain Agent has no HD Customer write, so it is a member here.
      await expect(dialog.getByRole("button", { name: "Invite people" })).toHaveCount(0);

      // With HD Customer write (Agent Manager) the agent manages it.
      await api.update("User", agent.email, { roles: [{ role: "Agent" }, { role: "Agent Manager" }] });
      await page.reload();
      await dialog.getByRole("tab", { name: /Organization/ }).click();
      await expect(dialog.getByRole("button", { name: "Invite people" })).toBeVisible();
      // `_get_organizations` labels by membership only, so the nav still reads View.
      await expect.soft(dialog.getByRole("tab", { name: /Organization/ }), "the label follows manage rights").toHaveText(/Manage Organization/);

      const plainDialog = await openSettingsAt(await pageOf(browser, baseURL!, plain.email));
      await expect(plainDialog.getByRole("tab", { name: /Organization/ })).toHaveCount(0);
    } finally {
      await restore();
    }
  });
});

void expectDenied;
