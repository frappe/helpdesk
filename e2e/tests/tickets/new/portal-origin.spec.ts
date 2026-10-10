import type { Page } from "@playwright/test";
import type { Api } from "../../../helpers/api";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { createArticle, createCategory } from "../../../helpers/portal";

usePersona("customer");

// Each "raise a ticket" link carries its origin; the server stores it on the ticket.
test.describe("ticket origin", () => {
  test("a ticket raised from an article records that article", async ({ page, api }) => {
    const category = await createCategory(api);
    const article = await createArticle(api, category.name);

    await page.goto(`/help/articles/${article.name}`);
    await page.getByRole("link", { name: "here", exact: true }).click();
    const origin = await submitTicket(page, api);

    expect(origin.entry_point).toBe("Article");
    expect(origin.source_article).toBe(article.name);
  });

  test("a ticket raised from my tickets records the ticket list", async ({ page, api }) => {
    await page.goto("/help/customer-tickets");
    await page.getByRole("button", { name: "Raise a ticket" }).click();

    expect((await submitTicket(page, api)).entry_point).toBe("Ticket List");
  });

  test("a ticket raised from a closed ticket records the closed ticket", async ({
    page,
    api,
    apiAs,
  }) => {
    const closed = await raiseTicket(await apiAs("customer"));
    await api.update("HD Ticket", closed.name, { status: "Closed" });

    await page.goto(`/help/tickets/${closed.name}`);
    await page.getByRole("button", { name: "Raise a ticket" }).click();

    expect((await submitTicket(page, api)).entry_point).toBe("Closed Ticket");
  });

  test("a ticket raised from search records the search text", async ({ page, api }) => {
    const query = `nothing matches ${uid()}`;

    await page.goto(`/help/tickets/new?from=search&q=${encodeURIComponent(query)}`);
    // the search text also starts the subject
    await expect(page.getByPlaceholder("A short description")).toHaveValue(query);
    const origin = await submitTicket(page, api, { keepSubject: true });

    expect(origin.entry_point).toBe("Search");
    expect(origin.source_search).toBe(query);
  });

  test("a ticket raised without a known link is direct", async ({ page, api }) => {
    await page.goto("/help/tickets/new");

    expect((await submitTicket(page, api)).entry_point).toBe("Direct");
  });
});

async function submitTicket(page: Page, api: Api, { keepSubject = false } = {}) {
  await expect(page).toHaveURL(/\/help\/tickets\/new/);
  const subjectField = page.getByPlaceholder("A short description");
  if (!keepSubject) await subjectField.fill(`E2E origin ${uid()}`);
  const subject = await subjectField.inputValue();
  await page.locator(".ProseMirror").fill("Where did this start?");
  await page.getByRole("button", { name: "Create ticket" }).click();
  await expect(page).toHaveURL(/\/help\/tickets\/\d+$/);

  const [ticket] = await api.list("HD Ticket", {
    filters: { subject },
    fields: ["entry_point", "source_article", "source_search"],
  });
  return ticket;
}
