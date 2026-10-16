import type { BrowserContext, Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expectDenied } from "../../helpers/api";
import { expect, test, uid } from "../../helpers/fixtures";
import { PASSWORD } from "../../helpers/personas";
import { loginContext } from "../../helpers/portal";
import { snapshotSettings } from "../../helpers/settings";

// The portal's settings dialog (`kb_settings`), driven as throwaway customers so the shared personas never change.

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

async function openSettingsAt(page: Page, hash = "settings/profile") {
  await page.goto(`/help#${hash}`);
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await expect(dialog).toBeVisible();
  return dialog;
}

async function confirm(page: Page, title: string, button: string) {
  const dialog = page.getByRole("dialog", { name: title });
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: button, exact: true }).click();
}

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
});

test.describe("app settings", () => {

  test("S35 leaving the Knowledge Base tab with unsaved changes asks first", async ({ api, pageAs }) => {
    const before = await api.get("HD Settings", "HD Settings");
    const page = await pageAs("admin");
    const dialog = await openSettingsAt(page, "settings/knowledge-base");
    // Switches save at once, so the banner makes the edit.
    await dialog.getByRole("radio", { name: before.banner_preset === "Blue" ? "None" : "Blue" }).click();
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
    expect(after.banner_preset).toBe(before.banner_preset);
  });
});

void expectDenied;
