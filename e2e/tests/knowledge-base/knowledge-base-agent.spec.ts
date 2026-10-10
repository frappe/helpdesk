import type { Page } from "@playwright/test";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import {
  createArticle,
  createCategory,
  pickOption,
} from "../../helpers/portal";

usePersona("manager");

test("create a category and article, publish it, customer can read it", async ({
  page,
  api,
  pageAs,
}) => {
  const categoryName = `E2E Category ${uid()}`;
  const title = `E2E Published ${uid()}`;
  await page.goto("/helpdesk/kb");
  await page.getByRole("button", { name: "Create" }).click();
  await page.getByRole("menuitem", { name: "Category" }).click();
  await page.getByPlaceholder("Support Issues").fill(categoryName);
  await page.getByRole("dialog").getByRole("button", { name: "Create" }).click();

  await expect(page).toHaveURL(/\/helpdesk\/kb\/articles\/\w+\?.*isEdit=1/);
  await page.getByPlaceholder("Title").fill(title);
  await page.locator(".ProseMirror").fill("Steps to reset a password");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Article updated successfully.")).toBeVisible();

  await page.getByRole("button", { name: "Publish" }).click();
  await expect(page.getByRole("button", { name: "Unpublish" })).toBeVisible();
  const [article] = await api.list("HD Article", {
    filters: { title },
    fields: ["name", "status", "category"],
  });
  expect(article.status).toBe("Published");

  const customer = await pageAs("customer");
  await customer.goto(`/help/category/${article.category}`);
  // The sidebar lists it too; the category's own list comes last.
  await customer.getByText(title).last().click();
  await expect(customer).toHaveURL(new RegExp(`/help/articles/${article.name}`));
  await expect(customer.getByText("Steps to reset a password")).toBeVisible();
});

test("edit, unpublish, move and delete an article", async ({ page, api }) => {
  const from = await createCategory(api);
  const to = await createCategory(api);
  await createArticle(api, from.name);
  const article = await createArticle(api, from.name);
  const renamed = `E2E Renamed ${uid()}`;

  await page.goto(`/helpdesk/kb/articles/${article.name}`);
  await openArticleMenu(page, "Edit");
  await page.getByPlaceholder("Title").fill(renamed);
  await page.getByRole("button", { name: "Save" }).click();
  await expect.poll(async () => (await api.get("HD Article", article.name)).title).toBe(renamed);

  await page.getByRole("button", { name: "Unpublish" }).click();
  await expect.poll(async () => (await api.get("HD Article", article.name)).status).toBe("Draft");

  await openArticleMenu(page, "Move To");
  await pickOption(page, "Category", to.category_name, { opensItself: true });
  await page.getByRole("dialog").getByRole("button", { name: "Move" }).click();
  await expect.poll(async () => (await api.get("HD Article", article.name)).category).toBe(to.name);

  // a category must keep one article, so give the target another before deleting
  await createArticle(api, to.name);
  await openArticleMenu(page, "Delete");
  await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
  await expect(page).toHaveURL(/\/helpdesk\/kb$/);
  expect(await api.exists("HD Article", { name: article.name })).toBeUndefined();
});

test("merge a category into another, then delete one", async ({ page, api }) => {
  const source = await createCategory(api);
  const target = await createCategory(api);
  const doomed = await createCategory(api);
  const moved = await createArticle(api, source.name);
  const orphan = await createArticle(api, doomed.name);

  await page.goto("/helpdesk/kb");
  await openCategoryMenu(page, source.category_name, "Merge");
  await pickOption(page, "Category", target.category_name);
  await page.getByRole("dialog").getByRole("button", { name: "Merge" }).click();
  await expect.poll(async () => (await api.get("HD Article", moved.name)).category).toBe(target.name);
  expect(await api.exists("HD Article Category", { name: source.name })).toBeUndefined();

  await openCategoryMenu(page, doomed.category_name, "Delete");
  await page.getByRole("dialog").getByRole("button", { name: "Confirm" }).click();
  await expect.poll(() => api.exists("HD Article Category", { name: doomed.name })).toBeUndefined();
  const general = await api.call("helpdesk.api.knowledge_base.get_general_category");
  expect((await api.get("HD Article", orphan.name)).category).toBe(general);
});

async function openArticleMenu(page: Page, item: string) {
  // ponytail: the article's "more" trigger has no label; add aria-label to target it directly
  await page
    .locator("button[aria-haspopup=menu]:not(nav *)")
    .filter({ hasNotText: /\S/ })
    .click();
  await page.getByRole("menuitem", { name: item }).click();
}

async function openCategoryMenu(page: Page, category: string, item: string) {
  await page
    .locator("div")
    .filter({ has: page.getByText(category, { exact: true }) })
    .filter({ has: page.locator("button") })
    .last()
    .getByRole("button")
    .click();
  await page.getByRole("menuitem", { name: item }).click();
}
