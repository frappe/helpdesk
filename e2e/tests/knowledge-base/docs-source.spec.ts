import type { Page } from "@playwright/test";
import { expect, test, usePersona } from "../../helpers/fixtures";
import { chooseOption, createArticle, createCategory } from "../../helpers/portal";
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
  // Half a day of margin, so the label is 3 or 4 days at any hour.
  synced_on: new Date(Date.now() - 3.5 * 86400_000).toISOString().replace("T", " ").slice(0, 19),
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
  // click, not uncheck: the failed save flips the box back before uncheck can verify it.
  await dialog.getByRole("checkbox", { name: "Legal" }).click();
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
  await expect(dialog.getByText(/142 pages · synced [34] days ago/)).toBeVisible();
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

  docsTest("no old Docs row shows while a new query is in flight", async ({ page, connected }) => {
    const hold = gate();
    await stubSearch(
      page,
      async (query) => (query === "third" ? (await hold.held, []) : [articleHit(query === "guide" ? "Alpha guide" : "Art report")]),
      async (query) => (query === "guide" ? [docHit("helpdesk/old", "Stale guide")] : (await hold.held, []))
    );
    const box = await searchFor(page, "guide");
    await expect(rowsOf(page)).toHaveCount(2);
    const reportArticles = page.waitForResponse(ARTICLE_SEARCH);
    await box.fill("report");
    await reportArticles;
    await expect(rowsOf(page).filter({ hasText: "Art report" })).toHaveCount(1);
    await box.fill("third");
    await page.waitForTimeout(700);
    expect(await rowsOf(page).filter({ hasText: "Stale guide" }).count()).toBe(0);
    hold.open();
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

const suggestionLinks = (page: Page) =>
  page.locator("section").filter({ hasText: "Related articles:" }).getByRole("link");

async function typeSubject(page: Page, text: string) {
  await page.goto("/help/my-tickets/new");
  const box = page.getByPlaceholder("A short description");
  await box.fill(text);
  return box;
}

test.describe("ticket form suggestions", () => {
  docsTest("title match outranks an Article", async ({ page, connected }) => {
    await stubSearch(page, [articleHit("Account help"), articleHit("Billing")], [docHit("helpdesk/reset", "Reset password")]);
    await typeSubject(page, "reset password");
    await expect(suggestionLinks(page)).toHaveCount(3);
    await expect(suggestionLinks(page).first()).toContainText("Reset password");
  });

  docsTest("slot 3 goes to the best Docs page when none made it", async ({ page, connected }) => {
    await stubSearch(
      page,
      [articleHit("One"), articleHit("Two"), articleHit("Three")],
      [docHit("helpdesk/best", "Best page"), docHit("helpdesk/next", "Next page")]
    );
    await typeSubject(page, "zzz");
    await expect(suggestionLinks(page)).toHaveCount(3);
    await expect(suggestionLinks(page).nth(2)).toContainText("Best page");
  });

  docsTest("suggestions wait for both lists", async ({ page, connected }) => {
    const docsGate = gate();
    const answered = page.waitForResponse(ARTICLE_SEARCH);
    await stubSearch(page, [articleHit("One"), articleHit("Two")], async () => {
      await docsGate.held;
      return [docHit("helpdesk/best", "Best page")];
    });
    await typeSubject(page, "zzz");
    await answered;
    await page.waitForTimeout(500);
    expect(await suggestionLinks(page).count()).toBe(0);
    docsGate.open();
    await expect(suggestionLinks(page)).toHaveCount(3);
  });

  docsTest("a docs request held past 2s shows Articles once and later docs change nothing", async ({ page, connected }) => {
    const docsGate = gate();
    await stubSearch(page, [articleHit("One"), articleHit("Two")], async () => {
      await docsGate.held;
      return [docHit("helpdesk/best", "Best page")];
    });
    await typeSubject(page, "zzz");
    const started = Date.now();
    await expect(suggestionLinks(page)).toHaveCount(2);
    const waited = Date.now() - started;
    expect(waited).toBeGreaterThan(1500);
    expect(waited).toBeLessThan(3200);
    docsGate.open();
    await page.waitForTimeout(700);
    expect(await suggestionLinks(page).count()).toBe(2);
    await expect(suggestionLinks(page).nth(1)).toContainText("Two");
  });

  docsTest("late Articles for a cut subject do not come back", async ({ page, connected }) => {
    const hold = gate();
    await stubSearch(page, async () => (await hold.held, [articleHit("Stale article")]), []);
    const box = await typeSubject(page, "abcd");
    await page.waitForTimeout(500);
    await box.fill("ab");
    hold.open();
    await page.waitForTimeout(800);
    expect(await suggestionLinks(page).count()).toBe(0);
  });

  docsTest("the cap timer of an old subject shows nothing for the new one", async ({ page, connected }) => {
    const hold = gate();
    await stubSearch(
      page,
      async (query) => (query === "older" ? [articleHit("Older link")] : (await hold.held, [articleHit("Newer link")])),
      async () => (await hold.held, [])
    );
    const box = await typeSubject(page, "older");
    await page.waitForTimeout(1000);
    await box.fill("newer");
    await page.waitForTimeout(2500);
    expect(await suggestionLinks(page).filter({ hasText: "Older link" }).count()).toBe(0);
    hold.open();
    await expect(suggestionLinks(page)).toHaveCount(1);
    await expect(suggestionLinks(page).first()).toContainText("Newer link");
  });

  docsTest("slow Articles do not push the cap past 2s from the search", async ({ page, connected }) => {
    const docsGate = gate();
    await stubSearch(
      page,
      async () => {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        return [articleHit("Slow article")];
      },
      async () => (await docsGate.held, [docHit("helpdesk/best", "Best page")])
    );
    await typeSubject(page, "zzz");
    const started = Date.now();
    await expect(suggestionLinks(page)).toHaveCount(1);
    expect(Date.now() - started).toBeLessThan(3000);
    docsGate.open();
  });

  docsTest("held Articles with answered docs still show the Docs pages", async ({ page, connected }) => {
    const hold = gate();
    await stubSearch(page, async () => (await hold.held, [articleHit("Late article")]), [docHit("helpdesk/best", "Best page")]);
    await typeSubject(page, "zzz");
    await expect(suggestionLinks(page)).toHaveCount(1, { timeout: 5000 });
    await expect(suggestionLinks(page).first()).toContainText("Best page");
    hold.open();
    await page.waitForTimeout(500);
    expect(await suggestionLinks(page).count()).toBe(1);
  });

  docsTest("an empty deadline does not lose a late answer", async ({ page, connected }) => {
    const hold = gate();
    await stubSearch(page, async () => (await hold.held, [articleHit("Late article")]), async () => (await hold.held, []));
    await typeSubject(page, "zzz");
    await page.waitForTimeout(2800);
    expect(await suggestionLinks(page).count()).toBe(0);
    hold.open();
    await expect(suggestionLinks(page)).toHaveCount(1);
  });

  docsTest("a failed config load still shows Articles", async ({ page, connected }) => {
    await page.route("**/api/method/helpdesk.api.config.get_config*", (route) =>
      route.fulfill({ status: 500, json: { exc_type: "ValidationError" } })
    );
    await stubSearch(page, [articleHit("Alpha guide")], [docHit("helpdesk/beta", "Beta guide")]);
    await typeSubject(page, "guide");
    await expect(suggestionLinks(page)).toHaveCount(1, { timeout: 5000 });
    await expect(suggestionLinks(page).first()).toContainText("Alpha guide");
  });

  docsTest("a failed docs answer does not bring back the old Docs pages", async ({ page, connected }) => {
    await stubSearch(
      page,
      async (query) => [articleHit(query === "first" ? "Alpha" : "Beta")],
      async (query) => (query === "first" ? [docHit("helpdesk/old", "Old docs")] : 500)
    );
    const box = await typeSubject(page, "first");
    await expect(suggestionLinks(page)).toHaveCount(2);
    await box.fill("second");
    await expect(suggestionLinks(page)).toHaveCount(1);
    await expect(suggestionLinks(page).first()).toContainText("Beta");
  });

  docsTest("a failed Articles answer does not bring back the old Articles", async ({ page, connected }) => {
    await stubSearch(
      page,
      async (query) => (query === "first" ? [articleHit("Alpha")] : 500),
      async (query) => (query === "first" ? [] : [docHit("helpdesk/new", "New docs")])
    );
    const box = await typeSubject(page, "first");
    await expect(suggestionLinks(page)).toHaveCount(1);
    await box.fill("second");
    await expect(suggestionLinks(page).first()).toContainText("New docs");
    await expect(suggestionLinks(page)).toHaveCount(1);
  });

  docsTest("old suggestions stay until the new list is ready", async ({ page, connected }) => {
    const hold = gate();
    await stubSearch(
      page,
      async (query) => [articleHit(query === "first" ? "Old link" : "New link")],
      async (query) => (query === "first" ? [] : (await hold.held, []))
    );
    const box = await typeSubject(page, "first");
    await expect(suggestionLinks(page)).toHaveCount(1);
    await box.fill("second");
    await page.waitForTimeout(700);
    await expect(suggestionLinks(page).first()).toContainText("Old link");
    hold.open();
    await expect(suggestionLinks(page).first()).toContainText("New link");
    await box.fill("ab");
    await expect(suggestionLinks(page)).toHaveCount(0);
  });

  docsTest("source failure still shows Articles", async ({ page, connected }) => {
    await stubSearch(page, [articleHit("Alpha guide")], async () => 500);
    await typeSubject(page, "guide");
    await expect(suggestionLinks(page)).toHaveCount(1);
    await expect(suggestionLinks(page).first()).toContainText("Alpha guide");
  });

  docsTest("an Articles failure still shows Docs pages", async ({ page, connected }) => {
    await stubSearch(page, async () => 500, [docHit("helpdesk/beta", "Beta guide")]);
    await typeSubject(page, "guide");
    await expect(suggestionLinks(page)).toHaveCount(1);
    await expect(suggestionLinks(page).first()).toContainText("Beta guide");
  });

  docsTest("typing before the config loads waits, then shows both lists", async ({ page, connected }) => {
    const configGate = gate();
    await page.route("**/api/method/helpdesk.api.config.get_config*", async (route) => {
      await configGate.held;
      await route.continue();
    });
    await stubSearch(page, [articleHit("Alpha guide")], [docHit("helpdesk/beta", "Beta guide")]);
    await typeSubject(page, "guide");
    await page.waitForTimeout(700);
    expect(await suggestionLinks(page).count()).toBe(0);
    configGate.open();
    await expect(suggestionLinks(page)).toHaveCount(2);
  });

  test("no source sends no docs request and waits for none", async ({ page }) => {
    const docsCalls = await stubSearch(page, [articleHit("Alpha guide")], [docHit("helpdesk/beta", "Beta guide")]);
    await typeSubject(page, "guide");
    await expect(suggestionLinks(page)).toHaveCount(1);
    expect(docsCalls).toEqual([]);
  });

  docsTest("a Docs suggestion opens in a new tab and keeps the draft", async ({ page, connected }) => {
    await stubDocs(page, { "helpdesk/beta": docPage("helpdesk/beta") });
    await stubSearch(page, [], [docHit("helpdesk/beta", "Beta guide")]);
    const box = await typeSubject(page, "guide");
    const link = suggestionLinks(page).first();
    await expect(link).toHaveAttribute("href", "/help/articles/helpdesk/beta");
    await expect(link).toHaveAttribute("target", "_blank");
    await link.hover();
    await expect(page.getByText("Docs excerpt")).toBeVisible();
    const [popup] = await Promise.all([page.waitForEvent("popup"), link.click()]);
    await expect(popup).toHaveURL(/\/help\/articles\/helpdesk\/beta$/);
    await expect(box).toHaveValue("guide");
  });

  test.describe("desk", () => {
    test.use({ storageState: "e2e/.auth/agent.json" });

    test("desk TicketNew still fetches nothing", async ({ page }) => {
      const asked: string[] = [];
      page.on("request", (req) => /search_articles|search_docs/.test(req.url()) && asked.push(req.url()));
      await page.goto("/helpdesk/tickets/new");
      await page.getByPlaceholder("A short description").fill("a long enough subject");
      await page.waitForTimeout(700);
      expect(asked).toEqual([]);
    });
  });
});

const CATEGORIES = "**/api/method/helpdesk.api.knowledge_base.get_category_options*";
const CONVERT = "**/api/method/helpdesk.api.docs_source.convert_docs_page*";
const LIST = "**/api/method/helpdesk.api.docs_source.list_docs_pages*";
const BULK = "**/api/method/helpdesk.api.docs_source.bulk_convert_docs_pages*";
const RESULT = "**/api/method/helpdesk.api.docs_source.get_bulk_convert_result*";
const dialogOf = (page: Page) => page.getByRole("dialog");

async function stubCategories(page: Page) {
  await page.route(CATEGORIES, (route) =>
    route.fulfill(json([{ value: "cat-1", label: "Guides" }, { value: "cat-2", label: "Billing" }]))
  );
}

function listed(count: number, section: string, fields: Record<string, unknown> = {}) {
  return Array.from({ length: count }, (_, i) => ({
    route: `${section}/p${i}`,
    title: `${section} page ${i}`,
    section,
    converted: null,
    matching: null,
    ...fields,
  }));
}

test.describe("convert: customer", () => {
  test.use({ storageState: "e2e/.auth/customer.json" });

  docsTest("readers see no Convert button", async ({ page, connected }) => {
    await stubDocs(page, { "helpdesk/setup": docPage("helpdesk/setup") });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(heading(page, "Doc helpdesk/setup")).toBeVisible();
    await expect(page.getByRole("button", { name: "Convert to article" })).toHaveCount(0);
  });
});

test.describe("convert: one page", () => {
  docsTest("an agent converts one page into a draft", async ({ page, api, connected }) => {
    const article = await seedArticle(api);
    await stubCategories(page);
    await stubDocs(page, { "helpdesk/setup": docPage("helpdesk/setup", { converted: null, matching: null }) });
    let sent: any;
    await page.route(CONVERT, (route) => {
      sent = route.request().postDataJSON();
      return route.fulfill(json(article.name));
    });
    await page.goto("/help/articles/helpdesk/setup");
    await page.getByRole("button", { name: "Convert to article" }).click();
    const submit = dialogOf(page).getByRole("button", { name: "Convert", exact: true });
    await expect(submit).toBeDisabled();
    await chooseOption(page, "Guides");
    await expect(submit).toBeEnabled();
    const [popup] = await Promise.all([page.waitForEvent("popup"), submit.click()]);
    await expect(popup).toHaveURL(new RegExp(`/helpdesk/kb/articles/${article.name}`));
    expect(sent).toEqual({ route: "helpdesk/setup", category: "cat-1" });
    await expect(heading(page, "Doc helpdesk/setup")).toBeVisible();
  });

  docsTest("a converted page links to its Article", async ({ page, connected }) => {
    await stubDocs(page, {
      "helpdesk/setup": docPage("helpdesk/setup", { converted: { name: "ART-9", title: "Setup draft" } }),
    });
    await page.goto("/help/articles/helpdesk/setup");
    await expect(page.getByRole("button", { name: "Convert to article" })).toHaveCount(0);
    const link = page.getByRole("link", { name: "Setup draft" });
    await expect(link).toHaveAttribute("href", "/helpdesk/kb/articles/ART-9");
    await expect(link).toHaveAttribute("target", "_blank");
  });

  docsTest("a Matching Article shows a warning, not a block", async ({ page, connected }) => {
    await stubCategories(page);
    await stubDocs(page, {
      "helpdesk/setup": docPage("helpdesk/setup", { matching: { name: "ART-5", title: "Existing setup" } }),
    });
    await page.goto("/help/articles/helpdesk/setup");
    await page.getByRole("button", { name: "Convert to article" }).click();
    const link = dialogOf(page).getByRole("link", { name: "Existing setup" });
    await expect(link).toHaveAttribute("href", "/helpdesk/kb/articles/ART-5");
    await chooseOption(page, "Guides");
    await expect(dialogOf(page).getByRole("button", { name: "Convert", exact: true })).toBeEnabled();
  });
});

test.describe("convert: bulk", () => {
  async function openBulk(page: Page, source: unknown, pages: any[] | ((section: string | null) => any[])) {
    await stubCategories(page);
    await page.route(LIST, (route) => {
      const section = new URL(route.request().url()).searchParams.get("section");
      return route.fulfill(json(typeof pages === "function" ? pages(section) : pages));
    });
    return open(page, source);
  }

  test("bulk list groups by section and searches", async ({ page }) => {
    const pages = [
      ...listed(2, "Guides"),
      ...listed(1, "Legal"),
      { ...listed(1, "Legal")[0], route: "legal/done", title: "Legal done", converted: { name: "ART-1", title: "Legal copy" } },
    ];
    const dialog = await openBulk(page, INDEXED, pages);
    await expect(dialog.getByRole("button", { name: "Guides" })).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Legal", exact: true })).toBeVisible();
    await dialog.getByRole("button", { name: "Guides" }).click();
    await expect(dialog.getByRole("checkbox", { name: "Guides page 1" })).toBeVisible();
    await dialog.getByPlaceholder("Search pages").fill("page 1");
    await expect(dialog.getByRole("checkbox", { name: "Guides page 0" })).toHaveCount(0);
    await expect(dialog.getByRole("checkbox", { name: "Guides page 1" })).toBeVisible();
    await dialog.getByPlaceholder("Search pages").fill("Legal done");
    await expect(dialog.getByRole("checkbox", { name: "Legal done" })).toHaveCount(0);
    await expect(dialog.getByRole("link", { name: "Legal copy" })).toHaveAttribute("href", "/helpdesk/kb/articles/ART-1");
  });

  test("wiki sections load pages lazily", async ({ page }) => {
    const asked: (string | null)[] = [];
    const dialog = await openBulk(page, WIKI, (section) => {
      asked.push(section);
      return listed(2, section!);
    });
    expect(asked).toEqual([]);
    await dialog.getByRole("button", { name: "Legal", exact: true }).click();
    await expect(dialog.getByRole("checkbox", { name: "legal page 0" })).toBeVisible();
    expect(asked).toEqual(["legal"]);
  });

  test("bulk refuses a 51st tick", async ({ page }) => {
    const dialog = await openBulk(page, INDEXED, listed(60, "Guides"));
    await dialog.getByRole("button", { name: "Guides" }).click();
    for (let i = 0; i < 50; i++) await dialog.getByRole("checkbox", { name: `Guides page ${i}`, exact: true }).check();
    await expect(dialog.getByRole("checkbox", { name: "Guides page 50", exact: true })).toBeDisabled();
    await expect(dialog.getByText("You can pick up to 50 pages at a time.")).toBeVisible();
    await dialog.getByRole("checkbox", { name: "Guides page 0", exact: true }).uncheck();
    await expect(dialog.getByRole("checkbox", { name: "Guides page 50", exact: true })).toBeEnabled();
  });

  test("bulk shows 42 created, 8 skipped and shows API errors", async ({ page }) => {
    const dialog = await openBulk(page, INDEXED, listed(3, "Guides", { matching: { name: "ART-5", title: "Same" } }));
    let enqueued = 0;
    let results = 0;
    let sent: any;
    await page.route(BULK, (route) => {
      enqueued++;
      if (enqueued === 1) {
        return route.fulfill({
          status: 417,
          json: { exc_type: "ValidationError", _server_messages: JSON.stringify([JSON.stringify({ message: "A bulk convert is already running." })]) },
        });
      }
      sent = route.request().postDataJSON();
      return route.fulfill(json(null));
    });
    await page.route(RESULT, (route) => route.fulfill(json(++results < 2 ? null : { created: 42, skipped: 8 })));
    await dialog.getByRole("button", { name: "Guides" }).click();
    await dialog.getByRole("checkbox", { name: "Guides page 0" }).check();
    await dialog.getByRole("checkbox", { name: "Guides page 1" }).check();
    await dialog.getByRole("button", { name: "Convert 2 pages" }).click();
    await chooseOption(page, "Billing");
    await dialogOf(page).last().getByRole("button", { name: "Convert", exact: true }).click();
    await expect(page.getByText("A bulk convert is already running.")).toBeVisible();
    await dialogOf(page).last().getByRole("button", { name: "Convert", exact: true }).click();
    await expect(dialog.getByText("42 created, 8 skipped")).toBeVisible({ timeout: 10_000 });
    expect(sent).toEqual({ routes: ["Guides/p0", "Guides/p1"], category: "cat-2" });
    expect(results).toBe(2);
  });
});

test("desk Article shows Copied from docs on <date>", async ({ page, api }) => {
  const article = await seedArticle(api);
  await api.update("HD Article", article.name, {
    docs_page_url: `${SOURCE}/helpdesk/setup`,
    docs_copied_on: "2026-03-04 12:00:00",
  });
  await page.goto(`/helpdesk/kb/articles/${article.name}`);
  const link = page.getByRole("link", { name: "Copied from docs on Mar 4, 2026" });
  await expect(link).toHaveAttribute("href", `${SOURCE}/helpdesk/setup`);
  await expect(link).toHaveAttribute("target", "_blank");
});
