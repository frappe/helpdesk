import type { Api } from "../helpers/api";
import { expect, test, uid, usePersona } from "../helpers/fixtures";

const setSetupComplete = (api: Api, value: 0 | 1) =>
  api.update("HD Settings", "HD Settings", { setup_complete: value });

test.describe("first-run setup", () => {
  usePersona("admin");

  test.beforeEach(async ({ api }) => {
    await setSetupComplete(api, 0);
  });

  test.afterEach(async ({ api }) => {
    await setSetupComplete(api, 1);
  });

  test("a pending admin is sent to setup", async ({ page }) => {
    await page.goto("/helpdesk/home");

    await expect(page).toHaveURL(/\/helpdesk\/setup$/);
    await expect(page.getByText("Step 1 of 2")).toBeVisible();
  });

  test("skipping setup confirms, sets the site flag and never shows it again", async ({
    page,
    api,
  }) => {
    await page.goto("/helpdesk/setup");
    await page.getByRole("button", { name: "Skip setup" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Skip setup" }).click();

    await expect(page).toHaveURL(/\/helpdesk\/home$/);
    const settings = await api.get("HD Settings", "HD Settings");
    expect(settings.setup_complete).toBe(1);

    await page.goto("/helpdesk/setup");
    await expect(page).toHaveURL(/\/helpdesk\/home$/);
  });

  test("invite rows are validated and nothing is sent when they are wrong", async ({
    page,
    api,
  }) => {
    const email = `${uid("setup")}@example.com`;
    await page.goto("/helpdesk/setup");
    await page.getByRole("button", { name: "Continue" }).click();
    await expect(page.getByText("Step 2 of 2")).toBeVisible();

    await page.getByPlaceholder("name@company.com").first().fill(email.toUpperCase());
    await page.getByRole("button", { name: "Add another" }).click();
    await page.getByPlaceholder("name@company.com").nth(1).fill(email);
    await page.getByRole("button", { name: /^Send/ }).click();

    await expect(page.getByText("This email is already in the list")).toBeVisible();
    expect(await api.exists("User Invitation", { email })).toBeFalsy();
  });
});

test.describe("who sees setup", () => {
  test.beforeEach(async ({ api }) => {
    await setSetupComplete(api, 0);
  });

  test.afterEach(async ({ api }) => {
    await setSetupComplete(api, 1);
  });

  for (const persona of ["manager", "agent"] as const) {
    test(`${persona} is sent home`, async ({ pageAs }) => {
      const page = await pageAs(persona);
      await page.goto("/helpdesk/setup");

      await expect(page).toHaveURL(/\/helpdesk\/home$/);
    });
  }
});
