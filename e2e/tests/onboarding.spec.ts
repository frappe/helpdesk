import type { Page } from "@playwright/test";
import type { Api } from "../helpers/api";
import { expect, test, uid } from "../helpers/fixtures";

const ANSWERS = [
  "Spreadsheets",
  "Email",
  "Via email",
  "Finding past conversations",
  "GitHub",
  "Create my first ticket",
];

test.describe.configure({ mode: "serial" });

test.describe("onboarding persona form", () => {
  let brandName: string;
  let appName: string;

  // Finishing the form renames the brand, so put the old names back.
  test.beforeEach(async ({ api }) => {
    brandName = (await api.get("HD Settings", "HD Settings")).brand_name || "";
    appName = (await api.get("Website Settings", "Website Settings")).app_name || "";
    await setPersonaCaptured(api, 0);
  });

  test.afterEach(async ({ api }) => {
    await api.update("HD Settings", "HD Settings", {
      persona_captured: 1,
      brand_name: brandName,
    });
    await api.update("Website Settings", "Website Settings", { app_name: appName });
  });

  test("an uncaptured admin fills the questionnaire once", async ({ api, pageAs }) => {
    const page = await pageAs("admin");
    const company = `E2E Org ${uid()}`;
    await page.goto("/helpdesk/onboarding");

    await page.getByPlaceholder("e.g. Acme Inc.").fill(company);
    await page.getByRole("button", { name: "Next", exact: true }).click();
    for (const answer of ANSWERS) {
      await page.getByRole("button", { name: answer, exact: true }).click();
      const last = answer === ANSWERS.at(-1);
      await page.getByRole("button", { name: last ? "Finish" : "Next", exact: true }).click();
    }

    await expect(page).toHaveURL(/\/helpdesk\/tickets\/new/);
    const settings = await api.get("HD Settings", "HD Settings");
    expect(settings.persona_captured).toBe(1);
    expect(settings.brand_name).toBe(company);

    await expectBlocked(page);
  });

  test("agents, managers and customers never see it", async ({ pageAs }) => {
    for (const persona of ["agent", "manager", "customer"] as const) {
      await expectBlocked(await pageAs(persona));
    }
  });

  test("a captured admin cannot reopen it", async ({ api, pageAs }) => {
    await setPersonaCaptured(api, 1);
    await expectBlocked(await pageAs("admin"));
  });

  test("an admin is interrupted only while telemetry is on", async ({ pageAs }) => {
    const withTelemetry = await pageAs("admin");
    await forceTelemetry(withTelemetry);
    await withTelemetry.goto("/helpdesk/tickets");
    await expect(withTelemetry).toHaveURL(/\/helpdesk\/onboarding$/);

    const withoutTelemetry = await pageAs("admin");
    await withoutTelemetry.goto("/helpdesk/tickets");
    await expect(withoutTelemetry.getByRole("button", { name: "Filter" })).toBeVisible();
    await expect(withoutTelemetry).toHaveURL(/\/helpdesk\/tickets$/);
  });
});

async function setPersonaCaptured(api: Api, value: 0 | 1) {
  await api.update("HD Settings", "HD Settings", { persona_captured: value });
}

async function expectBlocked(page: Page) {
  await page.goto("/helpdesk/onboarding");
  await expect(page).not.toHaveURL(/\/onboarding/);
  await expect(page.getByPlaceholder("e.g. Acme Inc.")).toHaveCount(0);
}

// The boot script assigns window.telemetry; pin it on and swallow the write.
async function forceTelemetry(page: Page) {
  await page.addInitScript(() => {
    Object.defineProperty(window, "telemetry", {
      get: () => ({ enabled: true }),
      set: () => {},
      configurable: true,
    });
  });
}
