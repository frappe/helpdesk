import type { Locator, Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { openSettings } from "../../helpers/settings";

const SLA = "HD Service Level Agreement";
const HOLIDAYS = "HD Service Holiday List";
const PRIORITIES = ["Low", "Medium", "High", "Urgent"];

usePersona("admin");

const created: { doctype: string; name: string }[] = [];

test.afterEach(async ({ api }) => {
  // SLAs link to holiday lists, so they go first.
  const records = created.splice(0);
  const ordered = [...records.filter((r) => r.doctype === SLA), ...records.filter((r) => r.doctype !== SLA)];
  for (const { doctype, name } of ordered) {
    if (await api.exists(doctype, { name })) await api.delete(doctype, name);
  }
});

test("an SLA is disabled, duplicated and deleted from the policy list", async ({ page, api }) => {
  const sla = await createSla(api, await createHolidayList(api));
  const copy = `${sla} (Copy)`;
  created.push({ doctype: SLA, name: copy });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "SLA Policies");

  await listRow(dialog, sla).getByRole("switch").click();
  await expect.poll(async () => (await api.get(SLA, sla)).enabled).toBe(0);

  await listRow(dialog, sla).getByRole("button").click();
  await page.getByRole("menuitem", { name: "Duplicate" }).click();
  const duplicate = page.getByRole("dialog", { name: "Duplicate SLA Policy" });
  await expect(duplicate.getByRole("textbox")).toHaveValue(copy);
  await duplicate.getByRole("button", { name: "Duplicate" }).click();
  await expect.poll(() => api.exists(SLA, { name: copy })).toBeTruthy();
  const duplicated = await api.get(SLA, copy);
  expect(duplicated.default_sla).toBe(0);
  expect(duplicated.priorities.map((row) => row.priority).sort()).toEqual([...PRIORITIES].sort());

  await dialog.getByRole("button", { name: copy, exact: true }).click();
  await deleteFromMenu(page, listRow(dialog, copy).getByRole("button"));
  await expect.poll(() => api.exists(SLA, { name: copy })).toBeFalsy();
  await expect(listRow(dialog, sla)).toBeVisible();
});

test("an SLA's targets, work days and holiday list are edited and saved", async ({ page, api }) => {
  const firstList = await createHolidayList(api);
  const secondList = await createHolidayList(api);
  const sla = await createSla(api, firstList);
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "SLA Policies");
  await listRow(dialog, sla).getByText(sla, { exact: true }).click();

  await rowMenu(page, tableRow(dialog, "High"), "Edit");
  const targets = page.getByRole("dialog", { name: "Edit response and resolution" });
  await targets.getByText("1 hour", { exact: true }).click();
  const hours = page.locator("div.group", { hasText: "Hrs" }).locator("input");
  await hours.fill("2");
  await hours.press("Tab");
  await targets.getByRole("checkbox", { name: "Set default priority" }).check();
  await targets.getByRole("button", { name: "Save" }).click();
  await deleteFromMenu(page, tableRow(dialog, "Urgent").getByRole("button"));

  await rowMenu(page, tableRow(dialog, "Tuesday"), "Edit");
  const workday = page.getByRole("dialog", { name: "Edit workday" });
  await workday.getByLabel("End Time").fill("08:00");
  await workday.getByRole("button", { name: "Save" }).click();
  await expect(workday.getByText("End time must be after start time")).toBeVisible();
  await workday.getByLabel("End Time").fill("18:30");
  await workday.getByRole("button", { name: "Save" }).click();
  await expect(workday).toBeHidden();
  await deleteFromMenu(page, tableRow(dialog, "Monday").getByRole("button"));
  await dialog.getByRole("button", { name: "Add row" }).last().click();

  await dialog.getByRole("button", { name: firstList, exact: true }).click();
  await page.getByText(secondList, { exact: true }).click();
  await page.keyboard.press("Escape");
  await dialog.getByRole("button", { name: "Save", exact: true }).click();

  await expect.poll(async () => (await api.get(SLA, sla)).holiday_list).toBe(secondList);
  const saved = await api.get(SLA, sla);
  const byPriority = Object.fromEntries(saved.priorities.map((row) => [row.priority, row]));
  expect(Object.keys(byPriority).sort()).toEqual(["High", "Low", "Medium"]);
  expect(byPriority.High).toMatchObject({ default_priority: 1, response_time: 7200 });
  expect(byPriority.Medium.default_priority).toBe(0);
  expect(
    saved.support_and_resolution.map((row) => [row.workday, row.start_time, row.end_time])
  ).toEqual([
    ["Tuesday", "9:00:00", "18:30:00"],
    ["Monday", "9:00:00", "17:00:00"],
  ]);
});

test("a holiday list gets a recurring weekend and its holidays are edited", async ({ page, api }) => {
  const list = await createHolidayList(api);
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Business Holidays");
  await dialog.getByText(list, { exact: true }).click();

  await dialog.getByRole("button", { name: "Add Recurring Holiday" }).click();
  const recurring = page.getByRole("dialog", { name: "Add Recurring Holiday" });
  await recurring.getByRole("combobox").click();
  await page.getByRole("option", { name: "Saturday" }).click();
  await recurring.getByRole("button", { name: "Add Holiday" }).click();
  await expect(page.getByText("Please select at least one repetition option")).toBeVisible();
  await recurring.getByRole("checkbox", { name: "Every week", exact: true }).check();
  await recurring.getByRole("button", { name: "Add Holiday" }).click();
  await expect(dialog.getByText(`There are in total ${daysIn2027(6).length + 1} holidays`)).toBeVisible();

  await rowMenu(page, recurringRow(dialog, "Saturday"), "Edit");
  const editRecurring = page.getByRole("dialog", { name: "Edit Recurring Holiday" });
  await editRecurring.getByRole("checkbox", { name: "Every week", exact: true }).uncheck();
  await editRecurring.getByRole("checkbox", { name: "Every first week" }).check();
  await editRecurring.getByRole("button", { name: "Update Holiday" }).click();
  await expect(recurringRow(dialog, "Saturday")).toContainText("Every first");
  await expect(dialog.getByText("There are in total 13 holidays")).toBeVisible();

  await dialog.getByRole("radio", { name: "List" }).click();
  await rowMenu(page, holidayRow(dialog, "26 Jan 2027"), "Edit");
  const editHoliday = page.getByRole("dialog", { name: "Edit Holiday" });
  await editHoliday.getByPlaceholder("National holiday, etc.").fill("Republic Day, observed");
  await editHoliday.getByRole("button", { name: "Add Holiday" }).click();

  await addHoliday(page, dialog, "2028-01-05", "Out of range");
  await expect(page.getByText(/Holiday date must be between/)).toBeVisible();
  await page.getByRole("dialog", { name: "Add Holiday" }).getByRole("button", { name: "Cancel" }).click();
  await addHoliday(page, dialog, "2027-08-15", "Independence Day");
  await deleteFromMenu(page, holidayRow(dialog, "15 Aug 2027").getByRole("button"));
  await expect(holidayRow(dialog, "15 Aug 2027")).toHaveCount(0);
  await dialog.getByRole("button", { name: "Save", exact: true }).click();

  await expect.poll(async () => JSON.parse((await api.get(HOLIDAYS, list)).recurring_holidays || "[]")).toEqual([
    expect.objectContaining({ day: "Saturday", repetition: expect.objectContaining({ all: false, first: true }) }),
  ]);
  const saved = await api.get(HOLIDAYS, list);
  const weeklyOffs = saved.holidays.filter((row) => row.weekly_off).map((row) => row.holiday_date);
  expect(weeklyOffs.sort()).toEqual(firstOfEachMonth(daysIn2027(6)));
  const others = saved.holidays.filter((row) => !row.weekly_off);
  expect(others.map((row) => [row.holiday_date, row.description])).toEqual([["2027-01-26", "Republic Day, observed"]]);
});

test("a holiday list spanning two years is browsed, duplicated and deleted", async ({ page, api }) => {
  const list = await createHolidayList(api, { to_date: "2028-12-31" });
  const copy = `${list} (Copy)`;
  created.push({ doctype: HOLIDAYS, name: copy });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Business Holidays");
  await dialog.getByText(list, { exact: true }).click();

  await dialog.getByRole("button", { name: /^20\d\d$/ }).click();
  await page.getByText("2028", { exact: true }).click();
  await expect(dialog.getByText("January, 2028")).toBeVisible();
  await dialog.getByRole("button", { name: "2028" }).click();
  await page.getByText("2027", { exact: true }).click();
  await dialog.locator(".bg-surface-yellow-2", { hasText: /^26$/ }).click();
  const editHoliday = page.getByRole("dialog", { name: "Edit Holiday" });
  await expect(editHoliday.getByPlaceholder("National holiday, etc.")).toHaveValue("Republic Day");
  await editHoliday.getByRole("button", { name: "Cancel" }).click();

  await dialog.getByRole("button", { name: list, exact: true }).click();
  await listRow(dialog, list).getByRole("button").click();
  await page.getByRole("menuitem", { name: "Duplicate" }).click();
  const duplicate = page.getByRole("dialog", { name: "Duplicate Holiday List" });
  await expect(duplicate.getByRole("textbox")).toHaveValue(copy);
  await duplicate.getByRole("button", { name: "Duplicate" }).click();
  await expect.poll(() => api.exists(HOLIDAYS, { name: copy })).toBeTruthy();
  expect((await api.get(HOLIDAYS, copy)).holidays.map((row) => row.holiday_date)).toEqual(["2027-01-26"]);

  await dialog.getByRole("button", { name: copy, exact: true }).click();
  await deleteFromMenu(page, listRow(dialog, copy).getByRole("button"));
  await expect.poll(() => api.exists(HOLIDAYS, { name: copy })).toBeFalsy();
});

test("the holiday calendar opens on the list's first year", async ({ page, api }) => {
  const list = await createHolidayList(api, { to_date: "2028-12-31" });
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Business Holidays");
  await dialog.getByText(list, { exact: true }).click();
  await expect(dialog.getByText("January, 2027")).toBeVisible();
});

test("every first Sunday includes a month that starts on a Sunday", async ({ page, api }) => {
  const list = await createHolidayList(api);
  await page.goto("/helpdesk/tickets");
  const dialog = await openSettings(page, "Business Holidays");
  await dialog.getByText(list, { exact: true }).click();
  await dialog.getByRole("button", { name: "Add Recurring Holiday" }).click();
  const recurring = page.getByRole("dialog", { name: "Add Recurring Holiday" });
  await recurring.getByRole("combobox").click();
  await page.getByRole("option", { name: "Sunday" }).click();
  await recurring.getByRole("checkbox", { name: "Every first week" }).check();
  await recurring.getByRole("button", { name: "Add Holiday" }).click();
  await dialog.getByRole("button", { name: "Save", exact: true }).click();
  await expect
    .poll(async () => (await api.get(HOLIDAYS, list)).holidays.filter((row) => row.weekly_off).map((row) => row.holiday_date).sort())
    .toEqual(firstOfEachMonth(daysIn2027(0)));
});

async function createHolidayList(api: Api, overrides: Record<string, unknown> = {}) {
  const name = `E2E Holidays ${uid()}`;
  created.push({ doctype: HOLIDAYS, name });
  await api.insert(HOLIDAYS, {
    holiday_list_name: name,
    from_date: "2027-01-01",
    to_date: "2027-12-31",
    holidays: [{ holiday_date: "2027-01-26", description: "Republic Day", weekly_off: 0 }],
    ...overrides,
  });
  return name;
}

async function createSla(api: Api, holidayList: string) {
  const name = `E2E SLA ${uid()}`;
  created.push({ doctype: SLA, name });
  await api.insert(SLA, {
    service_level: name,
    holiday_list: holidayList,
    enabled: 1,
    default_sla: 0,
    apply_sla_for_resolution: 1,
    priorities: PRIORITIES.map((priority) => ({
      priority,
      response_time: 3600,
      resolution_time: 86400,
      default_priority: priority === "Medium" ? 1 : 0,
    })),
    support_and_resolution: ["Monday", "Tuesday"].map((workday) => ({
      workday,
      start_time: "09:00:00",
      end_time: "17:00:00",
    })),
  });
  return name;
}

/** A row of the SLA or holiday list, found by its exact name. */
function listRow(dialog: Locator, name: string) {
  return dialog.locator("div.cursor-pointer").filter({ has: dialog.page().getByText(name, { exact: true }) });
}

/** A priority or work day row, found by the value selected in its dropdown. */
function tableRow(dialog: Locator, value: string) {
  return dialog.locator("div.grid").filter({ has: dialog.page().locator(`select option:checked[value="${value}"]`) });
}

/** A recurring holiday row, found by its day. */
function recurringRow(dialog: Locator, day: string) {
  return dialog.locator("div.grid").filter({ has: dialog.page().getByText(day, { exact: true }) });
}

function holidayRow(dialog: Locator, date: string) {
  return dialog.locator("div.grid").filter({ has: dialog.page().getByText(date, { exact: true }) });
}

async function rowMenu(page: Page, row: Locator, action: string) {
  await row.getByRole("button").click();
  await page.getByRole("menuitem", { name: action }).click();
}

async function deleteFromMenu(page: Page, menuButton: Locator) {
  await menuButton.click();
  await page.getByRole("menuitem", { name: "Delete" }).click();
  await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
}

async function addHoliday(page: Page, dialog: Locator, date: string, description: string) {
  await dialog.getByRole("button", { name: "Add Holiday" }).click();
  const modal = page.getByRole("dialog", { name: "Add Holiday" });
  await modal.getByRole("combobox").fill(date);
  await modal.getByRole("combobox").press("Enter");
  await modal.getByPlaceholder("National holiday, etc.").fill(description);
  await modal.getByRole("button", { name: "Add Holiday" }).click();
}

/** Every date in 2027 that falls on a weekday, 0 being Sunday. */
function daysIn2027(weekday: number) {
  const dates: string[] = [];
  for (let day = new Date(Date.UTC(2027, 0, 1)); day.getUTCFullYear() === 2027; day.setUTCDate(day.getUTCDate() + 1)) {
    if (day.getUTCDay() === weekday) dates.push(day.toISOString().slice(0, 10));
  }
  return dates;
}

function firstOfEachMonth(dates: string[]) {
  return dates.filter((date) => Number(date.slice(8)) <= 7);
}
