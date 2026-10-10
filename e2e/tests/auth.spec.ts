import { expect, test, usePersona } from "../helpers/fixtures";
import { PASSWORD, personas } from "../helpers/personas";

test.describe("logged out", () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test("login returns to the requested page, then logs out", async ({ page }) => {
    await page.goto("/helpdesk/tickets");
    await expect(page).toHaveURL(/\/login\?redirect-to=\/helpdesk\/tickets/);

    await page.getByRole("textbox", { name: "Email" }).fill(personas.agent.email);
    await page.getByRole("textbox", { name: "Password" }).fill(PASSWORD);
    await page.getByRole("button", { name: "Continue" }).click();

    await expect(page).toHaveURL(/\/helpdesk\/tickets$/);
    await expect(page.getByRole("button", { name: "Filter" })).toBeVisible();

    await page.getByRole("button", { name: /^Helpdesk / }).click();
    await page.getByRole("menuitem", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe("agent", () => {
  usePersona("agent");

  test("lands on home", async ({ page }) => {
    await page.goto("/helpdesk");
    await expect(page).toHaveURL(/\/helpdesk\/home$/);
  });
});

test.describe("customer", () => {
  usePersona("customer");

  test("lands on the portal and is kept out of agent routes", async ({ page, ticket }) => {
    await page.goto("/helpdesk");
    await expect(page).toHaveURL(/\/help\/?$/);
    await expect(page.getByRole("button", { name: "Customers" })).toHaveCount(0);

    await page.goto(`/helpdesk/tickets/${ticket.name}`);
    await expect(page).toHaveURL(new RegExp(`/help/tickets/${ticket.name}$`));
  });
});
