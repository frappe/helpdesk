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

const running = (done: number, total = 3, stage = "reading") => ({
  state: "running",
  stage,
  done,
  total,
  host: HOST,
});
const finished = (category: string, created = 3, skipped = 0, failed = 0) => ({
  state: "done",
  created,
  skipped,
  failed,
  host: HOST,
  category,
});

/** Answer the two import calls. `results` are served in order after the import starts, the last one repeating. */
async function mockImport(page: Page, results: Result[]) {
  let started = false;
  let polls = 0;
  await page.route("**/api/method/helpdesk.api.docs_source.import_docs", (route) => {
    started = true;
    return route.fulfill({ json: { message: running(0) } });
  });
  await page.route("**/api/method/helpdesk.api.docs_source.get_import_result", (route) => {
    const next = started ? results[Math.min(polls++, results.length - 1)] : null;
    return route.fulfill({ json: { message: next } });
  });
}

async function openDeskSettings(page: Page) {
  await page.goto("/helpdesk");
  return openSettings(page, "Knowledge Base");
}

async function openImport(page: Page) {
  const settings = await openDeskSettings(page);
  await settings.getByRole("button", { name: "Import pages" }).click();
  const dialog = page.getByRole("dialog", { name: "Import pages from a docs site" });
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

test("importing shows progress, then the three counts and a link to the drafts", async ({
  page,
  api,
}) => {
  const category = await createCategory(api);
  await mockImport(page, [running(1, 3, "finding"), running(1), running(2), finished(category.name)]);
  const { dialog } = await openImport(page);

  await expect(solidButtons(dialog)).toHaveCount(0);
  await fillForm(page, dialog, category.category_name);
  await expect(solidButtons(dialog)).toHaveCount(1);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();

  await expect(dialog.getByText("Reading page 2 of 3")).toBeVisible();
  await expect(solidButtons(dialog)).toHaveCount(0);
  await expect(dialog.getByRole("progressbar")).toBeVisible();

  const figure = (label: string) => dialog.locator("dt", { hasText: label }).locator("xpath=preceding-sibling::dd");
  await expect(figure("Added")).toHaveText("3");
  await expect(figure("Already imported")).toHaveText("0");
  await expect(figure("Couldn't read")).toHaveText("0");
  await expect(solidButtons(dialog)).toHaveCount(1);
  await expect(dialog.getByRole("link", { name: "View drafts" })).toHaveAttribute(
    "href",
    `/helpdesk/kb?category=${encodeURIComponent(category.name)}`,
  );
});

test("closing mid-run keeps the progress line in the settings row", async ({ page, api }) => {
  const category = await createCategory(api);
  await mockImport(page, [running(11, 50)]);
  const { settings, dialog } = await openImport(page);
  await fillForm(page, dialog, category.category_name);
  await dialog.getByRole("button", { name: "Import", exact: true }).click();
  await expect(dialog.getByText("Reading page 12 of 50")).toBeVisible();

  await dialog.getByRole("button", { name: "Close", exact: true }).first().click();
  await expect(dialog).toBeHidden();
  const line = settings.getByRole("button", { name: `Importing from ${HOST}, 12 of 50 pages…` });
  await expect(line).toBeVisible();

  await line.click();
  await expect(dialog.getByText("Reading page 12 of 50")).toBeVisible();
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
