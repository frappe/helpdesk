import type { Page } from "@playwright/test";
import type { Api } from "../../helpers/api";
import { expect, test, uid, usePersona } from "../../helpers/fixtures";
import {
  chooseOption,
  createArticle,
  createCategory,
} from "../../helpers/portal";

usePersona("manager");

test("nest a new category under another from the category dialog", async ({
  page,
  api,
}) => {
  const parent = await createCategory(api);
  const name = `E2E Nested ${uid()}`;
  await page.goto("/helpdesk/kb");
  await page.getByRole("button", { name: "Create" }).click();
  await page.getByRole("menuitem", { name: "Category" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("checkbox", { name: "Add as a subcategory" }).check();
  await expect(
    dialog.getByRole("button", { name: "Create subcategory" }),
  ).toBeDisabled();
  await dialog.getByRole("combobox", { name: "Parent category" }).click();
  await page.getByRole("combobox").last().fill(parent.category_name);
  await page
    .getByRole("option", { name: parent.category_name })
    .first()
    .click();
  await dialog.getByRole("textbox", { name: "Name" }).fill(name);
  await dialog.getByRole("button", { name: "Create subcategory" }).click();

  await expect(page).toHaveURL(/\/helpdesk\/kb\/articles\/\w+\?.*isEdit=1/);
  const created = await api.exists("HD Article Category", {
    category_name: name,
  });
  expect(
    (await api.get("HD Article Category", created!)).parent_article_category,
  ).toBe(parent.name);
});

test("a searched icon can be picked and shows in the portal", async ({
  page,
  api,
  pageAs,
}) => {
  const category = await createCategory(api);
  await createArticle(api, category.name);
  await page.goto("/helpdesk/kb");
  await openCategoryMenu(page, category.category_name, "Edit");
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("button", { name: "Choose an icon" }).click();
  await page.getByRole("textbox", { name: "Search icons" }).fill("anchor");
  await page.getByRole("button", { name: "anchor", exact: true }).click();
  await dialog.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText("Category updated successfully.")).toBeVisible();

  const customer = await pageAs("customer");
  await customer.goto(`/help/category/${category.name}`);
  const icon = customer.locator(".lucide-anchor").first();
  await expect(icon).toBeVisible();
  // No CSS for the name would leave an empty box.
  await expect(icon).toHaveCSS("mask-image", /url/);
});

test("a category's description saves from the dialog and the portal shows it", async ({
  page,
  api,
  pageAs,
}) => {
  const name = `E2E Described ${uid()}`;
  await page.goto("/helpdesk/kb");
  await page.getByRole("button", { name: "Create" }).click();
  await page.getByRole("menuitem", { name: "Category" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByRole("textbox", { name: "Name" }).fill(name);
  await dialog.getByRole("textbox", { name: "Description" }).fill("First words.");
  await dialog.getByRole("button", { name: "Create category" }).click();
  await expect(page).toHaveURL(/\/helpdesk\/kb\/articles\/\w+\?.*isEdit=1/);
  const category = (await api.exists("HD Article Category", {
    category_name: name,
  }))!;
  await createArticle(api, category);

  // Edit opens on the saved text, so saving cannot wipe it.
  await page.goto("/helpdesk/kb");
  await openCategoryMenu(page, name, "Edit");
  const description = dialog.getByRole("textbox", { name: "Description" });
  await expect(description).toHaveValue("First words.");
  await description.fill("Second words.");
  await dialog.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText("Category updated successfully.")).toBeVisible();

  const customer = await pageAs("customer");
  await customer.goto(`/help/category/${category}`);
  await expect(customer.getByText("Second words.")).toBeVisible();
});

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
  await page
    .getByRole("dialog")
    .getByRole("textbox", { name: "Name" })
    .fill(categoryName);
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Create category" })
    .click();

  await expect(page).toHaveURL(/\/helpdesk\/kb\/articles\/\w+\?.*isEdit=1/);
  await page.getByPlaceholder("Title").fill(title);
  await page.locator(".ProseMirror").fill("Steps to reset a password");
  await page.getByRole("button", { name: "Save" }).click();
  await expect(page.getByText("Article updated successfully.")).toBeVisible();

  await page.getByRole("button", { name: "Publish" }).click();
  // Publishing asks for the access first.
  await page
    .getByRole("dialog", { name: "Publish article as" })
    .getByRole("button", { name: "Publish" })
    .click();
  await expect(page.getByRole("button", { name: "Unpublish" })).toBeVisible();
  const [article] = await api.list("HD Article", {
    filters: { title },
    fields: ["name", "status", "category"],
  });
  expect(article.status).toBe("Published");

  const customer = await pageAs("customer");
  await customer.goto(`/help/category/${article.category}`);
  // The sidebar lists it too; the category list comes last.
  await customer.getByText(title).last().click();
  await expect(customer).toHaveURL(
    new RegExp(`/help/articles/${article.name}`),
  );
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
  await expect
    .poll(async () => (await api.get("HD Article", article.name)).title)
    .toBe(renamed);

  await page.getByRole("button", { name: "Unpublish" }).click();
  await expect
    .poll(async () => (await api.get("HD Article", article.name)).status)
    .toBe("Draft");

  await openArticleMenu(page, "Move To");
  await chooseOption(page, to.category_name);
  await page.getByRole("dialog").getByRole("button", { name: "Move" }).click();
  await expect
    .poll(async () => (await api.get("HD Article", article.name)).category)
    .toBe(to.name);

  // a category must keep one article, so give the target another before deleting
  await createArticle(api, to.name);
  await openArticleMenu(page, "Delete");
  await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
  await expect(page).toHaveURL(/\/helpdesk\/kb$/);
  expect(
    await api.exists("HD Article", { name: article.name }),
  ).toBeUndefined();
});

test("merge a category into another, then delete one", async ({
  page,
  api,
}) => {
  const source = await createCategory(api);
  const target = await createCategory(api);
  const doomed = await createCategory(api);
  const moved = await createArticle(api, source.name);
  const orphan = await createArticle(api, doomed.name);

  await page.goto("/helpdesk/kb");
  await openCategoryMenu(page, source.category_name, "Merge");
  await chooseOption(page, target.category_name);
  await page.getByRole("dialog").getByRole("button", { name: "Merge" }).click();
  await expect
    .poll(async () => (await api.get("HD Article", moved.name)).category)
    .toBe(target.name);
  expect(
    await api.exists("HD Article Category", { name: source.name }),
  ).toBeUndefined();

  await openCategoryMenu(page, doomed.category_name, "Delete");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Move articles to General" })
    .click();
  await expect
    .poll(() => api.exists("HD Article Category", { name: doomed.name }))
    .toBeUndefined();
  const general = await api.call(
    "helpdesk.api.knowledge_base.get_general_category",
  );
  expect((await api.get("HD Article", orphan.name)).category).toBe(general);
});

test("delete a category with its subcategory and articles; a cited one is archived", async ({
  page,
  api,
  apiAs,
}) => {
  const parent = await createCategory(api);
  const sub = await createCategory(api, undefined, {
    parent_article_category: parent.name,
  });
  const deleted = await createArticle(api, parent.name);
  const cited = await createArticle(api, sub.name);
  await (
    await apiAs("customer")
  ).call("helpdesk.helpdesk.doctype.hd_ticket.api.new", {
    doc: {
      subject: `E2E cites ${uid()}`,
      description: "<p>Cites an article</p>",
    },
    origin: { from: "article", article: cited.name },
  });

  await page.goto("/helpdesk/kb");
  await openCategoryMenu(page, parent.category_name, "Delete");
  const dialog = page.getByRole("dialog");
  await expect(
    dialog.getByText("1 article is linked to a ticket"),
  ).toBeVisible();
  await dialog
    .getByRole("button", { name: "Delete articles, archive linked" })
    .click();

  await expect(page.getByText("1 article was archived")).toBeVisible();
  expect(
    await api.exists("HD Article Category", { name: parent.name }),
  ).toBeUndefined();
  expect(
    await api.exists("HD Article Category", { name: sub.name }),
  ).toBeUndefined();
  expect(
    await api.exists("HD Article", { name: deleted.name }),
  ).toBeUndefined();
  expect((await api.get("HD Article", cited.name)).status).toBe("Archived");
});

test("convert a subcategory to a category from its menu", async ({
  page,
  api,
}) => {
  const parent = await createCategory(api);
  const sub = await createCategory(api, undefined, {
    parent_article_category: parent.name,
  });
  await createArticle(api, sub.name);
  // a parent can't be left empty
  await createArticle(api, parent.name);

  await page.goto("/helpdesk/kb");
  await openCategoryMenu(page, sub.category_name, "Convert to category");
  await expect(
    page.getByText(`${sub.category_name} is now a category`),
  ).toBeVisible();
  expect(
    (await api.get("HD Article Category", sub.name)).parent_article_category,
  ).toBeFalsy();
});

test("archive an article, then restore it as a draft", async ({
  page,
  api,
}) => {
  const category = await createCategory(api);
  await createArticle(api, category.name);
  const article = await createArticle(api, category.name);

  await page.goto(`/helpdesk/kb/articles/${article.name}`);
  await openArticleMenu(page, "Archive");
  await page
    .getByRole("dialog", { name: "Archive article" })
    .getByRole("button", { name: "Archive" })
    .click();
  await expect(page.getByText("Article archived.")).toBeVisible();
  expect((await api.get("HD Article", article.name)).status).toBe("Archived");

  await page.goto(`/helpdesk/kb/articles/${article.name}`);
  await page.getByRole("button", { name: "Restore" }).click();
  const dialog = page.getByRole("dialog", { name: "Restore article" });
  await dialog.getByRole("button", { name: "Restore" }).click();
  await expect(page.getByText("Article restored as a draft.")).toBeVisible();
  const general = await api.call(
    "helpdesk.api.knowledge_base.get_general_category",
  );
  const restored = await api.get("HD Article", article.name);
  expect([restored.status, restored.category]).toEqual(["Draft", general]);
});

test("deleting an archived article a ticket links offers only delete", async ({
  page,
  api,
  apiAs,
}) => {
  const category = await createCategory(api);
  await createArticle(api, category.name);
  const article = await createArticle(api, category.name);
  await (
    await apiAs("customer")
  ).call("helpdesk.helpdesk.doctype.hd_ticket.api.new", {
    doc: {
      subject: `E2E cites ${uid()}`,
      description: "<p>Cites an article</p>",
    },
    origin: { from: "article", article: article.name },
  });
  await api.call("helpdesk.api.knowledge_base.archive_articles", {
    articles: [article.name],
  });

  await page.goto(`/helpdesk/kb/articles/${article.name}`);
  await openArticleMenu(page, "Delete");
  await page.getByRole("menuitem", { name: "Confirm Delete" }).click();
  const dialog = page.getByRole("dialog", { name: "Delete archived article" });
  await expect(dialog.getByRole("button", { name: "Archive" })).toHaveCount(0);
  await dialog.getByRole("button", { name: "Delete" }).click();
  await expect
    .poll(() => api.exists("HD Article", { name: article.name }))
    .toBeUndefined();
});

test("delete a category: move to parent, delete articles, delete everything", async ({
  page,
  api,
}) => {
  const parent = await createCategory(api);
  const sub = await createCategory(api, undefined, {
    parent_article_category: parent.name,
  });
  await createArticle(api, parent.name);
  const moved = await createArticle(api, sub.name);
  const plain = await createCategory(api);
  const deleted = await createArticle(api, plain.name);
  const branch = await createCategory(api);
  await createCategory(api, undefined, {
    parent_article_category: branch.name,
  }).then((child) => createArticle(api, child.name));
  await createArticle(api, branch.name);

  await page.goto("/helpdesk/kb");
  await openCategoryMenu(page, sub.category_name, "Delete");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Move articles to parent category" })
    .click();
  await expect
    .poll(async () => (await api.get("HD Article", moved.name)).category)
    .toBe(parent.name);

  await openCategoryMenu(page, plain.category_name, "Delete");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete articles" })
    .click();
  await expect
    .poll(() => api.exists("HD Article", { name: deleted.name }))
    .toBeUndefined();

  await openCategoryMenu(page, branch.category_name, "Delete");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Delete everything" })
    .click();
  await expect
    .poll(() => api.exists("HD Article Category", { name: branch.name }))
    .toBeUndefined();
});

test("the category filter also lists its subcategories' articles", async ({
  page,
  api,
}) => {
  const parent = await createCategory(api);
  const sub = await createCategory(api, undefined, {
    parent_article_category: parent.name,
  });
  const own = await createArticle(api, parent.name);
  const nested = await createArticle(api, sub.name);
  const other = await createArticle(api, (await createCategory(api)).name);

  await page.goto("/helpdesk/kb");
  try {
    await page.getByPlaceholder("Category").fill(parent.category_name);
    await page
      .getByRole("option", { name: parent.category_name, exact: true })
      .click();

    await expect(page.getByText(own.title)).toBeVisible();
    await page
      .getByRole("button", { name: `Expand ${sub.category_name}` })
      .click();
    await expect(page.getByText(nested.title)).toBeVisible();
    await expect(page.getByText(other.title)).toHaveCount(0);
  } finally {
    await clearQuickFilters(api);
  }
});

test("select all, then Delete, deletes the categories, not just their articles", async ({
  page,
  api,
}) => {
  const parent = await createCategory(api);
  const sub = await createCategory(api, undefined, {
    parent_article_category: parent.name,
  });
  await createArticle(api, parent.name);
  await createArticle(api, sub.name);

  await page.goto("/helpdesk/kb");
  try {
    const filter = page.getByPlaceholder("Category");
    await filter.fill(sub.category_name);
    await page
      .getByRole("option", { name: new RegExp(sub.category_name) })
      .click();
    // after a reload the KB page names it "Parent › Sub", not its ID
    await expect
      .poll(async () =>
        JSON.stringify(
          await api.list("HD View", {
            filters: { dt: "HD Article", user: "e2e-manager@example.com" },
            fields: ["filters"],
          }),
        ),
      )
      .toContain(sub.name);
    await page.reload();
    await expect(filter).toHaveValue(
      `${parent.category_name} › ${sub.category_name}`,
    );

    await filter.fill(parent.category_name);
    await page
      .getByRole("option", { name: parent.category_name, exact: true })
      .click();
    await page
      .getByRole("button", { name: `Expand ${sub.category_name}` })
      .click();
    // the list header's checkbox
    await page.getByRole("checkbox").first().check();
    await expect(
      page.getByRole("checkbox", { name: `Select ${parent.category_name}` }),
    ).toBeChecked();
    await page
      .getByText(/\d+ rows? selected/)
      .locator("xpath=ancestor::div[contains(@class, 'shadow-2xl')]")
      .locator("[aria-haspopup=menu]")
      .click();
    await page.getByRole("menuitem", { name: "Delete" }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Delete everything" })
      .click();

    await expect
      .poll(() => api.exists("HD Article Category", { name: parent.name }))
      .toBeUndefined();
    expect(
      await api.exists("HD Article Category", { name: sub.name }),
    ).toBeUndefined();
  } finally {
    await clearQuickFilters(api);
  }
});

// quick filters save to the persona's default view
async function clearQuickFilters(api: Api) {
  const [view] = await api.list("HD View", {
    filters: { dt: "HD Article", user: "e2e-manager@example.com" },
    fields: ["name"],
  });
  if (view) await api.update("HD View", view.name, { filters: "[]" });
}

async function openArticleMenu(page: Page, item: string) {
  await page
    .locator("button[aria-haspopup=menu]:not(nav *)")
    .filter({ hasNotText: /\S/ })
    .click();
  await page.getByRole("menuitem", { name: item }).click();
}

async function openCategoryMenu(page: Page, category: string, item: string) {
  await page
    .getByRole("button", { name: `Options for ${category}`, exact: true })
    .click();
  await page.getByRole("menuitem", { name: item }).click();
}
