import { createHash } from "node:crypto";
import type { Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { createArticle, createCategory } from "../../helpers/portal";
import { openSettings } from "../../helpers/settings";

usePersona("manager");

const HOST = "docs.example.com";
const DOCS_URL = `https://${HOST}`;
const NOT_FOUND = `We couldn't find an llms.txt or sitemap.xml on ${HOST}. Check the address, or try the root of the docs site.`;

type Result = Record<string, unknown> | null;

const running = (done: number, stage = "reading") => ({
  state: "running",
  stage,
  done,
  host: HOST,
});
const finished = (category: string, created = 3, skipped = 0, unreadable: { url: string; reason: string }[] = []) => ({
  state: "done",
  created,
  skipped,
  failed: unreadable.length,
  unreadable,
  host: HOST,
  category,
});

/** Answer the two import calls. `results` are served in order after the import starts, the last one repeating. */
async function mockImport(page: Page, results: Result[]) {
  let started = false;
  let polls = 0;
  const calls = { import: 0 };
  await page.route("**/api/method/helpdesk.api.docs_source.import_docs", (route) => {
    started = true;
    calls.import++;
    return route.fulfill({ json: { message: running(0) } });
  });
  await page.route("**/api/method/helpdesk.api.docs_source.get_import_result", (route) => {
    const next = started ? results[Math.min(polls++, results.length - 1)] : null;
    return route.fulfill({ json: { message: next } });
  });
  return calls;
}

async function openDeskSettings(page: Page) {
  await page.goto("/helpdesk");
  return openSettings(page, "Knowledge Base");
}

async function openImport(page: Page) {
  const settings = await openDeskSettings(page);
  await settings.getByRole("button", { name: "Import pages" }).click();
  const dialog = page.getByRole("dialog", { name: "Import existing knowledge base" });
  await expect(dialog).toBeVisible();
  return { settings, dialog };
}

async function fillForm(page: Page, dialog: ReturnType<Page["getByRole"]>, category: string) {
  await dialog.getByRole("textbox", { name: /Docs site address/ }).fill(DOCS_URL);
  await dialog.getByRole("combobox", { name: /Add the drafts to/ }).click();
  await page.getByRole("combobox").last().fill(category);
  await page.getByRole("option", { name: category }).first().click();
}

const solidButtons = (scope: ReturnType<Page["getByRole"]>) =>
  scope.locator("button.bg-surface-gray-10, a.bg-surface-gray-10");

/** Labels of the solid buttons on the page that sit outside `dialog`. */
async function solidBehind(page: Page, dialog: ReturnType<Page["getByRole"]>) {
  const handle = await dialog.elementHandle();
  return page
    .locator("button.bg-surface-gray-10, a.bg-surface-gray-10")
    .evaluateAll((els, root) => els.filter((el) => !root!.contains(el)).map((el) => el.textContent?.trim()), handle);
}

test("importing shows progress, then success and a link to the drafts", async ({
  page,
  api,
}) => {
  const category = await createCategory(api);
  await mockImport(page, [running(0, "finding"), running(1), running(2), finished(category.name)]);
  const { dialog } = await openImport(page);

  await expect(solidButtons(dialog)).toHaveCount(0);
  await fillForm(page, dialog, category.category_name);
  await expect(solidButtons(dialog)).toHaveCount(1);
  expect(await solidBehind(page, dialog)).toEqual(["Save"]);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();

  await expect(dialog.getByText(`Read 1 page on ${HOST}…`)).toBeVisible();
  await expect(solidButtons(dialog)).toHaveCount(0);
  await expect(dialog.getByRole("progressbar")).toBeVisible();

  await expect(dialog.getByText(`Imported 3 pages as drafts in ${category.category_name}.`)).toBeVisible();
  await expect(dialog.getByRole("img")).toHaveCount(0);
  await expect(dialog.getByText(/couldn't be read/)).toHaveCount(0);
  await expect(solidButtons(dialog)).toHaveCount(1);
  await expect(dialog.getByRole("link", { name: "View drafts" })).toHaveAttribute(
    "href",
    `/helpdesk/kb?category=${encodeURIComponent(category.name)}`,
  );
});

test("pages that couldn't be read are listed with why, behind one click", async ({ page, api }) => {
  const category = await createCategory(api);
  const unreadable = [
    { url: `${DOCS_URL}/guide/billing.md`, reason: "not_found" },
    { url: `${DOCS_URL}/guide/empty.md`, reason: "empty" },
  ];
  await mockImport(page, [finished(category.name, 1, 2, unreadable)]);
  const { dialog } = await openImport(page);
  await fillForm(page, dialog, category.category_name);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();

  await expect(dialog.getByText(`5 pages checked on ${HOST}`)).toBeVisible();
  await expect(dialog.getByRole("img", { name: "1 new, 2 skipped, 2 failed" })).toBeVisible();
  const link = dialog.getByRole("link", { name: "/guide/billing.md" });
  await expect(link).toBeHidden();
  await dialog.getByText("2 pages couldn't be read").click();
  await expect(link).toHaveAttribute("href", unreadable[0].url);
  await expect(dialog.getByText("Page not found")).toBeVisible();
  await expect(dialog.getByText("No text on the page")).toBeVisible();
});

test("a new category named after the site can be picked", async ({ page }) => {
  let sent: Record<string, string> = {};
  await page.route("**/api/method/helpdesk.api.docs_source.import_docs", (route) => {
    sent = route.request().postDataJSON();
    return route.fulfill({ json: { message: running(0) } });
  });
  await page.route("**/api/method/helpdesk.api.docs_source.get_import_result", (route) =>
    route.fulfill({ json: { message: sent.url ? running(0) : null } }),
  );
  const { dialog } = await openImport(page);
  await dialog.getByRole("textbox", { name: /Docs site address/ }).fill(DOCS_URL);
  await dialog.getByRole("combobox", { name: /Add the drafts to/ }).click();
  await page.getByRole("option", { name: "New category: Example" }).click();
  await dialog.getByRole("button", { name: "Import", exact: true }).click();
  await expect(dialog.getByText(`Read 0 pages on ${HOST}…`)).toBeVisible();
  expect(sent).toEqual({ url: DOCS_URL, new_category: "Example" });
});

test("closing mid-run keeps the progress line in the settings row", async ({ page, api }) => {
  const category = await createCategory(api);
  await mockImport(page, [running(11)]);
  const { settings, dialog } = await openImport(page);
  await fillForm(page, dialog, category.category_name);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();
  await expect(dialog.getByText(`Read 11 pages on ${HOST}…`)).toBeVisible();

  await dialog.getByRole("button", { name: "Close", exact: true }).first().click();
  await expect(dialog).toBeHidden();
  const line = settings.getByRole("button", { name: `Importing from ${HOST}, 11 pages read…` });
  await expect(line).toBeVisible();

  await line.click();
  await expect(dialog.getByText(`Read 11 pages on ${HOST}…`)).toBeVisible();
});

test("a failed import shows plain words and Try again keeps the address", async ({ page, api }) => {
  const category = await createCategory(api);
  await mockImport(page, [{ state: "error", message: NOT_FOUND, host: HOST }]);
  const { dialog } = await openImport(page);
  await fillForm(page, dialog, category.category_name);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();

  await expect(dialog.getByText(NOT_FOUND)).toBeVisible();
  await expect(dialog).not.toContainText(/server|exception/i);
  await expect(solidButtons(dialog)).toHaveCount(1);
  await dialog.getByRole("button", { name: "Try again" }).click();
  await expect(dialog.getByText(NOT_FOUND)).toBeHidden();
  await expect(dialog.getByRole("textbox", { name: /Docs site address/ })).toHaveValue(DOCS_URL);
  await expect(dialog.getByRole("button", { name: "Import", exact: true })).toBeEnabled();
});

test("a failed start call shows plain words, never server text", async ({ page, api }) => {
  const category = await createCategory(api);
  await page.route("**/api/method/helpdesk.api.docs_source.get_import_result", (route) =>
    route.fulfill({ json: { message: null } }),
  );
  await page.route("**/api/method/helpdesk.api.docs_source.import_docs", (route) =>
    route.fulfill({ status: 500, json: { exception: "Traceback: boom", exc_type: "ValueError" } }),
  );
  const { dialog } = await openImport(page);
  await fillForm(page, dialog, category.category_name);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();

  await expect(dialog.getByText("We couldn't start the import. Check your connection and try again.")).toBeVisible();
  await expect(dialog).not.toContainText(/server|exception|traceback|boom/i);
});

test("Enter in the address field starts the import, Enter on a category does not", async ({ page, api }) => {
  const category = await createCategory(api);
  const calls = await mockImport(page, [running(0)]);
  const { dialog } = await openImport(page);
  const address = dialog.getByRole("textbox", { name: /Docs site address/ });
  await address.fill(DOCS_URL);
  await dialog.getByRole("combobox", { name: /Add the drafts to/ }).click();
  await page.getByRole("combobox").last().fill(category.category_name);
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  expect(calls.import).toBe(0);

  await address.press("Enter");
  await expect(dialog.getByText(`Read 0 pages on ${HOST}…`)).toBeVisible();
  expect(calls.import).toBe(1);
});

test("on a phone the dialog fits and the counts stay inside it", async ({ page, api }) => {
  const category = await createCategory(api);
  await page.setViewportSize({ width: 390, height: 844 });
  const longPath = { url: `${DOCS_URL}/a-very/long/path/to/one/page.md`, reason: "timed_out" };
  await mockImport(page, [finished(category.name, 12, 3, [longPath])]);
  const { dialog } = await openImport(page);
  await fillForm(page, dialog, category.category_name);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();

  await expect(dialog.getByRole("img", { name: "12 new, 3 skipped, 1 failed" })).toBeVisible();
  const box = await dialog.boundingBox();
  const list = await dialog.getByRole("list").first().boundingBox();
  expect(list!.x).toBeGreaterThanOrEqual(box!.x);
  expect(list!.x + list!.width).toBeLessThanOrEqual(box!.x + box!.width);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

test.describe("edited since the copy", () => {
  async function docsArticle(
    api: Parameters<typeof createArticle>[0],
    edited: boolean,
    pageUrl = `${DOCS_URL}/e2e/${uid()}`,
  ) {
    const category = await createCategory(api);
    const article = await createArticle(api, category.name, {
      title: `E2E Docs copy ${uid()}`,
      status: "Draft",
    });
    const saved = (await api.get("HD Article", article.name)).content as string;
    const hash = (text: string) => createHash("sha256").update(text).digest("hex");
    await api.update("HD Article", article.name, {
      docs_page_url: pageUrl,
      docs_copied_on: "2026-01-02 10:00:00",
      docs_content_hash: hash(edited ? `${saved} older` : saved),
    });
    return article;
  }

  test("an article changed after the copy says so, an untouched one does not", async ({ page, api }) => {
    const changed = await docsArticle(api, true);
    await page.goto(`/helpdesk/kb/articles/${changed.name}`);
    await expect(page.getByText(/Copied from docs on/)).toBeVisible();
    await expect(page.getByText("Edited since")).toBeVisible();

    const untouched = await docsArticle(api, false);
    await page.goto(`/helpdesk/kb/articles/${untouched.name}`);
    await expect(page.getByText(/Copied from docs on/)).toBeVisible();
    await expect(page.getByText("Edited since")).toHaveCount(0);
  });

  test("a stored link that is not https is never rendered as a link", async ({ page, api }) => {
    const article = await docsArticle(api, false, "javascript:alert(1)");
    await page.goto(`/helpdesk/kb/articles/${article.name}`);
    await expect(page.getByRole("heading").first()).toBeVisible();
    await expect(page.getByText(/Copied from docs on/)).toHaveCount(0);
    await expect(page.locator('a[href^="javascript:"]')).toHaveCount(0);
  });
});
