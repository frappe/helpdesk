import type { Locator, Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { raiseTicket } from "../../helpers/factories";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { TicketList } from "../../helpers/list";
import { personas } from "../../helpers/personas";

usePersona("agent2");

test.describe("home", () => {
  test.beforeEach(async ({ api }) => {
    await dropHomeLayout(api);
  });

  test.afterEach(async ({ api }) => {
    await dropHomeLayout(api);
  });

  test("a dragged and resized widget layout survives a reload and resets", async ({
    page,
    apiAs,
  }) => {
    const agent = await apiAs("agent2");
    const defaults = chartBoxes((await dashboard(agent)).layout);
    await page.goto("/helpdesk/home");
    await page.waitForLoadState("networkidle");
    await page.getByRole("button", { name: "Edit" }).click();
    const widget = page.locator(".vgl-item", { hasText: "My Tickets" });
    await expect(widget).toHaveClass(/vgl-item--resizable/);
    await drag(page, widget, widget, 0, 300);
    await drag(page, widget, widget.locator(".vgl-item__resizer"), 200, 100);
    await page.getByRole("button", { name: "Save" }).click();
    await expect(page.getByText("Dashboard saved")).toBeVisible();
    const saved = chartBoxes((await dashboard(agent)).layout);
    expect(saved.agent_tickets).not.toEqual(defaults.agent_tickets);

    const box = await widget.boundingBox();
    await page.reload();
    await expect(widget).toBeVisible();
    expect(await widget.boundingBox()).toEqual(box);

    await page.getByRole("button", { name: "Edit" }).click();
    await page.getByRole("button", { name: "Reset" }).click();
    await page.getByRole("button", { name: "Save" }).click();
    await expect
      .poll(async () => chartBoxes((await dashboard(agent)).layout))
      .toEqual(defaults);
  });

  test("dismissing a widget's custom range brings its presets back", async ({ page }) => {
    await page.goto("/helpdesk/home");
    const metrics = page.locator(".vgl-item", { hasText: "Avg. Time Metrics" });
    await metrics.getByRole("button", { name: "6 Months" }).click();
    await page.getByRole("menuitem", { name: "Custom Range" }).click();
    await expect(page.getByRole("grid", { name: "Calendar dates" })).toBeVisible();
    await page.keyboard.press("Escape");
    // Regression: the empty range picker used to stay with no way back.
    await expect(metrics.getByRole("button", { name: "6 Months" })).toBeVisible();
  });
});

test("dashboard presets and custom range drive the stats period", async ({ page }) => {
  await page.goto("/helpdesk/dashboard");
  const trigger = page.getByText("Last 30 Days");
  await trigger.click();
  const request = page.waitForRequest(
    (request) =>
      request.url().includes("get_dashboard_data") &&
      request.postData()!.includes(daysAgo(7))
  );
  await page.getByRole("menuitem", { name: "Last 7 Days" }).click();
  await request;
  await expect(page.getByText("Last 7 Days")).toBeVisible();

  await page.getByText("Last 7 Days").click();
  await page.getByRole("menuitem", { name: "Custom Range" }).click();
  await expect(page.getByRole("grid", { name: "Calendar dates" })).toBeVisible();
  await page.keyboard.press("Escape");
  // Regression: dismissing the calendar left a dead end with no presets.
  await expect(page.getByText("Last 30 Days")).toBeVisible();

  await page.getByText("Last 30 Days").click();
  await page.getByRole("menuitem", { name: "Custom Range" }).click();
  const cells = page.getByRole("grid", { name: "Calendar dates" }).getByRole("gridcell");
  await cells.nth(8).click();
  await cells.nth(10).click();
  await expect(page.getByText(/^\w{3} \d+ to \w{3} \d+$/)).toBeVisible();
});

test("the command palette finds a ticket and opens it", async ({ page, api, apiAs }) => {
  const token = `palette${uid()}`;
  const ticket = await raiseTicket(await apiAs("customer"), `${token} subject`);
  await indexForSearch(api, token);

  await new TicketList(page).goto();
  // The Desktop Chrome device reports a Windows user agent, so Mod is Control.
  await page.keyboard.press("Control+k");
  const palette = page.getByRole("dialog", { name: "Command Palette" });
  await palette.getByRole("combobox").fill(token);
  await palette.getByRole("option", { name: new RegExp(`${token} subject`) }).click();
  await expect(page).toHaveURL(new RegExp(`/helpdesk/tickets/${ticket.name}`));
});

test("search finds a ticket by text that is only in a comment", async ({
  page,
  api,
  ticket,
}) => {
  const token = `comment${uid()}`;
  await api.insert("Comment", {
    comment_type: "Comment",
    reference_doctype: "HD Ticket",
    reference_name: ticket.name,
    content: `<p>Internal note ${token}</p>`,
  });
  await indexForSearch(api, token);

  await page.goto("/helpdesk/search");
  const box = page.getByRole("textbox", { name: /Search tickets/ });
  await box.fill(token);
  await box.press("Enter");
  await page.getByText(new RegExp(token)).first().click();
  await expect(page).toHaveURL(new RegExp(`/helpdesk/tickets/${ticket.name}`));
});

test("a notification opens its ticket and mark all as read clears it", async ({
  page,
  api,
  apiAs,
}) => {
  const customer = await apiAs("customer");
  const first = await raiseTicket(customer);
  const second = await raiseTicket(customer);
  for (const ticket of [first, second]) {
    await api.call("frappe.desk.form.assign_to.add", {
      doctype: "HD Ticket",
      name: ticket.name,
      assign_to: JSON.stringify([personas.agent2.email]),
    });
  }
  const log = (ticket: { name: string }) =>
    api.list("Notification Log", {
      fields: ["name", "read"],
      filters: { for_user: personas.agent2.email, document_name: ticket.name },
    });
  await expect.poll(async () => (await log(second)).length).toBe(1);

  await page.goto("/helpdesk/tickets");
  const panel = page.locator(".notifications-panel");
  await page.getByRole("navigation", { name: "Main" }).getByRole("button", { name: "Notifications" }).click();
  await panel.getByText(first.subject).click();
  await expect(page).toHaveURL(new RegExp(`/helpdesk/tickets/${first.name}`));
  await expect.poll(async () => (await log(first))[0].read).toBe(1);

  await page.getByRole("navigation", { name: "Main" }).getByRole("button", { name: "Notifications" }).click();
  await panel.getByRole("button", { name: "Mark all as read" }).click();
  await expect.poll(async () => (await log(second))[0].read).toBe(1);
});

test("the shortcuts modal opens from the keyboard", async ({ page }) => {
  await new TicketList(page).goto();
  await page.keyboard.press("Control+/");
  const modal = page.getByRole("dialog", { name: "Keyboard Shortcuts" });
  await expect(modal.getByRole("heading", { name: "Ticket Management" })).toBeVisible();
  await expect(modal.getByText("Open reply box")).toBeVisible();
});

async function dashboard(api: Api) {
  return api.call("helpdesk.api.agent_home.agent_home.get_dashboard");
}

function chartBoxes(layout: any[]) {
  return Object.fromEntries(
    layout.map(({ chart, layout: { x, y, w, h } }) => [chart, { x, y, w, h }])
  );
}

async function dropHomeLayout(api: Api) {
  const name = await api.exists("HD Field Layout", { user: personas.agent2.email });
  if (name) await api.delete("HD Field Layout", name);
}

/** Drag `handle` by an offset, then wait for the grid to settle `widget`. */
async function drag(page: Page, widget: Locator, handle: Locator, dx: number, dy: number) {
  const box = (await handle.boundingBox())!;
  const x = box.x + Math.min(40, box.width / 2);
  const y = box.y + Math.min(30, box.height / 2);
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + dx, y + dy, { steps: 15 });
  await page.mouse.up();
  let last = "";
  await expect
    .poll(async () => {
      const style = (await widget.getAttribute("style")) || "";
      const settled = style === last;
      last = style;
      return settled;
    }, { intervals: [300] })
    .toBe(true);
}

/** New docs only reach the search index through scheduled jobs; run them now. */
async function indexForSearch(api: Api, token: string) {
  await runScheduledJob(api, "frappe.search.sqlite_search.build_index_if_not_exists");
  await expect
    .poll(
      async () => {
        await runScheduledJob(api, "frappe.search.sqlite_search.index_docs_in_queue");
        const found = await api
          .call("helpdesk.api.search.search", { query: token })
          .catch(() => ({ results: [] }));
        return found.results.length;
      },
      { timeout: 30_000, intervals: [1_000] }
    )
    .toBeGreaterThan(0);
}

async function runScheduledJob(api: Api, method: string) {
  const [job] = await api.list("Scheduled Job Type", { filters: { method } });
  await api.call("frappe.core.doctype.scheduled_job_type.scheduled_job_type.execute_event", {
    doc: JSON.stringify({ name: job.name }),
  });
}

// The browser runs in UTC (see playwright.config.ts), so the date is computed in UTC too.
function daysAgo(days: number) {
  return new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10);
}
