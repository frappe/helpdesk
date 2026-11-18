import type { Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../helpers/fixtures";
import { PASSWORD } from "../helpers/personas";
import { snapshotSettings } from "../helpers/settings";

usePersona("admin");

test.describe("first-run setup", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("a new site's admin names the company, skips email, invites an agent and lands on the desk", async ({
    page,
    api,
  }) => {
    const restore = await snapshotSettings(api, ["setup_complete", "brand_name", "brand_logo"]);
    try {
      const admin = `e2e-setup-${uid()}@example.com`;
      await api.insert("User", {
        email: admin,
        first_name: "Setup",
        send_welcome_email: 0,
        roles: [{ role: "System Manager" }],
        new_password: PASSWORD,
      });
      await api.update("HD Settings", "HD Settings", { setup_complete: 0 });
      await page.request.post("/api/method/login", { form: { usr: admin, pwd: PASSWORD } });

      await page.goto("/helpdesk/tickets");
      const pending = await page.evaluate(() => (window as any).setup_pending);
      test.skip(!pending, "Needs a Frappe Cloud v2 site: pilot_endpoint and pilot_auth_token in site config");
      await expect(page).toHaveURL(/\/helpdesk\/setup$/);

      await setPasswordIfAsked(page);

      const company = `Acme ${uid()}`;
      await expect(page.getByRole("heading", { name: "What's your company called?" })).toBeVisible();
      await page.getByLabel("Company or team name").fill(company);
      await page.getByRole("button", { name: "Continue" }).click();
      await expect.poll(async () => (await api.get("HD Settings", "HD Settings")).brand_name).toBe(company);

      await expect(page.getByRole("heading", { name: "Connect your support email" })).toBeVisible();
      await expect(page.getByRole("button", { name: /Gmail App password/ })).toBeVisible();
      await page.getByRole("button", { name: "Set up later" }).click();
      await page.getByRole("dialog").getByRole("button", { name: "Set up later" }).click();

      const agent = `e2e-setup-agent-${uid()}@example.com`;
      await expect(page.getByRole("heading", { name: "Invite your agents" })).toBeVisible();
      await page.getByLabel("Email 1").fill(agent);
      await page.getByRole("button", { name: "Send invite" }).click();
      await expect(page.getByText("Sent", { exact: true })).toBeVisible();
      expect(await api.exists("User Invitation", { email: agent, app_name: "helpdesk" })).toBeTruthy();

      await expect(page.getByRole("heading", { name: "You're all set" })).toBeVisible();
      await expect.poll(async () => (await api.get("HD Settings", "HD Settings")).setup_complete).toBe(1);
      await page.getByRole("button", { name: /Go to Helpdesk|Not now/ }).click();
      await expect(page).toHaveURL(/\/helpdesk\/home$/);
    } finally {
      await restore();
    }
  });
});

/** The Password step shows while the Framework setup is not done. */
async function setPasswordIfAsked(page: Page) {
  const heading = page.getByRole("heading", { name: "Welcome. Set your password" });
  const workspace = page.getByRole("heading", { name: "What's your company called?" });
  await expect(heading.or(workspace)).toBeVisible();
  if (!(await heading.isVisible())) return;
  const password = `Bright-Harbor-${uid()}-Lantern`;
  await page.getByLabel("New password", { exact: true }).fill(password);
  await expect(page.getByText("Great")).toBeVisible();
  await page.getByLabel("Confirm new password").fill(password);
  await page.getByRole("button", { name: "Confirm" }).click();
}
