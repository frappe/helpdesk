import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { FormScripts, ensureTemplate } from "../../../helpers/form-script";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";

usePersona("customer");

const PIXEL = "e2e/fixtures/pixel.png";
const DATE_FIELDS = [
  { fieldname: "e2e_date", fieldtype: "Date" },
  { fieldname: "e2e_datetime", fieldtype: "Datetime" },
];

async function useTemplate(api: Api, rows: Record<string, any>[], extra: Record<string, any> = {}) {
  const before = await api.get("HD Ticket Template", "Default");
  await api.update("HD Ticket Template", "Default", {
    fields: rows.map((row) => ({ visible_to: "Everyone", required: 0, ...row })),
    ...extra,
  });
  return () =>
    api.update("HD Ticket Template", "Default", {
      fields: before.fields,
      about: before.about || "",
      description_template: before.description_template || "",
    });
}

async function ensureDateFields(api: Api) {
  for (const field of DATE_FIELDS) {
    if (await api.exists("Custom Field", { name: `HD Ticket-${field.fieldname}` })) continue;
    await api.insert("Custom Field", {
      dt: "HD Ticket",
      label: field.fieldname.replace("e2e_", "E2E "),
      insert_after: "description",
      ...field,
    });
  }
}

function field(page: Page, label: string) {
  return page.getByRole("combobox", { name: new RegExp(`^${label}( \\(required\\))?$`) });
}

async function pick(page: Page, label: string, option: string) {
  await field(page, label).click();
  await page.getByRole("option", { name: option, exact: true }).click();
}

async function fillBasics(page: Page, subject = `E2E walk ${uid()}`) {
  await page.getByPlaceholder("A short description").fill(subject);
  await page.locator(".ProseMirror").fill("Details");
  return subject;
}

function createButton(page: Page) {
  return page.getByRole("button", { name: "Create ticket" });
}

/** Submitting with a required field empty names it and stays on the form. */
async function expectRequired(page: Page, label: string) {
  await createButton(page).click();
  await expect(page.getByRole("alert").filter({ hasText: /^Required:/ })).toContainText(label);
  await expect(page).toHaveURL(/\/help\/my-tickets\/new/);
}

function requiredHint(page: Page) {
  return page.getByRole("alert").filter({ hasText: /^Required:/ });
}

test.describe("template", () => {
  test("about, description template and required subject", async ({ page, api }) => {
    const restore = await useTemplate(api, [], {
      about: "<p>Tell us what broke</p>",
      description_template: "<p>Steps to reproduce:</p>",
    });
    try {
      await page.goto("/help/my-tickets/new");
      await expect(page.getByText("Tell us what broke")).toBeVisible();
      await expect(page.locator(".ProseMirror")).toContainText("Steps to reproduce:");
      await expectRequired(page, "Subject");
      await page.getByPlaceholder("A short description").fill(`E2E ${uid()}`);
      await expect(requiredHint(page)).toBeHidden();
    } finally {
      await restore();
    }
  });

  test("link options load and a required field blocks submit", async ({ page, api }) => {
    const restore = await useTemplate(api, [{ fieldname: "ticket_type", required: 1 }]);
    try {
      await page.goto("/help/my-tickets/new");
      const subject = await fillBasics(page);
      await expectRequired(page, "Ticket Type");
      await field(page, "Ticket Type").click();
      await expect(page.getByRole("option", { name: "Bug", exact: true })).toBeVisible();
      await page.getByRole("option", { name: "Bug", exact: true }).click();
      await expect(requiredHint(page)).toBeHidden();
      await createButton(page).click();
      await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
      const [ticket] = await api.list("HD Ticket", { filters: { subject }, fields: ["ticket_type"] });
      expect(ticket.ticket_type).toBe("Bug");
    } finally {
      await restore();
    }
  });

  test("date fields use the site date format and save", async ({ page, api }) => {
    await ensureDateFields(api);
    const restore = await useTemplate(api, DATE_FIELDS.map(({ fieldname }) => ({ fieldname })));
    const format = await api.callGet("frappe.client.get_single_value", {
      doctype: "System Settings",
      field: "date_format",
    });
    try {
      await page.goto("/help/my-tickets/new");
      const subject = await fillBasics(page);
      const date = field(page, "E2E date");
      await date.fill("2026-10-15");
      await date.press("Enter");
      // the picker shows the site's own format
      expect(format).toBe("yyyy-mm-dd");
      await expect(date).toHaveValue("2026-10-15");
      await createButton(page).click();
      await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
      const [ticket] = await api.list("HD Ticket", { filters: { subject }, fields: ["e2e_date"] });
      expect(ticket.e2e_date).toBe("2026-10-15");
    } finally {
      await restore();
    }
  });

  test("depends_on, mandatory_depends_on and a hidden required field", async ({ page, api }) => {
    await ensureTemplate(api);
    const restore = await useTemplate(api, [
      { fieldname: "e2e_trigger" },
      { fieldname: "e2e_shown", required: 1 },
      { fieldname: "e2e_needed" },
    ]);
    try {
      await page.goto("/help/my-tickets/new");
      await fillBasics(page);
      await expect(page.getByText("E2E shown")).toHaveCount(0);
      // hidden, so its `required` does not block submit; abort the create to stay on the form
      await page.route("**/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new", (route) => route.abort());
      const create = page.waitForRequest("**/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new");
      await createButton(page).click();
      await create;
      await page.unroute("**/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new");
      await expect(requiredHint(page)).toBeHidden();

      await pick(page, "E2E trigger", "Show");
      await expect(page.getByRole("textbox", { name: /^E2E shown/ })).toBeVisible();
      await expect(page.getByRole("textbox", { name: /^E2E needed \(required\)/ })).toBeVisible();
      await expect(requiredHint(page)).toContainText("E2E needed");
      await page.getByRole("textbox", { name: /^E2E shown/ }).fill("x");
      await page.getByRole("textbox", { name: /^E2E needed/ }).fill("y");
      await expect(requiredHint(page)).toBeHidden();
    } finally {
      await restore();
    }
  });

  test("a form script's onChange narrows options with applyFilters", async ({ page, api }) => {
    await ensureTemplate(api);
    const restore = await useTemplate(api, [{ fieldname: "e2e_trigger" }, { fieldname: "e2e_choice" }]);
    const scripts = new FormScripts(api);
    // Not portal-flagged: the portal new page loads agent scripts (form-script.spec fixme).
    await scripts.create(
      `return { actions: [], onChange: { e2e_trigger: (value) =>
        ctx.applyFilters("e2e_choice", value === "Show" ? ["Alpha", "Beta"] : null) } };`,
      { newPage: true }
    );
    try {
      await page.goto("/help/my-tickets/new");
      await pick(page, "E2E trigger", "Show");
      await field(page, "E2E choice").click();
      await expect(page.getByRole("option")).toHaveText(["Alpha", "Beta"]);
      await page.keyboard.press("Escape");

      await pick(page, "E2E trigger", "Hide");
      await expect(field(page, "E2E choice")).toBeDisabled();
    } finally {
      await scripts.removeAll();
      await restore();
    }
  });

  test("priority shows its description as a hint", async ({ page, api }) => {
    const restore = await useTemplate(api, [{ fieldname: "priority" }]);
    const hint = `Within four hours ${uid()}`;
    await api.update("HD Ticket Priority", "High", { description: hint });
    try {
      await page.goto("/help/my-tickets/new");
      await pick(page, "Priority", "High");
      await expect(page.getByText(hint)).toBeVisible();
    } finally {
      await api.update("HD Ticket Priority", "High", { description: "" });
      await restore();
    }
  });

  test("a url_method row offers that API's options", async ({ page, api }) => {
    await ensureTemplate(api);
    const restore = await useTemplate(api, [
      { fieldname: "e2e_needed", url_method: "helpdesk.e2e_options" },
    ]);
    await page.route("**/api/method/helpdesk.e2e_options*", (route) =>
      route.fulfill({ json: { message: ["Red", { label: "Green", value: "green" }] } })
    );
    try {
      await page.goto("/help/my-tickets/new");
      await page.getByRole("button", { name: /^E2E needed/ }).or(field(page, "E2E needed")).first().click();
      await expect(page.getByRole("option")).toHaveText(["Red", "Green"]);
    } finally {
      await restore();
    }
  });
});

test.describe("attachments", () => {
  async function attach(page: Page, files: string | { name: string; mimeType: string; buffer: Buffer }) {
    await page.locator("input[type=file].sr-only").setInputFiles(files);
  }

  test("upload, remove and submit with an attachment", async ({ page, api }) => {
    await page.goto("/help/my-tickets/new");
    const subject = await fillBasics(page);
    await attach(page, PIXEL);
    await expect(page.getByRole("link", { name: "pixel.png" }).or(page.getByText("pixel.png"))).toBeVisible();
    await expect(createButton(page)).toBeEnabled();

    await attach(page, { name: "notes.txt", mimeType: "text/plain", buffer: Buffer.from("hello") });
    await expect(page.getByRole("link", { name: "notes.txt" })).toHaveAttribute("target", "_blank");
    await page
      .locator("div")
      .filter({ has: page.getByText("notes.txt") })
      .filter({ has: page.getByRole("button", { name: "Remove" }) })
      .last()
      .getByRole("button", { name: "Remove" })
      .click();
    await expect(page.getByText("notes.txt")).toHaveCount(0);

    await createButton(page).click();
    await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
    const name = page.url().split("/").pop()!;
    const files = await api.list("File", {
      filters: { attached_to_doctype: "HD Ticket", attached_to_name: name },
      fields: ["file_name", "is_private"],
    });
    expect(files).toEqual([{ file_name: "pixel.png", is_private: 1 }]);
    expect((await api.get("HD Ticket", name)).subject).toBe(subject);
  });

  test("a disallowed type is refused for a customer", async ({ page }) => {
    await page.goto("/help/my-tickets/new");
    await attach(page, { name: "evil.html", mimeType: "text/html", buffer: Buffer.from("<b>x</b>") });
    await expect(page.getByText('"evil.html" was skipped')).toBeVisible();
  });

  test("an agent may attach any type", async ({ pageAs }) => {
    const page = await pageAs("agent");
    await page.goto("/help/my-tickets/new");
    await expect(page.locator("input[type=file].sr-only")).not.toHaveAttribute("accept", /.+/);
    await attach(page, { name: "page.html", mimeType: "text/html", buffer: Buffer.from("<b>x</b>") });
    await expect(page.getByText("page.html")).toBeVisible();
    await expect(page.getByText(/was skipped/)).toHaveCount(0);
  });

  test("files can be dropped or pasted onto the page", async ({ page }) => {
    await page.goto("/help/my-tickets/new");
    const dropZone = page.getByRole("button", { name: "Drag or paste files here, or click to browse" });
    const transfer = await page.evaluateHandle(() => {
      const data = new DataTransfer();
      data.items.add(new File(["dropped"], "dropped.txt", { type: "text/plain" }));
      return data;
    });
    await dropZone.dispatchEvent("dragover", { dataTransfer: transfer });
    await dropZone.dispatchEvent("drop", { dataTransfer: transfer });
    await expect(page.getByText("dropped.txt")).toBeVisible();

    await page.evaluate(() => {
      const data = new DataTransfer();
      data.items.add(new File(["pasted"], "pasted.txt", { type: "text/plain" }));
      // a real paste targets the focused element, never the document itself
      document.body.dispatchEvent(new ClipboardEvent("paste", { clipboardData: data, bubbles: true }));
    });
    await expect(page.getByText("pasted.txt")).toBeVisible();
    await expect(page.getByText("Add more")).toBeVisible();
  });
});

test.describe("submit", () => {
  test("a failed create shows the error and stays on the form", async ({ page }) => {
    await page.route("**/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new", (route) =>
      route.fulfill({ status: 417, json: { exc_type: "ValidationError", _server_messages: JSON.stringify([JSON.stringify({ message: "E2E refused" })]) } })
    );
    await page.goto("/help/my-tickets/new");
    await fillBasics(page);
    await createButton(page).click();
    await expect(page.getByText("E2E refused").first()).toBeVisible();
    await expect(page).toHaveURL(/\/help\/my-tickets\/new/);
    await expect(createButton(page)).toBeEnabled();
  });

  test("odd origins fall back safely", async ({ page, api }) => {
    const longQuery = "q".repeat(200);
    await page.goto(`/help/my-tickets/new?from=bogus&article=no-such-article&q=${longQuery}`);
    const subjectField = page.getByPlaceholder("A short description");
    await subjectField.fill(`E2E origin ${uid()}`);
    const subject = await subjectField.inputValue();
    await page.locator(".ProseMirror").fill("Where from?");
    await createButton(page).click();
    await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
    const [ticket] = await api.list("HD Ticket", {
      filters: { subject },
      fields: ["entry_point", "source_article", "source_search"],
    });
    expect(ticket.entry_point).toBe("Direct");
    expect(ticket.source_article).toBeNull();
  });

  test("search text over 140 characters is cut", async ({ page, api }) => {
    const longQuery = `${uid()} ${"q".repeat(200)}`;
    await page.goto(`/help/my-tickets/new?from=search&q=${longQuery}`);
    // cut to the 140 characters a subject holds
    const subjectField = page.getByPlaceholder("A short description");
    await expect(subjectField).toHaveValue(longQuery.slice(0, 140));
    const subject = `E2E long search ${uid()}`;
    await subjectField.fill(subject);
    await page.locator(".ProseMirror").fill("Long search");
    await createButton(page).click();
    await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
    const [ticket] = await api.list("HD Ticket", {
      filters: { subject },
      fields: ["entry_point", "source_search"],
    });
    expect(ticket.entry_point).toBe("Search");
    expect(ticket.source_search).toBe(longQuery.slice(0, 140));
  });

  test("a long search can still be raised as it is", async ({ page }) => {
    await page.goto(`/help/my-tickets/new?from=search&q=${"q".repeat(200)}`);
    await page.locator(".ProseMirror").fill("Long search");
    await createButton(page).click();
    await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/, { timeout: 5_000 });
  });
});
