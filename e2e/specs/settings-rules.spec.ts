import type { Locator, Page } from "@playwright/test";
import type { Api } from "../support/api";
import { expect, test, uid, usePersona } from "../support/fixtures";
import { personas } from "../support/personas";
import { openSettings } from "../support/settings";

const RULE = "Assignment Rule";
const DEPENDENCY = "Field Dependency-ticket_type-priority";
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

usePersona("admin");

test.describe("field dependencies", () => {
  test.afterEach(async ({ api }) => {
    if (await api.exists("HD Form Script", { name: DEPENDENCY })) await api.delete("HD Form Script", DEPENDENCY);
  });

  test("the builder maps values per parent, then edits, disables and deletes the dependency", async ({ page, api }) => {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Field Dependencies");
    await dialog.getByRole("button", { name: "New" }).click();
    await pickOption(page, dialog.getByRole("combobox").first(), "Ticket Type");
    await pickOption(page, dialog.getByRole("combobox").nth(1), "Priority");

    // Search narrows the child list, and Select All only takes the filtered values.
    await parentValue(dialog, "Bug").click();
    await dialog.getByPlaceholder("Search Bug values").fill("Urg");
    await dialog.getByText("Select All", { exact: true }).click();
    await expect(dialog.getByText("1 value selected")).toBeVisible();
    await dialog.getByPlaceholder("Search Bug values").fill("");
    await expect(childValue(dialog, "Low").getByRole("checkbox")).not.toBeChecked();

    await parentValue(dialog, "Question").click();
    await childValue(dialog, "Low").click();
    await childValue(dialog, "Medium").click();
    await expect(dialog.getByText("2 values selected")).toBeVisible();
    await expect(parentValue(dialog, "Bug")).toContainText("1");

    await turnOffCriteria(dialog);
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(() => mapping(api)).toEqual({ Bug: ["Urgent"], Question: ["Low", "Medium"] });

    const row = dialog.locator("div.grid-cols-11").filter({ hasText: "Ticket Type → Priority" });
    await row.getByText("Ticket Type → Priority").click();
    await expect(dialog.getByRole("combobox").first()).toBeDisabled();
    await parentValue(dialog, "Question").click();
    await childValue(dialog, "Medium").click();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect.poll(() => mapping(api)).toEqual({ Bug: ["Urgent"], Question: ["Low"] });

    // The back button carries the dependency's label.
    await dialog.getByRole("button", { name: /Ticket Type → Priority/ }).first().click();
    await row.getByRole("switch").click();
    await expect.poll(async () => (await api.get("HD Form Script", DEPENDENCY)).enabled).toBe(0);

    await row.getByRole("button").last().click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
    await expect.poll(() => api.exists("HD Form Script", { name: DEPENDENCY })).toBeFalsy();
  });

  test("going back with unsaved choices asks before discarding them", async ({ page, api }) => {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Field Dependencies");
    await dialog.getByRole("button", { name: "New" }).click();
    await pickOption(page, dialog.getByRole("combobox").first(), "Ticket Type");
    await dialog.getByRole("button", { name: "New Field Dependency" }).click();
    const confirm = page.getByRole("dialog", { name: "Unsaved changes" });
    await confirm.getByRole("button", { name: "Confirm" }).click();
    await expect(dialog.getByRole("button", { name: "New", exact: true })).toBeVisible();
    expect(await api.exists("HD Form Script", { name: DEPENDENCY })).toBeFalsy();
  });
});

test.describe("assignment rules", () => {
  let rule: string;

  test.beforeEach(async ({ api }) => {
    rule = `E2E Rule ${uid()}`;
    // The condition names a team that never exists, so the rule never grabs real tickets.
    await api.insert(RULE, {
      name: rule,
      assignment_rule_name: rule,
      document_type: "HD Ticket",
      description: "Route nothing",
      rule: "Round Robin",
      priority: 0,
      assign_condition: `agent_group == "${rule}"`,
      users: [{ user: personas.agent2.email }],
      assignment_days: DAYS.map((day) => ({ day })),
    });
  });

  test.afterEach(async ({ api }) => {
    for (const name of [rule, `${rule} (Copy)`, `${rule} Renamed`]) {
      if (await api.exists(RULE, { name })) await api.delete(RULE, name);
    }
  });

  test("the list changes priority, disables, duplicates and deletes a rule", async ({ page, api }) => {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Assignment Rules");
    const row = ruleRow(dialog, rule);

    await row.locator("select").selectOption({ label: "High" });
    await expect.poll(async () => (await api.get(RULE, rule)).priority).toBe(4);
    await row.getByRole("switch").click();
    await expect.poll(async () => (await api.get(RULE, rule)).disabled).toBe(1);

    await row.getByRole("button").last().click();
    await page.getByRole("menuitem", { name: "Duplicate" }).click();
    const duplicate = page.getByRole("dialog", { name: "Duplicate Assignment Rule" });
    await expect(duplicate.getByRole("textbox")).toHaveValue(`${rule} (Copy)`);
    await duplicate.getByRole("button", { name: "Duplicate" }).click();
    await expect.poll(() => api.exists(RULE, { name: `${rule} (Copy)` })).toBeTruthy();
    expect((await api.get(RULE, `${rule} (Copy)`)).users.map((u: { user: string }) => u.user)).toEqual([
      personas.agent2.email,
    ]);

    await dialog.getByRole("button", { name: `${rule} (Copy)` }).first().click();
    await ruleRow(dialog, `${rule} (Copy)`).getByRole("button").last().click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
    await expect.poll(() => api.exists(RULE, { name: `${rule} (Copy)` })).toBeFalsy();
    expect(await api.exists(RULE, { name: rule })).toBeTruthy();
  });

  test("editing a rule with an old condition renames it and keeps that condition", async ({ page, api }) => {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Assignment Rules");
    await ruleRow(dialog, rule).getByText(rule, { exact: true }).click();
    await expect(dialog.getByText("Old Condition").first()).toBeVisible();

    await dialog.getByRole("textbox", { name: /^Name/ }).fill(`${rule} Renamed`);
    await dialog.getByRole("textbox", { name: /^Description/ }).fill("Still routes nothing");
    await dialog.getByText("Low", { exact: true }).click();
    await page.getByText("Medium-High", { exact: true }).click();
    await dialog.getByRole("button", { name: "Save", exact: true }).click();

    await expect.poll(() => api.exists(RULE, { name: `${rule} Renamed` })).toBeTruthy();
    const saved = await api.get(RULE, `${rule} Renamed`);
    expect(saved).toMatchObject({ description: "Still routes nothing", priority: 3 });
    expect(saved.assign_condition).toBe(`agent_group == "${rule}"`);
  });

  test("saving without a name is refused", async ({ page }) => {
    await page.goto("/helpdesk/tickets");
    const dialog = await openSettings(page, "Assignment Rules");
    await ruleRow(dialog, rule).getByText(rule, { exact: true }).click();
    await dialog.getByRole("textbox", { name: /^Name/ }).fill("");
    await dialog.getByRole("button", { name: "Save", exact: true }).click();
    await expect(page.getByText("Invalid fields, check if all are filled in and values are correct.")).toBeVisible();
  });
});

async function pickOption(page: Page, combobox: Locator, option: string) {
  await combobox.click();
  await page.getByRole("option", { name: option, exact: true }).click();
}

function parentValue(dialog: Locator, value: string) {
  return dialog.getByRole("listitem").filter({ hasText: new RegExp(`^${value}\\d*$`) }).first();
}

function childValue(dialog: Locator, value: string) {
  return dialog.getByRole("listitem").filter({ hasText: new RegExp(`^${value}$`) }).last();
}

// Leave the visibility and mandatory rules off so HD Ticket's schema stays untouched.
async function turnOffCriteria(dialog: Locator) {
  for (const rule of [/^Show Priority if/, /^Make Priority mandatory if/]) {
    await dialog.getByText(rule).locator("xpath=ancestor::div[.//button[@role='switch']][1]").getByRole("switch").click();
  }
}

async function mapping(api: Api) {
  if (!(await api.exists("HD Form Script", { name: DEPENDENCY }))) return null;
  const dependency = await api.call("helpdesk.api.settings.field_dependency.get_field_dependency", {
    name: DEPENDENCY,
  });
  return JSON.parse(dependency.parent_child_mapping);
}

function ruleRow(dialog: Locator, name: string) {
  return dialog.locator("div.grid-cols-12").filter({ has: dialog.page().getByText(name, { exact: true }) });
}
