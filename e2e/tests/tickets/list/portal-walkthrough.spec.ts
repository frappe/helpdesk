import type { Page } from "@playwright/test";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { PASSWORD, personas } from "../../../helpers/personas";
import { siteHeader } from "../../../helpers/site";

// Every customer action on /help/customer-tickets, past what portal-list.spec covers.
usePersona("customer");

/** Raise `count` tickets sharing one token, so the Subject quick filter isolates them. */
async function raiseBatch(apiAs, count = 1) {
  const token = uid();
  const customer = await apiAs("customer");
  const tickets = [];
  for (let i = 0; i < count; i++) tickets.push(await raiseTicket(customer, `${token} walk ${i}`));
  return { token, tickets };
}

async function narrowTo(page: Page, token: string) {
  // Waits for the list to settle first: a fill before it mounts is wiped by the initial restore.
  await expect(page.getByRole("button", { name: /^\d{4} / }).first()).toBeVisible();
  const reloaded = page.waitForRequest(
    (request) => /frappe.client.get_count/.test(request.url()) && (request.postData() || "").includes(token)
  );
  await page.getByRole("textbox", { name: "Subject" }).fill(token);
  await reloaded;
}

function row(page: Page, subject: string) {
  return page.getByRole("button", { name: new RegExp(subject) });
}

test.describe("header", () => {
  test("logo menu links to home, my tickets and settings", async ({ page }) => {
    await page.goto("/help/customer-tickets");
    const menu = page.getByRole("button", { name: "Helpdesk" });

    await menu.click();
    await expect(page.getByRole("menuitem", { name: "Agent portal" })).toHaveCount(0);
    await page.getByRole("menuitem", { name: "Home" }).click();
    await expect(page).toHaveURL(/\/help\/?$/);

    await menu.click();
    await page.getByRole("menuitem", { name: "My tickets" }).click();
    await expect(page).toHaveURL(/\/help\/customer-tickets/);

    await menu.click();
    await page.getByRole("menuitem", { name: "Settings" }).click();
    await expect(page).toHaveURL(/#settings\/profile$/);
    await expect(page.getByRole("dialog")).toBeVisible();
  });

  test("an agent's menu also links to the agent portal", async ({ pageAs }) => {
    const page = await pageAs("agent");
    await page.goto("/help/customer-tickets");
    await page.getByRole("button", { name: "Helpdesk" }).click();
    await page.getByRole("menuitem", { name: "Agent portal" }).click();
    await expect(page).toHaveURL(/\/helpdesk/);
  });

  test("log out returns to the portal home", async ({ browser, baseURL }) => {
    // Its own session: logging out ends the session the other tests share.
    const context = await browser.newContext({ baseURL, extraHTTPHeaders: siteHeader() });
    const page = await context.newPage();
    await page.request.post("/api/method/login", {
      form: { usr: personas.customer.email, pwd: PASSWORD },
    });
    await page.goto("/help/customer-tickets");
    await page.getByRole("button", { name: "Helpdesk" }).click();
    await page.getByRole("menuitem", { name: "Log out" }).click();
    await expect(page).toHaveURL(/\/(help\/?|login.*)$/);
    const user = await page.request.get("/api/method/frappe.auth.get_logged_user");
    expect(user.status()).not.toBe(200);
    await context.close();
  });

  test("an unknown portal path shows Not Found with a way home", async ({ page }) => {
    await page.goto("/help/no-such-page");
    await expect(page.getByText("The page you are looking for does not exist.")).toBeVisible();
    await page.getByRole("link", { name: "Back to Home" }).click();
    await expect(page).toHaveURL(/\/help\/?$/);
  });

  test("other desk routes send a customer to the portal", async ({ page }) => {
    await page.goto("/helpdesk/kb");
    await expect(page).toHaveURL(/\/help\/?$/);
  });
});

test.describe("list", () => {
  test("an agent sees customers' tickets on the portal list", async ({ pageAs, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs);
    const page = await pageAs("agent");
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    await expect(row(page, tickets[0].subject)).toBeVisible();
  });

  test("default columns and opening a row", async ({ page, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs);
    await page.goto("/help/customer-tickets");
    for (const heading of ["ID", "Subject", "Status", "Priority", "First Response", "Resolution", "Created"]) {
      await expect(page.getByText(heading, { exact: true }).first()).toBeVisible();
    }
    await narrowTo(page, token);
    await row(page, tickets[0].subject).click();
    await expect(page).toHaveURL(new RegExp(`/help/tickets/${tickets[0].name}$`));
  });

  test("a ticket an agent changed reads unread until the customer opens it", async ({ page, api, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs);
    // any save by someone else resets `_seen` to them
    await api.update("HD Ticket", tickets[0].name, { priority: "High" });
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    const subject = () => row(page, tickets[0].subject).getByText(tickets[0].subject);
    await expect(subject()).toHaveClass(/font-semibold/);

    await row(page, tickets[0].subject).click();
    await expect(page.getByRole("button", { name: "Close" })).toBeVisible();
    // the list keeps its filter, so the row comes back without narrowing again
    await page.getByRole("link", { name: "Tickets" }).click();
    await expect(subject()).not.toHaveClass(/font-semibold/, { timeout: 5_000 });
  });

  test("refresh picks up a ticket raised after the list loaded", async ({ page, apiAs }) => {
    const { token } = await raiseBatch(apiAs);
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    const later = await raiseTicket(await apiAs("customer"), `${token} later`);
    await expect(row(page, later.subject)).toHaveCount(0);
    await page.getByRole("button", { name: "Refresh" }).click();
    await expect(row(page, later.subject)).toBeVisible();
  });

  test("filter narrows the list and explains an empty result", async ({ page, api, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs, 2);
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    await expect(row(page, token)).toHaveCount(2);

    // a closed ticket drops out of an Open-only list
    await api.update("HD Ticket", tickets[0].name, { status: "Closed" });
    // the desk's filter: pick a field, then its value
    await page.getByRole("button", { name: "Filter" }).click();
    const popover = page.getByRole("dialog", { name: "Filter" });
    await expect(popover).toBeVisible();
    const addFilter = popover.getByRole("button", { name: "Add filter" });
    if (await addFilter.isVisible()) await addFilter.click();
    await popover.getByRole("textbox").fill("Status");
    await page.getByRole("option", { name: "Status", exact: true }).click();
    await page.getByRole("option", { name: "Open", exact: true }).click();
    await page.keyboard.press("Escape");
    await expect(row(page, tickets[0].subject)).toHaveCount(0);
    await expect(row(page, tickets[1].subject)).toBeVisible();

    await page.getByRole("textbox", { name: "Subject" }).fill(`${token} nothing`);
    await expect(page.getByText("No tickets found")).toBeVisible();
    await expect(
      page.getByText("No tickets match the applied filters. Try adjusting or clearing them.")
    ).toBeVisible();
  });

  test("sort flips direction", async ({ page, apiAs }) => {
    const { token } = await raiseBatch(apiAs, 2);
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    const rows = page.getByRole("button", { name: new RegExp(`${token} walk`) });
    await expect(rows.first()).toContainText("walk 1");

    await page.getByRole("button", { name: "Created On" }).click();
    const reloaded = page.waitForResponse(/frappe.client.get_count/);
    await page.getByRole("dialog", { name: "Created On" }).getByRole("button").first().click();
    await reloaded;
    await expect(rows.first()).toContainText("walk 0");
  });

  test("columns can be removed and added", async ({ page }) => {
    await page.goto("/help/customer-tickets");
    await page.getByRole("button", { name: "Columns" }).click();
    const dialog = page.getByRole("dialog", { name: "Columns" });
    const priority = dialog.locator("input[value='Priority']");
    await priority.locator("xpath=following-sibling::button | ../following-sibling::button").first().click();
    await page.keyboard.press("Escape");
    await expect(page.getByText("Priority", { exact: true })).toHaveCount(0);

    await page.getByRole("button", { name: "Columns" }).click();
    await dialog.getByRole("button", { name: "Add Column" }).click();
    await page.getByRole("option", { name: "Priority", exact: true }).click();
    await page.keyboard.press("Escape");
    await expect(page.getByText("Priority", { exact: true }).first()).toBeVisible();
  });

  test("page length and load more", async ({ page, apiAs }) => {
    // its own tickets: backend suites on this site may have deleted everyone else's
    const { token } = await raiseBatch(apiAs, 51);
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    const rows = page.getByRole("button", { name: /^\d{4} / });
    await expect(rows).toHaveCount(20);
    await page.getByRole("button", { name: "Load More" }).click();
    await expect(rows).toHaveCount(40);
    await page.getByRole("radio", { name: "50" }).click();
    await expect(rows).toHaveCount(50);
  });

  test("selecting rows offers no bulk action that breaks", async ({ page, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs);
    const errors: string[] = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    await row(page, tickets[0].subject).getByRole("checkbox").check();
    await expect(page).toHaveURL(/customer-tickets/);
    await expect(page.getByText(/1 row selected/)).toBeVisible();
    expect(errors).toEqual([]);
  });

  test("filters are remembered when coming back", async ({ page, apiAs }) => {
    const { token } = await raiseBatch(apiAs);
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);
    await page.goto("/help");
    await page.getByRole("button", { name: "Helpdesk" }).click();
    await page.getByRole("menuitem", { name: "My tickets" }).click();
    await expect(page.getByRole("textbox", { name: "Subject" })).toHaveValue(token);
    await expect(page.getByRole("button", { name: new RegExp(`${token} walk`) })).toHaveCount(1);
  });

  test("organisation switcher is hidden for a single organisation", async ({ page }) => {
    await page.goto("/help/customer-tickets");
    await expect(page.getByRole("button", { name: "Refresh" })).toBeVisible();
    await expect(page.getByText("Select organizations")).toHaveCount(0);
  });
});

test.describe("organisations", () => {
  test("a member of two organisations switches between them", async ({ browser, baseURL, api }) => {
    const id = uid();
    const email = `e2e-two-orgs-${id}@example.com`;
    await api.insert("User", {
      email,
      first_name: "Twoorgs",
      send_welcome_email: 0,
      user_type: "Website User",
      new_password: PASSWORD,
      roles: [{ role: "HD Customer" }],
    });
    const contact = await api.insert("Contact", {
      first_name: "Twoorgs",
      email_id: email,
      user: email,
      email_ids: [{ email_id: email, is_primary: 1 }],
    });
    const orgs = [];
    for (const suffix of ["A", "B"]) {
      orgs.push(
        await api.insert("HD Customer", {
          customer_name: `E2E Walk Org ${suffix} ${id}`,
          contacts: [{ contact_name: contact.name }],
        })
      );
    }
    const tickets = [];
    for (const org of orgs) {
      tickets.push(
        await api.insert("HD Ticket", {
          subject: `${id} for ${org.name}`,
          description: "<p>org ticket</p>",
          raised_by: email,
          customer: org.name,
        })
      );
    }
    const context = await browser.newContext({ baseURL, extraHTTPHeaders: siteHeader() });
    try {
      const page = await context.newPage();
      await page.request.post("/api/method/login", { form: { usr: email, pwd: PASSWORD } });
      await page.goto("/help/customer-tickets");
      await expect(row(page, tickets[0].subject)).toBeVisible();
      await expect(row(page, tickets[1].subject)).toBeVisible();

      await page.getByRole("button", { name: /Select organizations/ }).click();
      await page.getByRole("option", { name: orgs[0].name }).click();
      await page.keyboard.press("Escape");
      await expect(row(page, tickets[1].subject)).toHaveCount(0);
      await expect(row(page, tickets[0].subject)).toBeVisible();
    } finally {
      await context.close();
    }
  });
});

test.describe("phone", () => {
  test.use({ viewport: { width: 390, height: 800 } });

  test("stacked rows open the ticket; no quick filters or column settings", async ({ page, apiAs }) => {
    const { tickets } = await raiseBatch(apiAs);
    await page.goto("/help/customer-tickets");
    const stacked = page.getByRole("button", { name: new RegExp(`^${tickets[0].subject} .* ${tickets[0].name}$`) });
    await expect(stacked).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Subject" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Columns" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Refresh" })).toBeVisible();
    await stacked.click();
    await expect(page).toHaveURL(new RegExp(`/help/tickets/${tickets[0].name}$`));
  });
});

test.describe("saved views", () => {
  async function openViews(page: Page, current = "List") {
    await page.getByRole("button", { name: current, exact: true }).click();
  }

  async function closeStuckMenu(page: Page) {
    if (!(await viewsMenu(page).isVisible())) return;
    await expect(page.locator("[role=dialog]")).toHaveCount(0);
    await expect(async () => {
      await page.keyboard.press("Escape");
      await expect(viewsMenu(page)).toBeHidden({ timeout: 1_000 });
    }).toPass();
  }

  /** The views menu, which a view action should close behind it. */
  function viewsMenu(page: Page) {
    // Not by role: once a dialog has opened over it, the stuck menu is aria-hidden yet still painted.
    return page.getByText("Save as new view", { exact: true });
  }

  async function viewAction(page: Page, label: string, action: string) {
    await openViews(page, label);
    const item = page.getByRole("menuitem", { name: label });
    await item.hover();
    await item.getByRole("button", { name: "View actions" }).click();
    await page.getByRole("menuitem", { name: action }).click();
    // ponytail: works around the menu-stays-open bug pinned by the test below; drop once fixed
    if (action !== "Rename") await closeStuckMenu(page);
  }

  test("a view action closes the views menu", async ({ page, api }) => {
    await page.goto("/help/customer-tickets");
    await expect(page.getByRole("button", { name: /^\d{4} / }).first()).toBeVisible();
    const label = `E2E view ${uid()}`;
    await openViews(page);
    await viewsMenu(page).click();
    await page.getByPlaceholder("My open tickets").fill(label);
    await page.getByPlaceholder("My open tickets").press("Enter");
    await expect.poll(() => new URL(page.url()).searchParams.get("view")).toBeTruthy();
    const name = new URL(page.url()).searchParams.get("view")!;
    try {
      await openViews(page, label);
      const item = page.getByRole("menuitem", { name: label });
      await item.hover();
      await item.getByRole("button", { name: "View actions" }).click();
      await page.getByRole("menuitem", { name: "Save current layout" }).click();
      await expect(viewsMenu(page)).toBeHidden({ timeout: 3_000 });
    } finally {
      await api.delete("HD View", name);
    }
  });

  test("save, open, update, rename and delete a view", async ({ page, api, apiAs }) => {
    const { token } = await raiseBatch(apiAs, 2);
    const label = `E2E view ${uid()}`;
    await page.goto("/help/customer-tickets");
    await narrowTo(page, token);

    // save as new view
    await openViews(page);
    await page.getByRole("menuitem", { name: "Save as new view" }).click();
    const dialog = page.getByRole("dialog", { name: "Save as new view" });
    await expect(dialog.getByText("Saves the filters, sort order and columns currently on screen.")).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Create" })).toBeDisabled();
    await dialog.getByPlaceholder("My open tickets").fill(label);
    await dialog.getByPlaceholder("My open tickets").press("Enter");
    await expect(page.getByText(`View "${label}" created`)).toBeVisible();
    await expect(page).toHaveURL(/\?view=/);
    const name = new URL(page.url()).searchParams.get("view")!;
    const saved = await api.get("HD View", name);
    expect(saved).toMatchObject({ is_customer_portal: 1, owner: personas.customer.email, icon: "text-align-justify" });
    expect(saved.filters).toContain(token);

    // back to List, then open the view from the dropdown: its filters return
    await openViews(page, label);
    await page.getByRole("menuitem", { name: "List" }).click();
    await expect(page).not.toHaveURL(/\?view=/);
    await openViews(page);
    await page.getByRole("menuitem", { name: label }).click();
    await expect.poll(() => new URL(page.url()).searchParams.get("view")).toBe(name);
    await expect(page.getByRole("button", { name: new RegExp(`${token} walk`) })).toHaveCount(2);

    // a direct link lands on the same view
    await page.goto(`/help/customer-tickets?view=${encodeURIComponent(name)}`);
    await expect(page.getByRole("button", { name: label, exact: true })).toBeVisible();

    // save current layout
    await page.getByRole("button", { name: "Created On" }).click();
    await page.getByRole("dialog", { name: "Created On" }).getByRole("button").first().click();
    await page.keyboard.press("Escape");
    await viewAction(page, label, "Save current layout");
    await expect(page.getByText("View updated")).toBeVisible();
    await expect.poll(async () => (await api.get("HD View", name)).order_by).toBe("creation asc");

    // rename with an emoji icon
    await viewAction(page, label, "Rename");
    const nameField = page.getByPlaceholder("My open tickets");
    await expect(nameField).toHaveValue(label);
    await nameField.fill(`${label} renamed`);
    await nameField.press("Enter");
    await expect.poll(async () => (await api.get("HD View", name)).label).toBe(`${label} renamed`);
    await closeStuckMenu(page);
    await expect(page.getByText(`${label} renamed`, { exact: true }).first()).toBeVisible();

    // delete the open view: no confirm, back to List
    await page.getByText(`${label} renamed`, { exact: true }).first().click();
    const renamed = page.getByRole("menuitem", { name: `${label} renamed` });
    await renamed.hover();
    await renamed.getByRole("button", { name: "View actions" }).click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await expect(page).not.toHaveURL(/\?view=/);
    await expect.poll(() => api.exists("HD View", { name })).toBeFalsy();
  });

  test("another user's view is not offered and its link falls back to List", async ({ page, apiAs, pageAs }) => {
    const manager = await apiAs("customerManager");
    const view = await manager.insert("HD View", {
      label: `E2E view ${uid()}`,
      dt: "HD Ticket",
      type: "list",
      is_customer_portal: 1,
      user: personas.customerManager.email,
      filters: "[]",
    });
    try {
      await page.goto(`/help/customer-tickets?view=${encodeURIComponent(view.name)}`);
      await page.getByRole("button", { name: "List", exact: true }).click();
      await expect(page.getByRole("menuitem", { name: view.label })).toHaveCount(0);

      const managerPage = await pageAs("customerManager");
      await managerPage.goto("/help/customer-tickets");
      await managerPage.getByRole("button", { name: "List", exact: true }).click();
      await expect(managerPage.getByRole("menuitem", { name: view.label })).toBeVisible();
    } finally {
      await manager.delete("HD View", view.name);
    }
  });
});
