import { expect, test, usePersona } from "../../helpers/fixtures";
import { personas } from "../../helpers/personas";
import { createArticle, createCategory } from "../../helpers/portal";

usePersona("customer");

test("public knowledge base: browse, rate an article, then raise a ticket from it", async ({
  page,
  api,
}) => {
  const category = await createCategory(api);
  const article = await createArticle(api, category.name);

  await page.goto("/helpdesk/kb-public");
  await page.getByText(category.category_name).click();
  await page.getByText(article.title, { exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/kb-public/articles/${article.name}`));

  // ponytail: thumbs are bare clickable svgs; buttons with aria-labels would make this getByRole
  const thumbs = page
    .locator("div")
    .filter({ hasText: "Was this article Helpful?" })
    .filter({ has: page.locator("svg.cursor-pointer") })
    .last()
    .locator("svg.cursor-pointer");
  await thumbs.first().click();
  await expect(page.getByText("Feedback submitted successfully.")).toBeVisible();
  await expect
    .poll(async () => {
      const [row] = await api.list("HD Article Feedback", {
        filters: { article: article.name, user: personas.customer.email },
        fields: ["feedback"],
      });
      return row?.feedback;
    })
    .toBe("1");
  await page.getByRole("link", { name: "here" }).click();
  await expect(page).toHaveURL(/\/helpdesk\/my-tickets\/new/);
});
