import type { Page } from "@playwright/test";
import { raiseTicket } from "../../../helpers/factories";
import { expect, test, uid, usePersona } from "../../../helpers/fixtures";
import { personas } from "../../../helpers/personas";
import { createArticle, createCategory } from "../../../helpers/portal";

usePersona("customer");

function ticketRows(page: Page) {
  return page.getByRole("button", { name: /^\d{4} / });
}

test("an article without headings scrolls without errors", async ({ page, api }) => {
  const category = await createCategory(api);
  const article = await createArticle(api, category.name, {
    content: Array.from({ length: 60 }, (_, i) => `<p>Line ${i}</p>`).join(""),
  });
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(`/help/articles/${article.name}`);
  await page.getByText("Line 30", { exact: true }).hover();
  await page.mouse.wheel(0, 2000);
  await expect(page.getByText("Line 59", { exact: true })).toBeInViewport();
  expect(errors).toEqual([]);
});

test("Back after creating a ticket returns to the list", async ({ page }) => {
  await page.goto("/help/my-tickets");
  await page.getByRole("button", { name: "Raise a ticket" }).click();
  await page.getByPlaceholder("A short description").fill(`E2E back ${uid()}`);
  await page.locator(".ProseMirror").fill("Back should skip the form");
  await page.getByRole("button", { name: "Create ticket" }).click();
  await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);

  await page.goBack();
  await expect(page).toHaveURL(/\/help\/my-tickets$/);
});

test("closing a ticket confirms with a uniquely named button", async ({ page, api, apiAs }) => {
  const ticket = await raiseTicket(await apiAs("customer"));
  await page.goto(`/help/my-tickets/${ticket.name}`);
  await page.getByRole("button", { name: "Close", exact: true }).click();
  const dialog = page.getByRole("dialog");
  // the dialog's X keeps the name Close
  await expect(dialog.getByRole("button", { name: "Close", exact: true })).toHaveCount(1);
  await dialog.getByRole("button", { name: "Close ticket" }).click();
  await expect.poll(async () => (await api.get("HD Ticket", ticket.name)).status).toBe("Closed");
});

test("tables and code blocks in a description are styled as on the desk", async ({ page, apiAs }) => {
  const subject = `E2E ${uid()} styled`;
  const ticket = await (await apiAs("customer")).call("helpdesk.helpdesk.doctype.hd_ticket.api.new", {
    doc: {
      subject,
      description: "<table><tbody><tr><th>Head</th></tr><tr><td>Cell</td></tr></tbody></table><pre><code>let a = 1</code></pre>",
    },
  });
  await page.goto(`/help/my-tickets/${ticket.name}`);
  const frame = page.frameLocator("iframe").first();
  await expect(frame.getByText("let a = 1")).toBeVisible();
  // desk's .prose-f: a grey code block and a rule under the header row
  await expect(frame.locator("pre")).not.toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
  await expect(frame.locator("tr").first()).not.toHaveCSS("border-bottom-width", "0px");
});

test("Load More rows survive opening a ticket and going back", async ({ page, api }) => {
  const token = uid();
  // as admin: the portal's create endpoint is rate limited per user
  for (let i = 0; i < 22; i++)
    await api.insert("HD Ticket", { subject: `${token} more ${i}`, raised_by: personas.customer.email });
  await page.goto("/help/my-tickets");
  await expect(ticketRows(page).first()).toBeVisible();
  const reloaded = page.waitForRequest(
    (request) => /frappe.client.get_count/.test(request.url()) && (request.postData() || "").includes(token)
  );
  await page.getByRole("textbox", { name: "Subject" }).fill(token);
  await reloaded;
  // a Load More before the filtered page lands appends to the unfiltered one
  await expect(ticketRows(page).filter({ hasNotText: token })).toHaveCount(0);
  await expect(ticketRows(page)).toHaveCount(20);
  await page.getByRole("button", { name: "Load More" }).click();
  await expect(ticketRows(page)).toHaveCount(22);

  await ticketRows(page).last().click();
  await expect(page).toHaveURL(/\/help\/my-tickets\/\d+$/);
  await page.goBack();
  await expect(ticketRows(page)).toHaveCount(22);
});

test("ticket details show a tooltip only for text that is cut off", async ({ page, ticket }) => {
  const longName = `Acme ${"Holdings ".repeat(12)}Ltd`;
  await page.route("**/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one*", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.message.customer = longName;
    await route.fulfill({ response, json: body });
  });
  await page.goto(`/help/my-tickets/${ticket.name}`);

  // A tooltip repeats its text, so a second copy means it opened.
  const priority = page.getByText("Priority", { exact: true });
  await priority.hover();
  await page.waitForTimeout(800); // past the tooltip's 500ms delay
  await expect(priority).toHaveCount(1);

  await page.getByText(longName).first().hover();
  await expect.poll(() => page.getByText(longName, { exact: true }).count()).toBeGreaterThan(1);
});
