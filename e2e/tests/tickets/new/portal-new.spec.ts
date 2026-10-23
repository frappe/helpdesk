import type { Page, Route } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { ensureTemplate } from "../../../helpers/form-script";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { personas } from "../../../helpers/personas";

const PIXEL = "e2e/fixtures/pixel.png";
const DEFAULTED_FIELDS = [
  { fieldname: "e2e_frozen", read_only: 1 },
  { fieldname: "e2e_answer", read_only: 0 },
].map((field) => ({ ...field, fieldtype: "Select", options: "No\nYes", default: "No" }));

usePersona("customer");

test.describe("raising a ticket", () => {
  test("with a custom field and an inline image", async ({ page, api }) => {
    const template = await api.get("HD Ticket Template", "Default");
    await api.update("HD Ticket Template", "Default", {
      fields: [{ fieldname: "ticket_type", required: 0, visible_to: "Everyone" }],
    });
    try {
      const subject = `E2E portal ${uid()}`;
      await page.goto("/help/my-tickets/new");
      await page.getByRole("combobox", { name: "Ticket Type" }).click();
      await page.getByRole("option", { name: "Question" }).click();
      await page.getByPlaceholder("A short description").fill(subject);
      await page.locator(".ProseMirror").fill("Screenshot of the error");
      await attachImage(page);
      await page.getByRole("button", { name: "Create ticket" }).click();

      await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
      const [ticket] = await api.list("HD Ticket", {
        filters: { subject },
        fields: ["description", "ticket_type", "raised_by"],
      });
      expect(ticket.description).toContain("<img");
      expect(ticket.ticket_type).toBe("Question");
      expect(ticket.raised_by).toBe(personas.customer.email);
    } finally {
      await api.update("HD Ticket Template", "Default", { fields: template.fields });
    }
  });

  test("accepts a description that is only an image", async ({ page }) => {
    await page.goto("/help/my-tickets/new");
    await page.getByPlaceholder("A short description").fill(`E2E image only ${uid()}`);
    await attachImage(page);
    await expect(page.getByRole("button", { name: "Create ticket" })).toBeEnabled();
  });

  test("keeps Create ticket disabled while an image is uploading", async ({ page }) => {
    let release: () => void = () => {};
    const held = new Promise<void>((resolve) => (release = resolve));
    await page.route("**/api/method/upload_file", async (route: Route) => {
      await held;
      await route.continue();
    });

    await page.goto("/help/my-tickets/new");
    await page.getByPlaceholder("A short description").fill(`E2E upload ${uid()}`);
    await page.locator(".ProseMirror").fill("See the screenshot");
    const submit = page.getByRole("button", { name: "Create ticket" });
    await expect(submit).toBeEnabled();

    await chooseImage(page);
    await expect(submit).toBeDisabled();
    release();
    await expect(uploadedImage(page)).toBeVisible();
    await expect(submit).toBeEnabled();
  });
});

test.describe("the form", () => {
  test("a read-only field is disabled and untouched fields keep their defaults", async ({
    page,
    api,
  }) => {
    await ensureDefaultedFields(api);
    const restore = await useTemplate(api, DEFAULTED_FIELDS);
    try {
      await page.goto("/help/my-tickets/new");
      await expect(page.getByRole("combobox", { name: /^E2E frozen/ })).toBeDisabled();
      await expect(page.getByRole("combobox", { name: /^E2E answer/ })).toBeEnabled();
      const subject = await fillBasics(page);
      await page.getByRole("button", { name: "Create ticket" }).click();

      await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
      const [ticket] = await api.list("HD Ticket", {
        filters: { subject },
        fields: ["e2e_frozen", "e2e_answer"],
      });
      expect(ticket).toEqual({ e2e_frozen: "No", e2e_answer: "No" });
    } finally {
      await restore();
    }
  });

  test("about links open in a new tab", async ({ page, api }) => {
    const restore = await useTemplate(api, [], {
      about: '<p><a href="https://example.com/register" target="_blank">Register your site</a></p>',
    });
    try {
      await page.goto("/help/my-tickets/new");
      const link = page.getByRole("link", { name: "Register your site" });
      await expect(link).toHaveAttribute("target", "_blank");
      await expect(link).toHaveAttribute("rel", "noopener noreferrer");
    } finally {
      await restore();
    }
  });

  test("says what is still required on submit and ignores a blank subject", async ({ page }) => {
    let creates = 0;
    page.on("request", (request) => request.url().includes("hd_ticket.api.new") && creates++);
    await page.goto("/help/my-tickets/new");
    const hint = page.getByRole("alert").filter({ hasText: /^Required:/ });
    const submit = page.getByRole("button", { name: "Create ticket" });
    await expect(hint).toBeHidden();
    await expect(submit).toBeEnabled();

    await submit.click();
    await expect(hint).toHaveText("Required: Subject, Description");
    await page.getByPlaceholder("A short description").fill("   ");
    await page.locator(".ProseMirror").fill("Details");
    await expect(hint).toHaveText("Required: Subject");
    await submit.click();
    expect(creates).toBe(0);
    await page.getByPlaceholder("A short description").fill(`E2E ${uid()}`);
    await expect(hint).toBeHidden();
  });

  test("a url_method field asks to select an option", async ({ page, api }) => {
    await ensureTemplate(api);
    const restore = await useTemplate(api, [
      { fieldname: "e2e_needed", url_method: "helpdesk.e2e_options" },
    ]);
    await page.route("**/api/method/helpdesk.e2e_options*", (route) =>
      route.fulfill({ json: { message: ["Red"] } })
    );
    try {
      await page.goto("/help/my-tickets/new");
      const picker = page.locator('[data-fieldname="e2e_needed"] button').first();
      await expect(picker).toContainText("Select an option");
    } finally {
      await restore();
    }
  });

  test("creating a ticket confirms with a toast", async ({ page }) => {
    await page.goto("/help/my-tickets/new");
    await fillBasics(page);
    await page.getByRole("button", { name: "Create ticket" }).click();
    await expect(page.getByText("Ticket created")).toBeVisible();
  });

  test("the editor does not offer Embed", async ({ page }) => {
    await page.goto("/help/my-tickets/new");
    await expect(page.getByRole("button", { name: "Image", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Embed" })).toHaveCount(0);
  });
});

async function ensureDefaultedFields(api: Api) {
  for (const field of DEFAULTED_FIELDS) {
    if (await api.exists("Custom Field", { name: `HD Ticket-${field.fieldname}` })) continue;
    await api.insert("Custom Field", {
      dt: "HD Ticket",
      label: field.fieldname.replace("e2e_", "E2E "),
      insert_after: "description",
      ...field,
    });
  }
}

async function useTemplate(api: Api, rows: Record<string, any>[], extra: Record<string, any> = {}) {
  const before = await api.get("HD Ticket Template", "Default");
  await api.update("HD Ticket Template", "Default", {
    fields: rows.map(({ fieldname, url_method }) => ({
      fieldname,
      url_method,
      visible_to: "Everyone",
      required: 0,
    })),
    ...extra,
  });
  return () =>
    api.update("HD Ticket Template", "Default", {
      fields: before.fields,
      about: before.about || "",
    });
}

async function fillBasics(page: Page) {
  const subject = `E2E form ${uid()}`;
  await page.getByPlaceholder("A short description").fill(subject);
  await page.locator(".ProseMirror").fill("Details");
  return subject;
}

async function chooseImage(page: Page) {
  const chooser = page.waitForEvent("filechooser");
  await page.getByRole("button", { name: "Image", exact: true }).click();
  await (await chooser).setFiles(PIXEL);
}

async function attachImage(page: Page) {
  await chooseImage(page);
  await expect(uploadedImage(page)).toBeVisible();
}

function uploadedImage(page: Page) {
  return page.locator('.ProseMirror img[src*="/files/"]');
}
