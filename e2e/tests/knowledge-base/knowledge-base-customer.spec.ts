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

  await page.goto("/kb");
  await page.getByText(category.category_name).first().click();
  await page.getByText(article.title, { exact: true }).first().click();
  await expect(page).toHaveURL(new RegExp(`/kb/articles/${article.name}`));

  await page.getByRole("button", { name: "Yes, it was helpful" }).click();
  await expect(page.getByText("Thanks for your feedback!")).toBeVisible();
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
  await expect(page).toHaveURL(/\/kb\/tickets\/new/);
});
