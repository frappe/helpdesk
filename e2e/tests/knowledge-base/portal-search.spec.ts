import type { Page } from "@playwright/test";
import { runScheduledJob, type Api } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import { createArticle, createCategory } from "../../helpers/portal";

usePersona("customer");

/** A word no other article holds, so a search finds only this test's articles. */
const token = () => `kbs${uid()}`;

/** New articles reach RediSearch through a queued job; wait until all of them are found. */
async function waitForIndex(api: Api, query: string, total: number) {
  await runScheduledJob(api, "helpdesk.search.build_index_if_not_exists");
  await expect
    .poll(
      async () =>
        (await api.callGet("helpdesk.api.knowledge_base.search_articles", { query, start: "0" })).total,
      { timeout: 30_000, intervals: [1_000] }
    )
    .toBe(total);
}

function searchBox(page: Page) {
  return page.getByRole("textbox", { name: "Search articles" }).last();
}

function results(page: Page) {
  return page.locator("a[href*='/articles/']").filter({ has: page.locator("mark") });
}

async function forgetHistory(page: Page) {
  await page.evaluate(() =>
    Object.keys(localStorage)
      .filter((key) => key.startsWith("helpdesk-kb-recent-articles"))
      .forEach((key) => localStorage.removeItem(key))
  );
}

test.describe("knowledge base search page", () => {
  test("a query shows highlighted results, stays in the URL and survives a reload", async ({ page, api }) => {
    const word = token();
    const category = await createCategory(api);
    await createArticle(api, category.name, { title: `${word} refunds` });
    await waitForIndex(api, word, 1);

    await page.goto("/help/search");
    await expect(searchBox(page)).toBeFocused();
    await expect(page).toHaveTitle("Search");
    await searchBox(page).fill(word);
    await expect(page).toHaveURL(new RegExp(`/help/search\\?q=${word}$`));
    await expect(results(page)).toHaveCount(1);
    await expect(results(page).locator("mark").first()).toHaveText(word);
    await expect(page.getByText("1 article", { exact: true })).toBeVisible();
    await expect(page).toHaveTitle(`${word} – Search`);

    await page.reload();
    await expect(searchBox(page)).toHaveValue(word);
    await expect(results(page)).toHaveCount(1);

    await page.getByRole("button", { name: "Clear search" }).click();
    await expect(searchBox(page)).toHaveValue("");
    await expect(page).toHaveURL(/\/help\/search$/);

    await searchBox(page).blur();
    await page.keyboard.press("/");
    await expect(searchBox(page)).toBeFocused();
  });

  test("the Category filter lists categories with results, includes subcategories, and chips remove it", async ({
    page,
    api,
  }) => {
    const word = token();
    const parent = await createCategory(api);
    const sub = await createCategory(api, undefined, { parent_article_category: parent.name });
    const other = await createCategory(api);
    const unrelated = await createCategory(api);
    await createArticle(api, parent.name, { title: `${word} parent` });
    const nested = await createArticle(api, sub.name, { title: `${word} nested` });
    await createArticle(api, other.name, { title: `${word} other` });
    await createArticle(api, unrelated.name);
    await waitForIndex(api, word, 3);

    await page.goto(`/help/search?q=${word}`);
    await expect(results(page)).toHaveCount(3);
    await page.getByRole("button", { name: "Category", exact: true }).click();
    const options = page.getByRole("option");
    await expect(options).toHaveCount(3);
    await expect(options.filter({ hasText: parent.category_name }).first()).toContainText("2");
    await expect(options.filter({ hasText: `${parent.category_name} › ${sub.category_name}` })).toContainText("1");
    await expect(options.filter({ hasText: unrelated.category_name })).toHaveCount(0);

    await options.filter({ hasText: new RegExp(`^${parent.category_name}\\s*2$`) }).click();
    await page.keyboard.press("Escape");
    await expect(page).toHaveURL(new RegExp(`category=${encodeURIComponent(parent.name)}`));
    await expect(results(page)).toHaveCount(2);
    await expect(results(page).filter({ hasText: nested.title })).toHaveCount(1);
    await expect(page.getByRole("button", { name: "Category · 1" })).toBeVisible();

    await page.getByRole("button", { name: `Remove filter ${parent.category_name}` }).click();
    await expect(results(page)).toHaveCount(3);
    await expect(page).toHaveURL(new RegExp(`/help/search\\?q=${word}$`));
  });

  test("an unknown category from the URL is dropped", async ({ page, api }) => {
    const word = token();
    const category = await createCategory(api);
    await createArticle(api, category.name, { title: `${word} kept` });
    await waitForIndex(api, word, 1);

    await page.goto(`/help/search?q=${word}&category=no-such-category`);
    await expect(results(page)).toHaveCount(1);
    await expect(page.getByRole("button", { name: /^Remove filter/ })).toHaveCount(0);
    await expect(page).toHaveURL(new RegExp(`/help/search\\?q=${word}$`));
  });

  test("a category from the URL stays selected while a query has no matches in it", async ({ page, api }) => {
    const word = token();
    const elsewhere = token();
    const category = await createCategory(api);
    const other = await createCategory(api);
    const inside = await createArticle(api, category.name, { title: `${word} inside` });
    await createArticle(api, other.name, { title: `${elsewhere} elsewhere` });
    await waitForIndex(api, word, 1);
    await waitForIndex(api, elsewhere, 1);

    await page.goto(`/help/search?category=${category.name}`);
    await searchBox(page).fill(elsewhere);
    await expect(page.getByText(`No articles match “${elsewhere}”`)).toBeVisible();
    const chip = page.getByRole("button", { name: `Remove filter ${category.category_name}` });
    await expect(chip).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`category=${encodeURIComponent(category.name)}`));

    await searchBox(page).fill(word);
    await expect(results(page)).toHaveCount(1);
    await expect(results(page).filter({ hasText: inside.title })).toHaveCount(1);
    await expect(chip).toBeVisible();
  });

  test("the page follows Gameplan's search layout", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/help/search");
    const box = await searchBox(page).evaluate((input) => ({
      height: input.getBoundingClientRect().height,
      fontSize: getComputedStyle(input).fontSize,
      column: input.closest("[class*='max-w-[940px]']")!.getBoundingClientRect().width,
    }));
    expect(box).toEqual({ height: 28, fontSize: "14px", column: 940 });
  });

  test("Load more adds the next 20 results and goes away at the end", async ({ page, api }) => {
    const word = token();
    const category = await createCategory(api);
    for (let index = 0; index < 25; index++) {
      await createArticle(api, category.name, { title: `${word} page ${index}` });
    }
    await waitForIndex(api, word, 25);

    await page.goto(`/help/search?q=${word}`);
    await expect(results(page)).toHaveCount(20);
    await expect(page.getByText("25 articles", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Load more" }).click();
    await expect(results(page)).toHaveCount(25);
    await expect(page.getByRole("button", { name: "Load more" })).toHaveCount(0);
  });

  test("no results offers a ticket that keeps the query", async ({ page }) => {
    await page.goto("/help/search?q=zzzz-none");
    await expect(page.getByText("No articles match “zzzz-none”")).toBeVisible();
    // The header has its own Raise a ticket, first in the page.
    await page.getByRole("button", { name: "Raise a ticket" }).last().click();
    await expect(page).toHaveURL(/\/help\/my-tickets\/new/);
    await expect(page.getByPlaceholder("A short description")).toHaveValue("zzzz-none");
  });

  test("with no query and no history it asks for a query", async ({ page }) => {
    await page.goto("/help/search");
    await forgetHistory(page);
    await page.reload();
    await expect(page.getByText("Type to search articles")).toBeVisible();

    await page.goto("/help/search?q=ab");
    await expect(page.getByText("Type to search articles")).toBeVisible();
    await expect(page.getByRole("button", { name: "Category", exact: true })).toHaveCount(0);
  });

  test("the home dropdown's See all results opens the search page", async ({ page, api }) => {
    const word = token();
    const category = await createCategory(api);
    await createArticle(api, category.name, { title: `${word} from home` });
    await waitForIndex(api, word, 1);

    await page.goto("/help");
    await page.getByPlaceholder("Search articles").first().fill(word);
    await page.getByRole("link", { name: "See all results" }).click();
    await expect(page).toHaveURL(new RegExp(`/help/search\\?q=${word}$`));
    await expect(results(page)).toHaveCount(1);
  });
});
