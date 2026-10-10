import type { Page, Route } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { personas } from "../../../helpers/personas";
import { createArticle, createCategory } from "../../../helpers/portal";

const PIXEL = "e2e/fixtures/pixel.png";

usePersona("customer");

test.describe("raising a ticket", () => {
  test("with a custom field and an inline image", async ({ page, api }) => {
    const template = await api.get("HD Ticket Template", "Default");
    await api.update("HD Ticket Template", "Default", {
      fields: [{ fieldname: "ticket_type", required: 0, visible_to: "Everyone" }],
    });
    try {
      const subject = `E2E portal ${uid()}`;
      await page.goto("/kb/tickets/new");
      await page.getByRole("combobox", { name: "Ticket Type" }).click();
      await page.getByRole("option", { name: "Question" }).click();
      await page.getByPlaceholder("A short description").fill(subject);
      await page.locator(".ProseMirror").fill("Screenshot of the error");
      await attachImage(page);
      await page.getByRole("button", { name: "Create ticket" }).click();

      await expect(page).toHaveURL(/\/kb\/tickets\/\d+$/);
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
    await page.goto("/kb/tickets/new");
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

    await page.goto("/kb/tickets/new");
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

  test("suggests matching knowledge base articles", async ({ page, api, apiAs }) => {
    const probe = await (await apiAs("customer")).raw("helpdesk.api.article.search", { query: "probe" });
    test.skip(!probe.ok(), "article search needs RediSearch (redis-stack) on redis_cache");

    const category = await createCategory(api);
    const title = `Rotate ${uid()} credentials`;
    await createArticle(api, category.name, { title });
    await page.goto("/kb/tickets/new");
    await page.getByPlaceholder("A short description").fill(title);
    await expect(page.getByText("These articles may already cover")).toBeVisible();
    await expect(page.getByText(title).last()).toBeVisible();
  });
});

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
