import { expect, type Page } from "@playwright/test";
import type { Api } from "./api";

/** Open the settings modal from the user menu and switch to a tab. */
export async function openSettings(page: Page, tab: string | RegExp) {
  await page.getByRole("button", { name: /^Helpdesk / }).click();
  await page.getByRole("menuitem", { name: "Settings" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: tab, exact: true }).click();
  await expect(dialog.getByRole("heading", { level: 1 }).nth(1)).toBeVisible();
  return dialog;
}

/** Snapshot HD Settings fields so a test can put them back afterwards. */
export async function snapshotSettings(api: Api, fields: string[]) {
  const settings = await api.get("HD Settings", "HD Settings");
  // REST updates skip nulls, so an empty field is restored as "".
  const saved = Object.fromEntries(fields.map((field) => [field, settings[field] ?? ""]));
  return () => api.update("HD Settings", "HD Settings", saved);
}

/** Create an active agent nobody else uses, safe to disable or delete. */
export async function createThrowawayAgent(api: Api, email: string, password?: string) {
  await api.insert("User", {
    email,
    first_name: email.split("@")[0],
    send_welcome_email: 0,
    roles: [{ role: "Agent" }],
    ...(password && { new_password: password }),
  });
  return api.insert("HD Agent", { user: email, agent_name: email.split("@")[0], is_active: 1 });
}
