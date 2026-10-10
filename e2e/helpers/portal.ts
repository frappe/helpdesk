import { expect, request, type Page } from "@playwright/test";
import { runScheduledJob, type Api } from "./api";
import { uid } from "./factories";
import { siteHeader } from "./site";

export async function createCategory(api: Api, name = `E2E Category ${uid()}`) {
  return api.insert("HD Article Category", { category_name: name });
}

export async function createArticle(
  api: Api,
  category: string,
  fields: Record<string, any> = {}
) {
  const title = fields.title || `E2E Article ${uid()}`;
  return api.insert("HD Article", {
    title,
    category,
    content: `<p>${title} body</p>`,
    status: "Published",
    ...fields,
  });
}

/** Pick an option in a frappe-ui Combobox-backed Link field. */
/** New articles reach the search index only through a scheduled job; run it until `query` finds one. */
export async function indexArticles(api: Api, query: string) {
  await expect
    .poll(
      async () => {
        await runScheduledJob(api, "frappe.search.sqlite_search.index_docs_in_queue");
        const hits = await api.callGet("helpdesk.api.knowledge_base.search_articles", { query });
        return hits.length;
      },
      { timeout: 30_000, intervals: [1_000] }
    )
    .toBeGreaterThan(0);
}

export async function pickOption(
  page: Page,
  trigger: string,
  option: string,
  { opensItself = false } = {}
) {
  if (!opensItself) await page.getByRole("button", { name: trigger }).click();
  await page.getByRole("combobox").last().fill(option);
  await page.getByRole("option", { name: option }).first().click();
}

/** Raw request context for calls the Api client does not cover (uploads, file GETs). */
export async function loginContext(baseURL: string, user: string, password: string) {
  const context = await request.newContext({ baseURL, extraHTTPHeaders: siteHeader() });
  await context.post("/api/method/login", { form: { usr: user, pwd: password } });
  return context;
}

/**
 * Open the ticket list scoped to one ticket through a private throwaway view.
 * Typing into the list filters would auto-save them into the persona's shared default view.
 */
export async function openTicketInList(page: Page, api: Api, user: string, ticket: string) {
  const view = await api.insert("HD View", {
    label: `E2E ${uid()}`,
    user,
    dt: "HD Ticket",
    type: "list",
    route_name: "TicketsAgent",
    filters: JSON.stringify({ name: ticket }),
    order_by: "modified desc",
  });
  await page.goto(`/helpdesk/tickets?view=${view.name}`);
  return view.name;
}
