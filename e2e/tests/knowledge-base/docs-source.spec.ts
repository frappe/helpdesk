import type { Page } from "@playwright/test";
import { expect, test, usePersona } from "../../helpers/fixtures";
import { createArticle, createCategory } from "../../helpers/portal";
import { snapshotSettings } from "../../helpers/settings";

usePersona("manager");

const GET = "**/api/method/helpdesk.api.docs_source.get_docs_source*";
const CONNECT = "**/api/method/helpdesk.api.docs_source.connect_docs_source*";
const HIDE = "**/api/method/helpdesk.api.docs_source.set_hidden_sections*";
const DOC_PAGE = "**/api/method/helpdesk.api.docs_source.get_doc_page*";
const SOURCE = "https://docs.example.com";
const PHONE = { width: 390, height: 844 };

const BASE = {
  url: "https://docs.example.com",
  sections: [],
  sections_error: false,
  page_count: 0,
  synced_on: null,
  truncated: false,
  error: "",
  syncing: false,
};
const WIKI = {
  ...BASE,
  type: "Frappe Wiki",
  label: "Frappe Wiki",
  sections: [
    { key: "guides", title: "Guides", hidden: false },
    { key: "legal", title: "Legal", hidden: false },
  ],
};
const INDEXED = {
  ...BASE,
  type: "llms.txt",
  label: "docs.example.com",
  page_count: 142,
  synced_on: new Date(Date.now() - 3 * 86400_000).toISOString().replace("T", " ").slice(0, 19),
};

const json = (message: unknown) => ({ json: { message } });

async function open(page: Page, source: unknown) {
  await page.route(GET, (route) => route.fulfill(json(source)));
  await page.goto("/help/settings/knowledge-base");
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await expect(dialog.getByRole("heading", { name: "Docs source" })).toBeVisible();
  return dialog;
}

test("wiki shows section checkboxes and unticking saves at once", async ({ page }) => {
  const dialog = await open(page, WIKI);
  let sent: any;
  await page.route(HIDE, (route) => {
    sent = route.request().postDataJSON();
    return route.fulfill(json(null));
  });
  await expect(dialog.getByRole("checkbox", { name: "Guides" })).toBeChecked();
  await dialog.getByRole("checkbox", { name: "Legal" }).uncheck();
  await expect.poll(() => sent?.sections).toEqual(["legal"]);
  await expect(dialog.getByRole("checkbox", { name: "Legal" })).not.toBeChecked();
});

test("a failed save restores the box and shows the error", async ({ page }) => {
  const dialog = await open(page, WIKI);
  await page.route(HIDE, (route) =>
    route.fulfill({
      status: 417,
      json: { exc_type: "ValidationError", _server_messages: JSON.stringify([JSON.stringify({ message: "Nope, not now" })]) },
    })
  );
  await dialog.getByRole("checkbox", { name: "Legal" }).uncheck();
  await expect(dialog.getByText("Nope, not now")).toBeVisible();
  await expect(dialog.getByRole("checkbox", { name: "Legal" })).toBeChecked();
});

test("unreadable wiki sections show a message, not an empty list", async ({ page }) => {
  const dialog = await open(page, { ...WIKI, sections: [], sections_error: true });
  await expect(dialog.getByText("The sections could not be read right now.")).toBeVisible();
  await expect(dialog.getByRole("checkbox")).toHaveCount(0);
});

test("indexed source shows Resync and the page line", async ({ page }) => {
  const dialog = await open(page, { ...INDEXED, truncated: true });
  await expect(dialog.getByRole("button", { name: "Resync" })).toBeVisible();
  await expect(dialog.getByText(/142 pages · synced 3 days ago/)).toBeVisible();
  await expect(dialog.getByText(/not all pages/i)).toBeVisible();
  await expect(dialog.getByRole("checkbox")).toHaveCount(0);
});

test("a sync error shows the server text", async ({ page }) => {
  const dialog = await open(page, { ...INDEXED, error: "The site refused the read." });
  await expect(dialog.getByText("The site refused the read.")).toBeVisible();
});

test("connect on an indexed site polls until the sync ends", async ({ page }) => {
  let connected = false;
  let release = false;
  await page.route(GET, (route) => {
    if (!connected) return route.fulfill(json(null));
    const syncing = { ...INDEXED, synced_on: null, page_count: 0, syncing: true };
    return route.fulfill(json(release ? INDEXED : syncing));
  });
  await page.route(CONNECT, (route) => {
    connected = true;
    return route.fulfill(json({ ...INDEXED, synced_on: null, page_count: 0, syncing: false }));
  });
  await page.goto("/help/settings/knowledge-base");
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await dialog.getByPlaceholder("https://docs.example.com").fill("https://docs.example.com");
  await dialog.getByRole("button", { name: "Connect" }).click();
  await expect(dialog.getByRole("button", { name: /Syncing/ })).toBeVisible({ timeout: 15_000 });
  release = true;
  await expect(dialog.getByText(/142 pages/)).toBeVisible({ timeout: 15_000 });
  await expect(dialog.getByRole("button", { name: "Resync" })).toBeVisible();
});

test("a failed load shows the error and offers no Connect", async ({ page }) => {
  await page.route(GET, (route) =>
    route.fulfill({
      status: 417,
      json: { exc_type: "ValidationError", _server_messages: JSON.stringify([JSON.stringify({ message: "Settings are down" })]) },
    })
  );
  await page.goto("/help/settings/knowledge-base");
  const dialog = page.getByRole("dialog", { name: "Settings" });
  await expect(dialog.getByText("Settings are down")).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Connect" })).toHaveCount(0);
});

test.describe("plain agent", () => {
  test.use({ storageState: "e2e/.auth/agent.json" });

  test("does not see the Docs source section", async ({ page }) => {
    await page.goto("/help/settings/knowledge-base");
    await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Docs source" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Connect" })).toHaveCount(0);
  });
});

const docsTest = test.extend<{ connected: void }>({
  connected: async ({ api }, use) => {
    const restore = await snapshotSettings(api, ["docs_source_url"]);
    await api.update("HD Settings", "HD Settings", { docs_source_url: SOURCE });
    await use();
    await restore();
  },
});

function docPage(route: string, fields: Record<string, unknown> = {}) {
  return {
    route,
    title: `Doc ${route}`,
    content: "<h2>First part</h2><p>Body of the page</p><h2>Second part</h2><p>More of it</p>",
    label: "Helpdesk docs",
    last_updated: "5 months ago",
    source_url: `${SOURCE}/${route}`,
    site_url: `${SOURCE}/helpdesk`,
    related: { docs: [], articles: [] },
    ...fields,
  };
}

// Answers known routes, 404s the rest; returns the routes the portal asked for.
async function stubDocs(page: Page, pages: Record<string, unknown>) {
  const asked: string[] = [];
  await page.route(DOC_PAGE, (route) => {
    const path = new URL(route.request().url()).searchParams.get("route")!;
    asked.push(path);
    if (path in pages) return route.fulfill(json(pages[path]));
    return route.fulfill({ status: 404, json: { exc_type: "DoesNotExistError" } });
  });
  return asked;
}

const heading = (page: Page, name: string) => page.getByRole("heading", { name, level: 1 });
const robots = (page: Page) => page.locator('head meta[name="robots"]');
const canonical = (page: Page) => page.locator('head link[rel="canonical"]');

async function seedArticle(api) {
  const category = await createCategory(api);
  return createArticle(api, category.name);
}

test.describe("docs pages", () => {
  docsTest("multi-segment path shows the Docs page", async ({ page, connected }) => {
    await stubDocs(page, { "helpdesk/setup": docPage("helpdesk/setup") });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(heading(page, "Doc helpdesk/setup")).toBeVisible();
    await expect(page.getByText("Helpdesk docs")).toBeVisible();
    await expect(page.getByText("Updated 5 months ago")).toBeVisible();
    await expect(page.getByRole("link", { name: "View on docs.example.com" })).toHaveAttribute(
      "href",
      `${SOURCE}/helpdesk/setup`
    );
    await expect(page.getByText("Body of the page")).toBeVisible();
    await expect(page.getByRole("button", { name: "Second part" })).toBeVisible();
    await expect(page).toHaveTitle(/^Doc helpdesk\/setup \| .+/);
  });

  docsTest("single-segment path falls back to the Docs page", async ({ page, connected }) => {
    await stubDocs(page, { introduction: docPage("introduction") });
    await page.goto("/help/articles/introduction");
    await expect(heading(page, "Doc introduction")).toBeVisible();
    await expect(page.getByText("Article not found")).toHaveCount(0);
  });

  docsTest("a missing Article never flashes the empty state", async ({ page, connected }) => {
    await stubDocs(page, { introduction: docPage("introduction") });
    let release = () => {};
    const held = new Promise<void>((resolve) => (release = resolve));
    await page.route("**/api/method/helpdesk.api.config.get_config*", async (route) => {
      await held;
      await route.continue();
    });
    const missing = page.waitForResponse(/knowledge_base\.get_article/);
    await page.goto("/help/articles/introduction");
    await missing;
    await page.waitForTimeout(300);
    await expect(page.getByText("Article not found")).toHaveCount(0);
    release();
    await expect(heading(page, "Doc introduction")).toBeVisible();
  });

  docsTest("an Article wins over a Docs page", async ({ page, api, connected }) => {
    const article = await seedArticle(api);
    const asked = await stubDocs(page, { [article.name]: docPage(article.name) });
    for (const path of [article.name, `${article.name}/`]) {
      await page.goto(`/help/articles/${path}`);
      await expect(heading(page, article.title)).toBeVisible();
    }
    expect(asked).toEqual([]);
  });

  docsTest("settings path stays a Docs page", async ({ page, connected }) => {
    const routes = ["helpdesk/settings", "crm/settings/sales-hierarchy"];
    await stubDocs(page, Object.fromEntries(routes.map((route) => [route, docPage(route)])));
    for (const route of routes) {
      await page.goto(`/help/articles/${route}`);
      await expect(heading(page, `Doc ${route}`)).toBeVisible();
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page).toHaveURL(new RegExp(`/help/articles/${route}$`));
    }
  });

  docsTest("Article settings dialog still opens", async ({ page, api, connected }) => {
    const article = await seedArticle(api);
    const asked = await stubDocs(page, {});
    await page.goto(`/help/articles/${article.name}/settings/profile`);
    await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page).toHaveURL(new RegExp(`/help/articles/${article.name}-[^/]+$`));
    await expect(heading(page, article.title)).toBeVisible();
    expect(asked).toEqual([]);
  });

  test("Article settings dialog opens with no source", async ({ page, api }) => {
    const article = await seedArticle(api);
    await page.goto(`/help/articles/${article.name}/settings/profile`);
    await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page).toHaveURL(new RegExp(`/help/articles/${article.name}-[^/]+$`));
  });

  docsTest("the account menu opens settings over the same Docs page", async ({ page, connected }) => {
    const asked = await stubDocs(page, { "helpdesk/setup": docPage("helpdesk/setup") });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(heading(page, "Doc helpdesk/setup")).toBeVisible();
    await page.getByRole("button", { name: "Helpdesk", exact: true }).click();
    await page.getByRole("menuitem", { name: "Settings" }).click();
    await expect(page).toHaveURL(/\/helpdesk\/setup\/settings\/profile$/);
    await page.keyboard.press("Escape");
    await expect(page).toHaveURL(/\/articles\/helpdesk\/setup$/);
    await expect(heading(page, "Doc helpdesk/setup")).toBeVisible();
    expect(asked.every((route) => route === "helpdesk/setup")).toBe(true);
  });

  test("no source shows the Article empty state", async ({ page }) => {
    const asked = await stubDocs(page, {});
    await page.goto("/help/articles/helpdesk/setup");
    await expect(page.getByText("Article not found")).toBeVisible();
    await page.goto("/help/articles/");
    await expect(page.getByText("The page you are looking for does not exist.")).toBeVisible();
    expect(asked).toEqual([]);
  });

  docsTest("a failed read shows Page not found and a source link", async ({ page, connected }) => {
    await stubDocs(page, {});
    await page.goto("/help/articles/helpdesk/gone");
    await expect(page.getByText("Page not found")).toBeVisible();
    await expect(page.getByText("Article not found")).toHaveCount(0);
    await expect(page.getByRole("link", { name: "View on docs.example.com" })).toHaveAttribute(
      "href",
      `${SOURCE}/helpdesk/gone`
    );
  });

  docsTest("sidebar shows Help center, Related, All docs", async ({ page, connected }) => {
    const related = {
      docs: [{ route: "helpdesk/sla", title: "<b>SLA</b> rules" }],
      articles: [{ name: "abc", title: "<i>Reset</i> a password", title_slug: "reset" }],
    };
    await stubDocs(page, {
      "helpdesk/setup": docPage("helpdesk/setup", { related }),
      "helpdesk/sla": docPage("helpdesk/sla", { title: "<b>Plain</b> title" }),
    });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(page.getByRole("link", { name: "Help center" })).toHaveAttribute("href", "/help/");
    const links = page.getByRole("navigation", { name: "Related" }).getByRole("link");
    await expect(links).toHaveText(["<b>SLA</b> rules", "<i>Reset</i> a password"]);
    await expect(links.nth(0)).toHaveAttribute("href", "/help/articles/helpdesk/sla");
    await expect(links.nth(1)).toHaveAttribute("href", "/help/articles/abc-reset");
    await expect(page.getByRole("link", { name: "All docs" })).toHaveAttribute("href", `${SOURCE}/helpdesk`);
    await links.nth(0).click();
    await expect(heading(page, "<b>Plain</b> title")).toBeVisible();
  });

  docsTest("page has noindex and canonical, removed on leaving", async ({ page, connected }) => {
    const related = { docs: [{ route: "helpdesk/sla", title: "SLA" }], articles: [] };
    await stubDocs(page, {
      "helpdesk/setup": docPage("helpdesk/setup", { related }),
      "helpdesk/sla": docPage("helpdesk/sla"),
    });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(canonical(page)).toHaveAttribute("href", `${SOURCE}/helpdesk/setup`);
    await expect(robots(page)).toHaveAttribute("content", "noindex");
    await page.getByRole("link", { name: "SLA" }).click();
    await expect(canonical(page)).toHaveAttribute("href", `${SOURCE}/helpdesk/sla`);
    await expect(robots(page)).toHaveCount(1);
    await page.getByRole("link", { name: "Help center" }).click();
    await expect(page).toHaveURL(/\/help\/?$/);
    await expect(canonical(page)).toHaveCount(0);
    await expect(robots(page)).toHaveCount(0);
  });

  docsTest.describe("phone", () => {
    docsTest.use({ viewport: PHONE });

    docsTest("phone shows a back link", async ({ page, connected }) => {
      await stubDocs(page, { "helpdesk/setup": docPage("helpdesk/setup") });
      await page.goto("/help/articles/helpdesk/setup");
      await expect(heading(page, "Doc helpdesk/setup")).toBeVisible();
      await expect(page.getByRole("button", { name: /^Articles/ })).toHaveCount(0);
      await page.getByRole("link", { name: "Help center" }).click();
      await expect(page).toHaveURL(/\/help\/?$/);
    });
  });

  docsTest("moving from a Docs page to an Article shows the Article", async ({ page, api, connected }) => {
    const article = await seedArticle(api);
    const related = { docs: [], articles: [{ name: article.name, title: article.title, title_slug: "" }] };
    await stubDocs(page, { introduction: docPage("introduction", { related }) });
    await page.goto("/help/articles/introduction");
    await page.getByRole("link", { name: article.title }).click();
    await expect(heading(page, article.title)).toBeVisible();
    await expect(page).toHaveTitle(new RegExp(`^${article.title} \\| `));
    await expect(robots(page)).toHaveCount(0);
    await page.goBack();
    await expect(heading(page, "Doc introduction")).toBeVisible();
    await expect(page).toHaveTitle(/^Doc introduction \| /);
  });

  docsTest("a get_doc_page answer with article redirects to that Article", async ({ page, api, connected }) => {
    const article = await seedArticle(api);
    await stubDocs(page, { "helpdesk/setup": { article: { name: article.name, title_slug: "moved" } } });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(heading(page, article.title)).toBeVisible();
    await expect(page).toHaveURL(new RegExp(`/help/articles/${article.name}-`));
  });

  docsTest("leaving during a read skips its redirect", async ({ page, connected }) => {
    let release = () => {};
    const held = new Promise<void>((resolve) => (release = resolve));
    await page.route(DOC_PAGE, async (route) => {
      await held;
      await route.fulfill(json({ article: { name: "abc", title_slug: "moved" } }));
    });
    await page.goto("/help/articles/helpdesk/setup");
    await page.getByRole("link", { name: "Help center" }).click();
    await expect(page).toHaveURL(/\/help\/?$/);
    const answered = page.waitForResponse(DOC_PAGE);
    release();
    await answered;
    await page.waitForTimeout(300);
    await expect(page).toHaveURL(/\/help\/?$/);
  });

  docsTest("fetched fixed styles stay inside the Docs page", async ({ page, connected }) => {
    await stubDocs(page, { "helpdesk/setup": docPage("helpdesk/setup") });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(heading(page, "Doc helpdesk/setup")).toBeVisible();
    const top = await page.evaluate(() => {
      const fixed = Object.assign(document.createElement("div"), { style: "position:fixed;inset:0" });
      document.querySelector(".ProseMirror")!.append(fixed);
      return fixed.getBoundingClientRect().top;
    });
    expect(top).toBeGreaterThan(0);
  });

  docsTest("a hash scrolls to its heading and a new page starts at the top", async ({ page, connected }) => {
    const long = `<h2>First part</h2>${"<p>Filler</p>".repeat(120)}<h2>Second part</h2><p>More of it</p>`;
    const related = { docs: [{ route: "helpdesk/sla", title: "SLA" }], articles: [] };
    await stubDocs(page, {
      "helpdesk/setup": docPage("helpdesk/setup", { content: long, related }),
      "helpdesk/sla": docPage("helpdesk/sla", { content: long }),
    });
    await page.goto("/help/articles/helpdesk/setup#second-part");
    const target = page.locator(".ProseMirror #second-part");
    await expect(target).toBeInViewport();
    await page.getByRole("link", { name: "SLA" }).click();
    await expect(heading(page, "Doc helpdesk/sla")).toBeInViewport();
  });
});

const ARTICLE_SEARCH = "**/api/method/helpdesk.api.knowledge_base.search_articles*";
const DOCS_SEARCH = "**/api/method/helpdesk.api.docs_source.search_docs*";

const articleHit = (title: string, fields: Record<string, unknown> = {}) => ({
  name: `art-${title.replace(/\W+/g, "-")}`,
  title,
  title_slug: "slug",
  excerpt: "Article excerpt",
  category_label: "Guides",
  is_converted: false,
  ...fields,
});
const docHit = (route: string, title: string) => ({
  route,
  title,
  excerpt: "Docs excerpt",
  category_label: "Helpdesk docs",
});

type Answer = unknown[] | ((query: string) => Promise<unknown[] | number>);

// An answer is a list, or a function that may wait and may return a status.
async function stubSearch(page: Page, articles: Answer, docs: Answer) {
  const docsCalls: string[] = [];
  const answer = async (route, what: Answer) => {
    const query = new URL(route.request().url()).searchParams.get("query")!;
    const out = typeof what === "function" ? await what(query) : what;
    if (typeof out === "number") return route.fulfill({ status: out, json: { exc_type: "ValidationError" } });
    return route.fulfill(json(out));
  };
  await page.route(ARTICLE_SEARCH, (route) => answer(route, articles));
  await page.route(DOCS_SEARCH, (route) => {
    docsCalls.push(route.request().url());
    return answer(route, docs);
  });
  return docsCalls;
}

function gate() {
  let open = () => {};
  const held = new Promise<void>((resolve) => (open = resolve));
  return { held, open };
}

async function searchFor(page: Page, text: string) {
  await page.goto("/help/");
  const box = page.getByPlaceholder("Search articles").first();
  await box.fill(text);
  return box;
}

const rowsOf = (page: Page) => page.getByRole("option");

test.describe("search list", () => {
  docsTest("Docs pages sit under Articles in one list with no tag", async ({ page, connected }) => {
    await stubSearch(page, [articleHit("Alpha guide")], [docHit("helpdesk/beta", "Beta guide")]);
    await searchFor(page, "guide");
    await expect(rowsOf(page)).toHaveCount(2);
    await expect(rowsOf(page).nth(0)).toContainText("Alpha guide");
    await expect(rowsOf(page).nth(1)).toContainText("Beta guide");
    await expect(page.getByText("1 result").or(page.getByText("2 results"))).toHaveCount(1);
    await expect(page.getByText(/^Docs$/)).toHaveCount(0);
  });

  docsTest("Matching Article drops its Docs page", async ({ page, connected }) => {
    await stubSearch(
      page,
      [articleHit("Reports & dashboards")],
      [docHit("helpdesk/reports", "Reports &amp; dashboards"), docHit("helpdesk/other", "Other reports")]
    );
    await searchFor(page, "reports");
    await expect(rowsOf(page)).toHaveCount(2);
    await expect(rowsOf(page).filter({ hasText: "Docs excerpt" })).toHaveCount(1);
    await expect(rowsOf(page).nth(1)).toContainText("Other reports");
  });

  docsTest("Converted Article does not drop other same-title pages", async ({ page, connected }) => {
    await stubSearch(
      page,
      [articleHit("Introduction", { is_converted: true })],
      [docHit("helpdesk/introduction", "Introduction"), docHit("crm/introduction", "Introduction")]
    );
    await searchFor(page, "introduction");
    await expect(rowsOf(page)).toHaveCount(3);
  });

  docsTest("rows above do not move when docs arrive", async ({ page, connected }) => {
    const docsGate = gate();
    await stubSearch(page, [articleHit("Alpha guide")], async () => {
      await docsGate.held;
      return [docHit("helpdesk/beta", "Beta guide")];
    });
    await searchFor(page, "guide");
    const first = rowsOf(page).first();
    await expect(first).toContainText("Alpha guide");
    const before = await first.boundingBox();
    expect(await page.getByText("No articles match").count()).toBe(0);
    docsGate.open();
    await expect(rowsOf(page)).toHaveCount(2);
    expect(await first.boundingBox()).toEqual(before);
    await expect(first).toContainText("Alpha guide");
  });

  docsTest("docs answered before Articles do not reorder rows", async ({ page, connected }) => {
    const articlesGate = gate();
    const asked = page.waitForResponse(DOCS_SEARCH);
    await stubSearch(
      page,
      async () => {
        await articlesGate.held;
        return [articleHit("Alpha guide")];
      },
      [docHit("helpdesk/beta", "Beta guide")]
    );
    await searchFor(page, "guide");
    await asked;
    await page.waitForTimeout(300);
    expect(await rowsOf(page).count()).toBe(0);
    articlesGate.open();
    await expect(rowsOf(page)).toHaveCount(2);
    await expect(rowsOf(page).nth(0)).toContainText("Alpha guide");
    await expect(rowsOf(page).nth(1)).toContainText("Beta guide");
  });

  docsTest("a failed docs answer drops the old Docs rows", async ({ page, connected }) => {
    await stubSearch(
      page,
      async (query) => [articleHit(query === "guide" ? "Alpha guide" : "New report")],
      async (query) => (query === "guide" ? [docHit("helpdesk/beta", "Beta guide")] : 500)
    );
    const box = await searchFor(page, "guide");
    await expect(rowsOf(page)).toHaveCount(2);
    await box.fill("report");
    await expect(rowsOf(page)).toHaveCount(1);
    await expect(rowsOf(page).first()).toContainText("New report");
    await expect(page.getByText(/unavailable|error|failed/i)).toHaveCount(0);
  });

  docsTest("no empty state while docs are pending", async ({ page, connected }) => {
    const docsGate = gate();
    const answered = page.waitForResponse(ARTICLE_SEARCH);
    await stubSearch(page, [], async () => {
      await docsGate.held;
      return [docHit("helpdesk/beta", "Beta guide")];
    });
    await searchFor(page, "guide");
    await answered;
    await page.waitForTimeout(400);
    expect(await page.getByText("No articles match").count()).toBe(0);
    docsGate.open();
    await expect(rowsOf(page)).toHaveCount(1);
  });

  docsTest("typing before the config loads still searches docs", async ({ page, connected }) => {
    const configGate = gate();
    await page.route("**/api/method/helpdesk.api.config.get_config*", async (route) => {
      await configGate.held;
      await route.continue();
    });
    const docsCalls = await stubSearch(page, [articleHit("Alpha guide")], [docHit("helpdesk/beta", "Beta guide")]);
    await searchFor(page, "guide");
    await expect(rowsOf(page)).toHaveCount(1);
    expect(docsCalls).toEqual([]);
    configGate.open();
    await expect(rowsOf(page)).toHaveCount(2);
  });

  test("no source sends no docs request", async ({ page }) => {
    const docsCalls = await stubSearch(page, [articleHit("Alpha guide")], [docHit("helpdesk/beta", "Beta guide")]);
    await searchFor(page, "guide");
    await expect(rowsOf(page)).toHaveCount(1);
    await page.waitForTimeout(500);
    expect(docsCalls).toEqual([]);
  });

  docsTest("a Docs row opens /help/articles/<route>", async ({ page, connected }) => {
    await stubDocs(page, { "helpdesk/beta": docPage("helpdesk/beta") });
    await stubSearch(page, [articleHit("Alpha guide")], [docHit("helpdesk/beta", "Beta <mark>guide</mark>")]);
    const box = await searchFor(page, "guide");
    await expect(rowsOf(page)).toHaveCount(2);
    await expect(rowsOf(page).nth(1).locator("mark")).toHaveText("guide");
    await box.press("ArrowDown");
    await box.press("ArrowDown");
    await box.press("Enter");
    await expect(page).toHaveURL(/\/help\/articles\/helpdesk\/beta$/);
    await expect(heading(page, "Doc helpdesk/beta")).toBeVisible();
  });
});
