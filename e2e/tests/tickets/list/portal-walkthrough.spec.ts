import type { Page } from "@playwright/test";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { PASSWORD, personas } from "../../../helpers/personas";
import { siteHeader } from "../../../helpers/site";

usePersona("customer");

/** Tickets share one token, so the Subject quick filter isolates them. */
async function raiseBatch(apiAs, count = 1) {
  const token = uid();
  const customer = await apiAs("customer");
  const tickets = [];
  for (let i = 0; i < count; i++) tickets.push(await raiseTicket(customer, `${token} walk ${i}`));
  return { token, tickets };
}

async function narrowTo(page: Page, token: string) {
  // A fill before the list mounts is wiped by the initial restore.
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
    await page.goto("/help/my-tickets");
    const menu = page.getByRole("button", { name: "Helpdesk" });

    await menu.click();
    await expect(page.getByRole("menuitem", { name: "Agent portal" })).toHaveCount(0);
    await page.getByRole("menuitem", { name: "Home" }).click();
    await expect(page).toHaveURL(/\/help\/?$/);

    await menu.click();
    await page.getByRole("menuitem", { name: "My tickets" }).click();
    await expect(page).toHaveURL(/\/help\/my-tickets/);

    await menu.click();
    await page.getByRole("menuitem", { name: "Settings" }).click();
    await expect(page).toHaveURL(/\/settings\/profile$/);
    await expect(page.getByRole("dialog")).toBeVisible();
  });

  test("an agent's menu also links to the agent portal", async ({ pageAs }) => {
    const page = await pageAs("agent");
    await page.goto("/help/my-tickets");
    await page.getByRole("button", { name: "Helpdesk" }).click();
    await page.getByRole("menuitem", { name: "Agent portal" }).click();
    await expect(page).toHaveURL(/\/helpdesk/);
  });

  test("log out returns to the portal home", async ({ browser, baseURL }) => {
    // Own session: logging out would end the shared one.
    const context = await browser.newContext({ baseURL, extraHTTPHeaders: siteHeader() });
    const page = await context.newPage();
    await page.request.post("/api/method/login", {
      form: { usr: personas.customer.email, pwd: PASSWORD },
    });
    await page.goto("/help/my-tickets");
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
    await page.goto("/help/my-tickets");
    await narrowTo(page, token);
    await expect(row(page, tickets[0].subject)).toBeVisible();
  });

  test("default columns and opening a row", async ({ page, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs);
    await page.goto("/help/my-tickets");
    for (const heading of ["ID", "Subject", "Status", "Priority", "First Response", "Resolution", "Created"]) {
      await expect(page.getByText(heading, { exact: true }).first()).toBeVisible();
    }
    await narrowTo(page, token);
    await row(page, tickets[0].subject).click();
    await expect(page).toHaveURL(new RegExp(`/help/my-tickets/${tickets[0].name}$`));
  });

  test("a ticket an agent changed reads unread until the customer opens it", async ({ page, api, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs);
    // any save by someone else resets `_seen` to them
    await api.update("HD Ticket", tickets[0].name, { priority: "High" });
    await page.goto("/help/my-tickets");
    await narrowTo(page, token);
    const subject = () => row(page, tickets[0].subject).getByText(tickets[0].subject);
    await expect(subject()).toHaveClass(/font-semibold/);

    await row(page, tickets[0].subject).click();
    await expect(page.getByRole("button", { name: "Close" })).toBeVisible();
    await page.getByRole("link", { name: "Tickets" }).click();
    await expect(subject()).not.toHaveClass(/font-semibold/, { timeout: 5_000 });
  });

  test("refresh picks up a ticket raised after the list loaded", async ({ page, apiAs }) => {
    const { token } = await raiseBatch(apiAs);
    await page.goto("/help/my-tickets");
    await narrowTo(page, token);
    const later = await raiseTicket(await apiAs("customer"), `${token} later`);
    await expect(row(page, later.subject)).toHaveCount(0);
    await page.getByRole("button", { name: "Refresh" }).click();
    await expect(row(page, later.subject)).toBeVisible();
  });

  test("filter narrows the list and explains an empty result", async ({ page, api, apiAs }) => {
    const { token, tickets } = await raiseBatch(apiAs, 2);
    await page.goto("/help/my-tickets");
    await narrowTo(page, token);
    await expect(row(page, token)).toHaveCount(2);

    await api.update("HD Ticket", tickets[0].name, { status: "Closed" });
    await page.getByRole("button", { name: "Filter", exact: true }).click();
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
    await page.goto("/help/my-tickets");
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
    await page.goto("/help/my-tickets");
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
    // own tickets: backend suites may have deleted everyone else's
    const { token } = await raiseBatch(apiAs, 51);
    await page.goto("/help/my-tickets");
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
    await page.goto("/help/my-tickets");
    await narrowTo(page, token);
    await row(page, tickets[0].subject).getByRole("checkbox").check();
    await expect(page).toHaveURL(/my-tickets/);
    await expect(page.getByText(/1 row selected/)).toBeVisible();
    expect(errors).toEqual([]);
  });

  test("filters are remembered when coming back", async ({ page, apiAs }) => {
    const { token } = await raiseBatch(apiAs);
    await page.goto("/help/my-tickets");
    await narrowTo(page, token);
    await page.goto("/help");
    await page.getByRole("button", { name: "Helpdesk" }).click();
    await page.getByRole("menuitem", { name: "My tickets" }).click();
    await expect(page.getByRole("textbox", { name: "Subject" })).toHaveValue(token);
    await expect(page.getByRole("button", { name: new RegExp(`${token} walk`) })).toHaveCount(1);
  });

  test("organisation switcher is hidden for a single organisation", async ({ page }) => {
    await page.goto("/help/my-tickets");
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
      await page.goto("/help/my-tickets");
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

  test("list rows open the ticket; no quick filters or column settings", async ({ page, apiAs }) => {
    const { tickets } = await raiseBatch(apiAs);
    await page.goto("/help/my-tickets");
    // the same list view as on a desktop, as the old desk portal did
    await expect(row(page, tickets[0].subject)).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Subject" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Columns" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Refresh" })).toBeVisible();
    await row(page, tickets[0].subject).click();
    await expect(page).toHaveURL(new RegExp(`/help/my-tickets/${tickets[0].name}$`));
  });
});

test.describe("saved views", () => {
  async function openViews(page: Page, current = "List") {
    await page.getByRole("button", { name: current, exact: true }).click();
  }

  function viewsMenu(page: Page) {
    // Not by role: under a dialog the stuck menu is aria-hidden yet painted.
    return page.getByText("Create View", { exact: true });
  }

  async function viewAction(page: Page, label: string, action: string) {
    await openViews(page, label);
    const item = page.getByRole("menuitem", { name: label });
    await item.hover();
    await item.getByRole("button", { name: "View actions" }).click();
    await page.getByRole("menuitem", { name: action }).click();
  }

  test("a view action closes the views menu", async ({ page, api }) => {
    await page.goto("/help/my-tickets");
    await expect(page.getByRole("button", { name: /^\d{4} / }).first()).toBeVisible();
    const label = `E2E view ${uid()}`;
    await openViews(page);
    await viewsMenu(page).click();
    await page.getByPlaceholder("My open tickets").fill(label);
    await page.getByPlaceholder("My open tickets").press("Enter");
    await expect.poll(() => new URL(page.url()).searchParams.get("view")).toBeTruthy();
    const name = new URL(page.url()).searchParams.get("view")!;
    try {
      await viewAction(page, label, "Delete");
      await expect(viewsMenu(page)).toBeHidden({ timeout: 3_000 });
    } finally {
      await api.delete("HD View", name).catch(() => {});
    }
  });

  test("List keeps resized and added columns; a changed view offers Save Changes", async ({ page, api }) => {
    const header = page.locator("[style*='grid-template-columns']").first();
    const grid = () => header.evaluate((el: HTMLElement) => el.style.gridTemplateColumns);
    const save = page.getByRole("button", { name: "Save Changes" });
    async function drag(index: number, dx: number) {
      const box = (await page.locator(".cursor-col-resize").nth(index).boundingBox())!;
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down();
      await page.mouse.move(box.x + dx, box.y, { steps: 5 });
      await page.mouse.up();
    }

    await page.goto("/help/my-tickets");
    await expect(page.getByRole("button", { name: /^\d{4} / }).first()).toBeVisible();
    await drag(1, -100);
    await page.getByRole("button", { name: "Columns" }).click();
    await page.getByRole("dialog", { name: "Columns" }).getByRole("button", { name: "Add Column" }).click();
    await page.getByRole("option", { name: "Ticket Type", exact: true }).click();
    await page.keyboard.press("Escape");
    // fixed width: an `fr` column lets the `auto` ID column size per row
    await expect.poll(grid).toMatch(/px .* 10rem$/);
    const listGrid = await grid();
    await page.reload();
    await expect(page.getByRole("button", { name: /^\d{4} / }).first()).toBeVisible();
    await expect.poll(grid).toBe(listGrid);
    await expect(save).toBeHidden();

    await openViews(page);
    await page.getByRole("menuitem", { name: "Create View" }).click();
    await page.getByPlaceholder("My open tickets").fill(`E2E view ${uid()}`);
    await page.getByPlaceholder("My open tickets").press("Enter");
    await expect.poll(() => new URL(page.url()).searchParams.get("view")).toBeTruthy();
    const name = new URL(page.url()).searchParams.get("view")!;
    try {
      await expect(page.getByText('View created')).toBeVisible();
      await expect(save).toBeHidden();
      await drag(2, 80);
      await expect(save).toBeVisible();
      await save.click();
      await expect(save).toBeHidden();
      expect(JSON.parse((await api.get("HD View", name)).columns)[2].width).toMatch(/px$/);
    } finally {
      await api.delete("HD View", name);
    }
  });

  test("a view saved by the old portal opens; its auto-saved list state stays hidden", async ({
    page,
    api,
    apiAs,
  }) => {
    const { token } = await raiseBatch(apiAs, 2);
    const customer = await apiAs("customer");
    const legacy = {
      doctype: "HD View",
      dt: "HD Ticket",
      type: "list",
      route_name: "TicketsCustomer",
      is_customer_portal: 1,
      filters: JSON.stringify({ subject: ["LIKE", `%${token}%`] }),
      columns: JSON.stringify([
        { label: "ID", type: "Int", key: "name", width: "5rem" },
        { label: "Subject", type: "Data", key: "subject", width: "25rem" },
      ]),
    };
    const label = `E2E legacy ${uid()}`;
    const named = await customer.insert<{ name: string }>("HD View", { ...legacy, label });
    const bare = await customer.insert<{ name: string }>("HD View", {
      ...legacy,
      label: `E2E bare ${uid()}`,
      columns: "[]",
    });
    const autoSaved = await customer.insert<{ name: string }>("HD View", {
      ...legacy,
      label: `E2E auto ${uid()}`,
      is_default: 1,
    });
    const errors: Error[] = [];
    page.on("pageerror", (error) => errors.push(error));
    try {
      await page.goto(`/help/my-tickets?view=${encodeURIComponent(named.name)}`);
      await expect(page.getByRole("button", { name: new RegExp(`${token} walk`) })).toHaveCount(2);
      await expect(page.getByRole("button", { name: /^\d{4} / })).toHaveCount(2);
      const header = page.locator("[style*='grid-template-columns']").first();
      await expect(header).toContainText("Subject");
      await expect(header).not.toContainText("Status");

      await openViews(page, label);
      await expect(page.getByRole("menuitem", { name: label })).toBeVisible();
      await expect(page.getByRole("menuitem", { name: /^E2E auto / })).toHaveCount(0);

      await page.goto(`/help/my-tickets?view=${encodeURIComponent(bare.name)}`);
      await expect(page.getByRole("button", { name: new RegExp(`${token} walk`) })).toHaveCount(2);
      for (const column of ["ID", "Status", "First Response", "Created"]) {
        await expect(header).toContainText(column);
      }
      await expect(page.getByRole("button", { name: "Save Changes" })).toBeHidden();
      expect(errors).toEqual([]);
    } finally {
      await api.delete("HD View", named.name);
      await api.delete("HD View", bare.name);
      await api.delete("HD View", autoSaved.name);
    }
  });

  test("a view with no saved columns shows translated headers and stays unmodified", async ({ page, api, apiAs }) => {
    const { token } = await raiseBatch(apiAs, 2);
    const isViewList = (request) =>
      /frappe\.client\.get_list/.test(request.url()) && request.postDataJSON()?.doctype === "HD View";
    // Translations land once the session is loaded, while the view is requested but not yet applied.
    const viewsRequested = page.waitForRequest(isViewList);
    await page.route(/helpdesk\.api\.general\.get_translations/, async (route) => {
      await viewsRequested;
      await route.fulfill({ json: { message: { Subject: "Asunto", Status: "Estado" } } });
    });
    let release = () => {};
    const released = new Promise<void>((resolve) => (release = resolve));
    await page.route(/frappe\.client\.get_list/, async (route) => {
      if (isViewList(route.request())) await released;
      await route.continue();
    });
    const customer = await apiAs("customer");
    const view = await customer.insert<{ name: string }>("HD View", {
      label: `E2E bare ${uid()}`,
      dt: "HD Ticket",
      type: "list",
      is_customer_portal: 1,
      filters: JSON.stringify({ subject: ["LIKE", `%${token}%`] }),
      order_by: "creation asc",
      columns: "[]",
    });
    try {
      await page.goto(`/help/my-tickets?view=${encodeURIComponent(view.name)}`);
      const header = page.locator("[style*='grid-template-columns']").first();
      await expect(header).toContainText("Asunto");
      release();
      const rows = page.getByRole("button", { name: /^\d{4} / });
      await expect(rows).toHaveCount(2);
      await expect(rows.first()).toContainText(`${token} walk 0`);
      await expect(header).toContainText("Asunto");
      await expect(header).toContainText("Estado");
      await expect(page.getByRole("button", { name: "Save Changes" })).toBeHidden();
    } finally {
      await api.delete("HD View", view.name);
    }
  });

  test("save, open, update, rename and delete a view", async ({ page, api, apiAs }) => {
    const { token } = await raiseBatch(apiAs, 2);
    const label = `E2E view ${uid()}`;
    await page.goto("/help/my-tickets");
    await narrowTo(page, token);

    await openViews(page);
    await page.getByRole("menuitem", { name: "Create View" }).click();
    const dialog = page.getByRole("dialog", { name: "Create View" });
    await expect(dialog.getByText("Saves the filters, sort order and columns currently on screen.")).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Create" })).toBeDisabled();
    await dialog.getByPlaceholder("My open tickets").fill(label);
    await dialog.getByPlaceholder("My open tickets").press("Enter");
    await expect(page.getByText('View created')).toBeVisible();
    await expect(page).toHaveURL(/\?view=/);
    const name = new URL(page.url()).searchParams.get("view")!;
    const saved = await api.get("HD View", name);
    expect(saved).toMatchObject({ is_customer_portal: 1, owner: personas.customer.email, icon: "text-align-justify" });
    expect(saved.filters).toContain(token);

    await openViews(page, label);
    await page.getByRole("menuitem", { name: "List" }).click();
    await expect(page).not.toHaveURL(/\?view=/);
    await openViews(page);
    await page.getByRole("menuitem", { name: label }).click();
    await expect.poll(() => new URL(page.url()).searchParams.get("view")).toBe(name);
    await expect(page.getByRole("button", { name: new RegExp(`${token} walk`) })).toHaveCount(2);

    await page.goto(`/help/my-tickets?view=${encodeURIComponent(name)}`);
    await expect(page.getByRole("button", { name: label, exact: true })).toBeVisible();

    await page.getByRole("button", { name: "Created On" }).click();
    await page.getByRole("dialog", { name: "Created On" }).getByRole("button").first().click();
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: "Save Changes" }).click();
    await expect(page.getByText("View updated")).toBeVisible();
    await expect.poll(async () => (await api.get("HD View", name)).order_by).toBe("creation asc");

    await viewAction(page, label, "Rename");
    const nameField = page.getByPlaceholder("My open tickets");
    await expect(nameField).toHaveValue(label);
    await nameField.fill(`${label} renamed`);
    await nameField.press("Enter");
    await expect.poll(async () => (await api.get("HD View", name)).label).toBe(`${label} renamed`);
    await expect(page.getByText(`${label} renamed`, { exact: true }).first()).toBeVisible();

    await page.getByText(`${label} renamed`, { exact: true }).first().click();
    const renamed = page.getByRole("menuitem", { name: `${label} renamed` });
    await renamed.hover();
    await renamed.getByRole("button", { name: "View actions" }).click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Delete" }).click();
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
      await page.goto(`/help/my-tickets?view=${encodeURIComponent(view.name)}`);
      await page.getByRole("button", { name: "List", exact: true }).click();
      await expect(page.getByRole("menuitem", { name: view.label })).toHaveCount(0);

      const managerPage = await pageAs("customerManager");
      await managerPage.goto("/help/my-tickets");
      await managerPage.getByRole("button", { name: "List", exact: true }).click();
      await expect(managerPage.getByRole("menuitem", { name: view.label })).toBeVisible();
    } finally {
      await manager.delete("HD View", view.name);
    }
  });

  test("a link to a missing view remembers changes on the fallback List", async ({ page, apiAs }) => {
    const { token } = await raiseBatch(apiAs);
    const missing = `/help/my-tickets?view=${encodeURIComponent(`missing-${uid()}`)}`;
    const viewsLoaded = page.waitForResponse(
      (response) =>
        /frappe\.client\.get_list/.test(response.url()) &&
        response.request().postDataJSON()?.doctype === "HD View"
    );
    await page.goto(missing);
    await viewsLoaded;
    await narrowTo(page, token);
    await page.goto("/help");
    await page.goto(missing);
    await expect(page.getByRole("textbox", { name: "Subject" })).toHaveValue(token);
  });
});
