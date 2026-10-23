import type { Browser, BrowserContext, Locator, Page } from "@playwright/test";
import { Api } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { PASSWORD } from "../../helpers/personas";
import { loginContext } from "../../helpers/portal";
import { snapshotSettings } from "../../helpers/settings";
import { siteHeader } from "../../helpers/site";
import { setHelpdeskSetting } from "../../helpers/ticket";

// Throwaway customers, so the shared personas never change.

const PIXEL = "e2e/fixtures/pixel.png";
const PORTAL_TOGGLES = [
  "allow_customer_managers_to_invite",
  "allow_customer_managers_to_manage_organization",
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

async function openSettingsAt(page: Page, path = "settings/profile") {
  await page.goto(`/help/${path}`);
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

async function changeRole(page: Page, row: Locator, role: string) {
  await row.getByRole("button", { name: "Member actions" }).click();
  await page.getByRole("menuitem", { name: "Change role" }).hover();
  await page.getByRole("menuitem", { name: role, exact: true }).click();
}

async function confirm(page: Page, title: string, button: string) {
  const dialog = page.getByRole("dialog", { name: title });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: button, exact: true }).click();
}

test.describe("dialog", () => {
  usePersona("customerManager");

  test("S1 opens from the menu, follows each screen in the path, and closes", async ({ page }) => {
    await page.goto("/help");
    await page.getByRole("button", { name: /Helpdesk/ }).first().click();
    await page.getByRole("menuitem", { name: "Settings" }).click();
    const dialog = page.getByRole("dialog", { name: "Settings" });
    await expect(dialog.getByRole("heading", { name: "Profile" })).toBeVisible();
    await expect(page).toHaveURL(/\/help\/settings\/profile$/);

    await dialog.getByRole("tab", { name: "Manage Organization" }).click();
    await expect(page).toHaveURL(/\/help\/settings\/members\/E2E%20Customer%20Org$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/help\/settings\/profile$/);
    await expect(dialog.getByRole("heading", { name: "Profile" })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(page).not.toHaveURL(/\/settings/);

    await openSettingsAt(page);
    await page.mouse.click(5, 300);
    await expect(dialog).toBeHidden();
    await expect(page).not.toHaveURL(/\/settings/);
  });

  test("S4 a customer's path to an admin tab shows nothing broken", async ({ page }) => {
    const dialog = await openSettingsAt(page, "settings/knowledge-base");
    await expect(dialog.getByRole("tab", { name: "Knowledge Base" })).toHaveCount(0);
    await expect(dialog.getByText("Make knowledge base public")).toHaveCount(0);
    await expect(dialog.getByRole("heading", { name: "Profile" }), "a tab you cannot see falls back to Profile").toBeVisible();
    await openSettingsAt(page, "settings/portal-settings");
    await expect(dialog.getByText("Allow member invites")).toHaveCount(0);
  });

  test("an old #settings link moves to the settings path", async ({ page }) => {
    await page.goto("/help/my-tickets#settings/members/E2E Customer Org");
    await expect(page).toHaveURL(/\/help\/my-tickets\/settings\/members\/E2E%20Customer%20Org$/);
    await expect(page.getByRole("dialog", { name: "Settings" }).getByText("E2E Customer Org", { exact: true })).toBeVisible();
  });
});

test.describe("guest", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("S3 a settings path on the public knowledge base", async ({ page, api }) => {
    const restore = await setHelpdeskSetting(api, "public_knowledge_base", 1);
    try {
      await page.goto("/help/settings/profile");
      await expect(page.getByRole("heading", { name: "Here's what might help" })).toBeVisible();
      await expect(page).toHaveURL(/\/help\/?$/);
      await page.waitForLoadState("networkidle");
      await expect(page.getByRole("dialog"), "a guest gets no settings dialog").toHaveCount(0);
    } finally {
      await restore();
    }
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
    expect(profileSaves, "a failed upload saves nothing").toEqual([]);
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
    await expect.poll(async () => (await api.get("User", person.email)).time_zone).toBe("Europe/Berlin");
    await expect(dialog.getByRole("button", { name: /Europe\/Berlin/ })).toBeVisible();

    // S8 language
    await dialog.getByRole("button", { name: "Select language" }).click();
    await page.getByRole("combobox").last().fill("Deutsch");
    await page.getByRole("option", { name: /Deutsch/ }).first().click();
    await expect.poll(async () => (await api.get("User", person.email)).language).toBe("de");
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
    // S16 identity; name not editable
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
    await expect(page).toHaveURL(new RegExp(`/settings/members/${encodeURIComponent(org.name)}$`));
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
    const refused = await managerApi.post("/api/method/helpdesk.api.customer.update_organization_image", { data: { customer: org.name, image: "" } });
    expect(await refused.text()).toContain("You are not permitted to change the organization's logo");

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
    const notManager = await memberApi.post("/api/method/helpdesk.api.customer.update_organization_image", { data: { customer: org.name, image: "" } });
    expect(await notManager.text()).toContain(`You are not permitted to manage ${org.name}`);
    const memberDialog = await openOrgScreen(await pageOf(browser, baseURL!, org.member.email), org.name);
    await expect(memberDialog.getByRole("button", { name: "Upload photo" })).toHaveCount(0);
  });

  test("S18 S19 S27 member list: order, search, filters, last seen, member view", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, true);
    const page = await pageOf(browser, baseURL!, org.manager.email);
    const dialog = await openOrgScreen(page, org.name);
    const names = await dialog.locator("div.grid div.text-base-medium").allInnerTexts();
    // you first, then by role
    expect(names.map((name) => name.split("\n")[0].trim())).toEqual([
      org.manager.fullName,
      org.owner.fullName,
      org.member.fullName,
    ]);
    // S19 last seen: managers only
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
    // Not asserted: frappe-ui's SettingsDialog overflows a phone by 16px (upstream bug).

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
      ["invite_members", { emails: [`x-${uid()}@${org.domain}`], is_manager: false }],
      ["update_member_role", { contact: org.manager.contact, is_manager: 0 }],
      ["remove_member", { contact: org.manager.contact }],
    ] as const) {
      const response = await memberApi.post(`/api/method/helpdesk.api.customer.${method}`, { data: { customer: org.name, ...args } });
      expect(await response.text(), method).toContain(`You are not permitted to manage ${org.name}`);
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

    await changeRole(page, memberRow(dialog, org.member.email), "Manager");
    await confirm(page, "Grant manager access", "Confirm");
    await expect(toast(page, "Role updated")).toBeVisible();
    await expect
      .poll(async () => (await api.get("User", org.member.email)).roles.map((row: any) => row.role))
      .toContain("HD Customer Manager");
    await changeRole(page, memberRow(dialog, org.member.email), "Member");
    await confirm(page, "Revoke manager access", "Confirm");
    await expect
      .poll(async () => (await api.get("User", org.member.email)).roles.map((row: any) => row.role))
      .not.toContain("HD Customer Manager");

    const managerApi = await loginContext(baseURL!, org.manager.email, PASSWORD);
    for (const contact of [org.owner.contact, org.manager.contact]) {
      const response = await managerApi.post("/api/method/helpdesk.api.customer.remove_member", { data: { customer: org.name, contact } });
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

  test("S22–S26 invites: screen, errors, pending rows, cancel", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, true);
    const page = await pageOf(browser, baseURL!, org.manager.email);
    const dialog = await openOrgScreen(page, org.name);

    await dialog.getByRole("button", { name: "Invite people" }).click();
    await expect(page).toHaveURL(/\/invite$/);
    await expect(dialog.getByText("Invite by email")).toBeVisible();
    // S24 no emails, nothing to send
    await expect(dialog.getByRole("button", { name: "Send Invites" })).toBeDisabled();
    const input = dialog.getByPlaceholder("user1@example.com, user2@example.com, ...");
    await input.click();
    // S22 Enter adds each address as a chip
    const first = `invitee-a-${uid()}@${org.domain}`;
    const second = `invitee-b-${uid()}@${org.domain}`;
    // Enter picks the highlighted row, which offers the typed address.
    const addEmail = async (email: string) => {
      await page.keyboard.type(email);
      await expect(page.getByRole("option", { name: email }).first()).toBeVisible();
      await page.keyboard.press("Enter");
    };
    await addEmail(first);
    await addEmail(second);
    await expect(dialog.getByText(first)).toBeVisible();
    await expect(dialog.getByText(second)).toBeVisible();
    await choose(page, dialog.locator('[data-component-id="kb_settings-invite-role"]'), "Manager");
    await dialog.getByRole("button", { name: "Send Invites" }).click();
    await expect(page.getByText(/invited successfully|Invitations created, but the emails could not be sent/).first()).toBeVisible();
    const invitations = await api.list("User Invitation", { filters: { customer: org.name }, fields: ["email", "status"] });
    expect(invitations.map((row) => row.email).sort()).toEqual([first, second].sort());
    await expect(page).not.toHaveURL(/\/invite$/);

    // S25 pending rows
    const row = memberRow(dialog, first);
    await expect(row).toContainText("by you");
    await expect(row).toContainText("Pending");
    await expect(row).toContainText("Manager");
    // S22 an already invited email is skipped, not refused
    await dialog.getByRole("button", { name: "Invite people" }).click();
    await input.click();
    await addEmail(first);
    await dialog.getByRole("button", { name: "Send Invites" }).click();
    await expect(toast(page, `Could not invite ${first}`)).toBeVisible();
    await expect(page).not.toHaveURL(/\/invite$/);
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
    const response = await managerApi.post("/api/method/helpdesk.api.customer.invite_members", {
      data: { customer: org.name, emails: tooMany, is_manager: false },
    });
    expect(await response.text()).toContain("You can invite up to 20 people at a time");
  });

  test("S2 a deep link opens the invite screen", async ({ api, browser, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, true);
    const page = await pageOf(browser, baseURL!, org.manager.email);
    await page.goto(`/help/settings/members/${org.name}/invite`);
    const dialog = page.getByRole("dialog", { name: "Settings" });
    await expect(dialog.getByText("Invite by email")).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Send Invites" })).toBeVisible();
  });

  test("S24 invites are rate limited per user", async ({ api, baseURL }) => {
    const org = await newOrg(api);
    await setToggles(api, true);
    const managerApi = await loginContext(baseURL!, org.manager.email, PASSWORD);
    const statuses: number[] = [];
    for (let n = 0; n < 11; n++) {
      const response = await managerApi.post("/api/method/helpdesk.api.customer.invite_members", {
        data: { customer: org.name, emails: [`rate-${n}-${uid()}@${org.domain}`], is_manager: false },
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
    await expect(page).toHaveURL(new RegExp(`/help/my-tickets/${theirs.name}$`));

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

test.describe("customer portal settings", () => {
  test("S29 the Customer Portal group shows only to settings editors", async ({ pageAs }) => {
    for (const [key, shown] of [
      ["admin", true],
      ["manager", true],
      ["agent", false],
      ["customer", false],
      ["customerManager", false],
    ] as const) {
      const page = await pageAs(key);
      const dialog = await openSettingsAt(page);
      await expect(dialog.getByRole("tab", { name: "Portal Settings" }), key).toHaveCount(shown ? 1 : 0);
    }
  });

  test("S36 portal permission toggles save at once", async ({ api, pageAs }) => {
    const restore = await snapshotSettings(api, PORTAL_TOGGLES);
    const signup = (await api.get("Website Settings", "Website Settings")).disable_signup;
    try {
      const page = await pageAs("admin");
      const dialog = await openSettingsAt(page, "settings/portal-settings");
      await expect(dialog.getByText("Allow signup")).toBeVisible();
      const labels = ["Allow member invites", "Allow organization management"];
      for (const [index, label] of labels.entries()) {
        const before = (await api.get("HD Settings", "HD Settings"))[PORTAL_TOGGLES[index]];
        await dialog.getByRole("switch", { name: label }).click();
        await expect(toast(page, "Settings updated")).toBeVisible();
        await expect.poll(async () => (await api.get("HD Settings", "HD Settings"))[PORTAL_TOGGLES[index]]).toBe(before ? 0 : 1);
      }
      const managerDialog = await openSettingsAt(await pageAs("manager"), "settings/portal-settings");
      await expect(managerDialog.getByText("Allow member invites")).toBeVisible();
      await expect(managerDialog.getByText("Allow signup")).toHaveCount(0);
    } finally {
      await restore();
      await api.update("Website Settings", "Website Settings", { disable_signup: signup });
    }
  });

  test("S35 leaving the Knowledge Base tab with unsaved changes asks first", async ({ api, pageAs }) => {
    const before = await api.get("HD Settings", "HD Settings");
    const page = await pageAs("admin");
    const dialog = await openSettingsAt(page, "settings/knowledge-base");
    // Switches save at once, so the banner makes the edit.
    await dialog.getByRole("radio", { name: before.banner_preset === "Blue" ? "None" : "Blue" }).click();
    await expect(dialog.getByText("Unsaved", { exact: true })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeVisible();
    await dialog.getByRole("tab", { name: /Profile/ }).click();
    await confirm(page, "Unsaved changes", "Confirm");
    await expect(dialog.getByRole("heading", { name: "Profile" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    const after = await api.get("HD Settings", "HD Settings");
    expect(after.banner_preset).toBe(before.banner_preset);
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
      await expect(dialog.getByRole("tab", { name: /Organization/ }), "the label follows manage rights").toHaveText(/Manage Organization/);

      const plainDialog = await openSettingsAt(await pageOf(browser, baseURL!, plain.email));
      await expect(plainDialog.getByRole("tab", { name: /Organization/ })).toHaveCount(0);
    } finally {
      await restore();
    }
  });
});
