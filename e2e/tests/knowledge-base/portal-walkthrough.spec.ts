import type { Page } from "@playwright/test";
import { expect, test as base, uid, usePersona } from "../../helpers/fixtures";
import { raiseTicket } from "../../helpers/factories";
import { PASSWORD, personas } from "../../helpers/personas";
import { createArticle, createCategory, indexArticles } from "../../helpers/portal";
import { snapshotSettings } from "../../helpers/settings";

// Every route and control a reader meets on the Studio portal's knowledge base, per persona.
// The ids in the titles (R1, H9, K2, ...) follow the portal walkthrough checklist.

const KB_SETTINGS = ["public_knowledge_base", "allow_anonymous_article_voting", "banner_preset"];
const QUICK_LINKS = "Knowledge Base Quick Links";
const GUEST = { storageState: { cookies: [], origins: [] } };
const PHONE = { width: 390, height: 844 };

/** `kb(values)` sets the knowledge base settings for one test; they are put back after it. */
const test = base.extend<{ kb: (values: Record<string, any>) => Promise<void> }>({
  kb: async ({ api }, use) => {
    const restore = await snapshotSettings(api, KB_SETTINGS);
    await use((values) => api.update("HD Settings", "HD Settings", values));
    await restore();
  },
});

/** A category holding one article per audience, plus a draft. */
async function seedAudiences(api) {
  const category = await createCategory(api);
  const make = (visibility: string, status = "Published") =>
    createArticle(api, category.name, { title: `${visibility} ${status} ${uid()}`, visibility, status });
  return {
    category,
    public: await make("Public"),
    customers: await make("Customers"),
    agents: await make("Private"),
    draft: await make("Public", "Draft"),
  };
}

function searchBox(page: Page) {
  return page.getByRole("combobox", { name: /Search articles/ });
}

function accountMenu(page: Page) {
  return page.getByRole("button", { name: "Helpdesk", exact: true });
}

test.describe("routing", () => {
  test.describe("guest, private knowledge base", () => {
    test.use(GUEST);

    test("R1 sends a guest to login and back", async ({ page, kb }) => {
      await kb({ public_knowledge_base: 0 });
      await page.goto("/help/categories?a=1");
      await expect(page).toHaveURL(/\/login\?redirect-to=%2Fhelp%2Fcategories%3Fa%3D1/);
      await page.locator("#login_email").fill(personas.customer.email);
      await page.locator("#login_password").fill(PASSWORD);
      await page.getByRole("button", { name: "Continue", exact: true }).click();
      await expect(page).toHaveURL(/\/help\/categories\?a=1$/);
    });
  });

  test.describe("guest, public knowledge base", () => {
    test.use(GUEST);

    test("R3 ticket pages send a guest to login with the query kept", async ({ page, kb, apiAs }) => {
      await kb({ public_knowledge_base: 1 });
      const ticket = await raiseTicket(await apiAs("customer"));
      for (const path of ["/help/my-tickets?x=1", "/help/tickets/new?from=search&q=hi", `/help/tickets/${ticket.name}`]) {
        await page.goto(path);
        await expect(page).toHaveURL(`/login?redirect-to=${encodeURIComponent(path)}`);
      }
    });

    test("R4 an unknown path sends a public guest to login, not a 404 (finding 3)", async ({ page, kb }) => {
      await kb({ public_knowledge_base: 1 });
      await page.goto("/help/no-such-page");
      await expect(page).toHaveURL(/\/login\?redirect-to=%2Fhelp%2Fno-such-page/);
    });
  });

  test.describe("customer", () => {
    usePersona("customer");

    test("R5 an unknown path shows Not Found with a way home", async ({ page }) => {
      await page.goto("/help/no-such-page");
      await expect(page.getByText("The page you are looking for does not exist.")).toBeVisible();
      await page.getByRole("link", { name: "Back to Home" }).click();
      await expect(page).toHaveURL(/\/help\/?$/);
    });

    test("R6 /help and /help/ open the knowledge base home", async ({ page }) => {
      for (const path of ["/help", "/help/"]) {
        await page.goto(path);
        await expect(page.getByRole("heading", { name: "Here's what might help" })).toBeVisible();
      }
    });

    test("R7–R12 old desk portal links land on the new routes", async ({ page, api }) => {
      const category = await createCategory(api);
      const article = await createArticle(api, category.name, { title: `Old link ${uid()}` });
      const cases: [string, RegExp][] = [
        ["/helpdesk/my-tickets?x=1", /\/help\/my-tickets\?x=1$/],
        ["/helpdesk/my-tickets/new?from=article", /\/help\/tickets\/new\?from=article$/],
        ["/helpdesk/kb-public", /\/help\/?$/],
        [`/helpdesk/kb-public/articles/${article.name}`, new RegExp(`/help/articles/${article.name}-old-link-`)],
        [`/helpdesk/kb-public/${category.name}`, new RegExp(`/help/category/${category.name}$`)],
      ];
      for (const [from, to] of cases) {
        await page.goto(from);
        await expect(page, from).toHaveURL(to);
      }
    });

    test("R15 any other desk route sends a customer to the portal", async ({ page }) => {
      await page.goto("/helpdesk/teams");
      await expect(page).toHaveURL(/\/help\/?$/);
    });
  });
});

test.describe("header", () => {

  test.describe("admin preview", () => {
    usePersona("admin");

    test("H15 ?preview=1 shows the stored draft for the rest of the tab", async ({ page, api }) => {
      const category = await createCategory(api);
      await createArticle(api, category.name);
      await page.goto("/help");
      await page.evaluate(
        ([pinned]) =>
          localStorage.setItem(
            "kb:preview",
            JSON.stringify({ banner_image: "", banner_preset: "Violet", pinned: [pinned], links: [{ label: "E2E Preview link", url: "https://example.com", open_in_new_tab: false }] })
          ),
        [category.name]
      );
      await page.goto("/help?preview=1");
      await expect(page.getByRole("link", { name: "E2E Preview link" })).toBeVisible();
      await expect(page.getByRole("heading", { name: category.category_name, level: 2 })).toBeVisible();
      await page.goto("/help/categories");
      await expect(page.getByRole("link", { name: "E2E Preview link" })).toBeVisible();
      await page.evaluate(() => localStorage.removeItem("kb:preview"));
    });
  });
});

test.describe("knowledge base home", () => {
  usePersona("customer");

  test("K1 the hero shows the title and the banner preset", async ({ page, kb }) => {
    await kb({ banner_preset: "Blue" });
    await page.goto("/help");
    const title = page.getByRole("heading", { name: "Here's what might help", level: 1 });
    await expect(title).toBeVisible();
    await expect(page.getByText("Explore answers to frequently asked questions")).toBeVisible();
    const background = await page.evaluate(() =>
      [...document.querySelectorAll<HTMLElement>("*")].map((el) => el.style.background).find((bg) => bg.includes("surface-blue"))
    );
    expect(background).toContain("surface-blue");
  });

  test("K2–K8 search, keyboard, no results, recently viewed", async ({ page, api }) => {
    const word = `zq${uid()}`;
    const category = await createCategory(api);
    const article = await createArticle(api, category.name, { title: `Searchable ${word} guide` });
    await indexArticles(api, word);

    await page.goto("/help");
    // K6: "/" focuses the box.
    await page.locator("body").press("/");
    await expect(searchBox(page)).toBeFocused();

    // K2: fewer than three characters sends nothing.
    let searches = 0;
    page.on("request", (request) => request.url().includes("search_articles") && searches++);
    await searchBox(page).fill("zq");
    await page.waitForTimeout(600);
    expect(searches).toBe(0);

    await searchBox(page).fill(word);
    await expect(page.getByText("1 article")).toBeVisible();
    await expect(page.locator("mark", { hasText: word }).first()).toBeVisible();
    // K3: arrows and Enter open the hit.
    await searchBox(page).press("ArrowDown");
    await searchBox(page).press("Enter");
    await expect(page).toHaveURL(new RegExp(`/help/articles/${article.name}-searchable-`));

    // K4: no results offers a ticket with the search text.
    await page.goto("/help");
    await searchBox(page).fill(`nothing${word}`);
    await expect(page.getByText(`No articles match “nothing${word}”`)).toBeVisible();
    await expect(page.getByText("Try other words, or ask our team.")).toBeVisible();
    await page.getByRole("button", { name: "Create a ticket" }).first().click();
    await expect(page).toHaveURL(new RegExp(`/help/tickets/new\\?from=search&q=nothing${word}`));
    await expect(page.getByPlaceholder("A short description")).toHaveValue(`nothing${word}`);

    // K7: the article just opened is under Recently viewed.
    await page.goto("/help");
    await searchBox(page).click();
    await expect(page.getByText("Recently viewed")).toBeVisible();
    const recent = page.getByRole("option", { name: new RegExp(`Searchable ${word}`) });
    await expect(recent).toBeVisible();
    // K8: Remove drops it.
    await recent.hover();
    await recent.getByRole("button", { name: "Remove" }).click();
    await expect(recent).toHaveCount(0);
  });

  test("K9 recently viewed is kept per user", async ({ page, api }) => {
    const category = await createCategory(api);
    const article = await createArticle(api, category.name);
    await page.goto(`/help/articles/${article.name}`);
    await expect(page.getByRole("heading", { name: article.title, level: 1 })).toBeVisible();
    const lists = await page.evaluate(() =>
      Object.fromEntries(Object.keys(localStorage).filter((key) => key.startsWith("helpdesk-kb-recent")).map((key) => [key, JSON.parse(localStorage.getItem(key) || "[]")]))
    );
    expect(lists[`helpdesk-kb-recent-articles:${personas.customer.email}`][0].name).toBe(article.name);
    // The guest's list, written while the session loads, must not get the customer's reading.
    expect.soft(lists["helpdesk-kb-recent-articles:Guest"] || []).toEqual([]);
  });

  test("K15 a lone pinned category gets its own layout", async ({ page, api }) => {
    const category = await createCategory(api);
    const articles = [await createArticle(api, category.name), await createArticle(api, category.name)];
    try {
      await api.update("HD Article Category", category.name, { pinned: 1, pinned_order: 1 });
      await page.goto("/help");
      await expect(page.getByRole("heading", { name: category.category_name })).toBeVisible();
      for (const article of articles) await expect(page.getByRole("link", { name: article.title })).toBeVisible();
      await expect(page.getByRole("radio", { name: "Popular" })).toHaveCount(0);
      await page.getByRole("button", { name: "View all categories" }).click();
      await expect(page).toHaveURL(/\/help\/categories$/);
    } finally {
      await api.update("HD Article Category", category.name, { pinned: 0, pinned_order: 0 });
    }
  });

  test("K14 Latest and Popular tabs sort the articles", async ({ page, api }) => {
    const category = await createCategory(api);
    const popular = await createArticle(api, category.name, { title: `Popular ${uid()}` });
    // Above any earlier run's articles; HD Article.views is a 32 bit int.
    await api.update("HD Article", popular.name, { views: Math.floor(Date.now() / 1000) });
    const latest = await createArticle(api, category.name, { title: `Latest ${uid()}` });
    await page.goto("/help");
    const articles = page.locator('[data-component-id="Repeater-9o4hxaycp"]').getByRole("link");
    await expect(articles.first()).toContainText(latest.title);
    await page.getByRole("radio", { name: "Popular" }).click();
    await expect(articles.first()).toContainText(popular.title);
    await articles.first().press("Enter");
    await expect(page).toHaveURL(new RegExp(`/help/articles/${popular.name}-`));
  });
});

test.describe("audiences", () => {
  test.describe("guest", () => {
    test.use(GUEST);

    test("K16 CT3 AR4 AR21 AR24 a guest reads public articles only and cannot vote", async ({ page, api, kb }) => {
      await kb({ public_knowledge_base: 1, allow_anonymous_article_voting: 0 });
      const seeded = await seedAudiences(api);
      const only = await createCategory(api);
      await createArticle(api, only.name, { visibility: "Customers" });

      await page.goto(`/help/category/${seeded.category.name}`);
      await expect(page.getByText("1 article", { exact: true })).toBeVisible();
      await expect(page.getByRole("link", { name: seeded.public.title }).last()).toBeVisible();
      await expect(page.getByRole("link", { name: seeded.customers.title })).toHaveCount(0);

      await page.goto(`/help/category/${only.name}`);
      await expect(page.getByText("Category not found")).toBeVisible();
      await page.goto(`/help/articles/${seeded.customers.name}`);
      await expect(page.getByText("Article not found")).toBeVisible();

      await page.goto(`/help/articles/${seeded.public.name}`);
      await expect(page.getByRole("heading", { name: seeded.public.title, level: 1 })).toBeVisible();
      await expect(page.getByRole("button", { name: "Yes, it was helpful" })).toHaveCount(0);
      await expect(page.getByRole("link", { name: "here", exact: true })).toHaveCount(0);
      const vote = await page.request.post("/api/method/helpdesk.api.knowledge_base.set_article_feedback", {
        form: { article: seeded.public.name, value: "1" },
      });
      expect(vote.status()).toBe(403);
    });

    test("AR20 a guest votes with a visitor cookie when anonymous voting is on", async ({ page, api, kb }) => {
      await kb({ public_knowledge_base: 1, allow_anonymous_article_voting: 1 });
      const category = await createCategory(api);
      const article = await createArticle(api, category.name);
      await page.goto(`/help/articles/${article.name}`);
      await page.getByRole("button", { name: "Yes, it was helpful" }).click();
      await expect(page.getByText("Thanks for your feedback!")).toBeVisible();
      const cookie = (await page.context().cookies()).find((row) => row.name === "hd_visitor");
      expect(cookie?.httpOnly).toBe(true);
      const [row] = await api.list("HD Article Feedback", { filters: { article: article.name }, fields: ["feedback", "visitor_id", "user"] });
      expect(row.feedback).toBe("1");
      expect(row.visitor_id).toBeTruthy();
      // AR19: the vote is still shown on a revisit.
      await page.reload();
      await expect(page.getByRole("button", { name: "Yes, it was helpful" })).toHaveAttribute("aria-pressed", "true");
    });
  });

  test.describe("customer", () => {
    usePersona("customer");

    test("K16 CT1 AR4 a customer reads public and customer articles", async ({ page, api }) => {
      const seeded = await seedAudiences(api);
      await page.goto(`/help/category/${seeded.category.name}`);
      await expect(page.getByRole("heading", { name: seeded.category.category_name, level: 1 })).toBeVisible();
      await expect(page.getByText("2 articles", { exact: true })).toBeVisible();
      await expect(page.getByText("By Administrator")).toBeVisible();
      await expect(page.getByRole("link", { name: seeded.customers.title }).last()).toBeVisible();
      await expect(page.getByRole("link", { name: seeded.agents.title })).toHaveCount(0);
      for (const hidden of [seeded.agents, seeded.draft]) {
        await page.goto(`/help/articles/${hidden.name}`);
        await expect(page.getByText("Article not found")).toBeVisible();
      }
    });
  });

  test.describe("agent", () => {
    usePersona("agent");

    test("K16 AR5 an agent reads every audience and drafts", async ({ page, api }) => {
      const seeded = await seedAudiences(api);
      await page.goto(`/help/category/${seeded.category.name}`);
      await expect(page.getByText("3 articles", { exact: true })).toBeVisible();
      for (const article of [seeded.agents, seeded.draft]) {
        await page.goto(`/help/articles/${article.name}`);
        await expect(page.getByRole("heading", { name: article.title, level: 1 })).toBeVisible();
      }
    });
  });
});

test.describe("categories and category pages", () => {
  usePersona("customer");

  test("CT2–CT5 article list, sidebar toggle and sidebar search", async ({ page, api }) => {
    const category = await createCategory(api);
    const other = await createCategory(api);
    const article = await createArticle(api, category.name, { title: `Sidebar ${uid()}` });
    const otherArticle = await createArticle(api, other.name, { title: `Elsewhere ${uid()}` });

    await page.goto("/help/category/no-such-category");
    await expect(page.getByText("Category not found")).toBeVisible();

    await page.goto(`/help/category/${category.name}`);
    const sidebar = page.getByRole("navigation", { name: "Knowledge base" });
    await expect(sidebar.getByRole("button", { name: category.category_name })).toHaveAttribute("aria-expanded", "true");
    await sidebar.getByRole("button", { name: other.category_name }).click();
    await expect(sidebar.getByRole("button", { name: other.category_name })).toHaveAttribute("aria-expanded", "true");
    await expect(sidebar.getByRole("button", { name: category.category_name })).toHaveAttribute("aria-expanded", "false");
    await expect(sidebar.getByRole("link", { name: otherArticle.title })).toBeVisible();

    // The test browser reports Windows, so the shortcut is Ctrl+K.
    await page.locator("body").press("Control+k");
    const search = sidebar.getByRole("textbox", { name: "Search articles" });
    await expect(search).toBeFocused();
    await search.fill(article.title);
    await expect(sidebar.getByRole("link", { name: article.title })).toBeVisible();
    await expect(sidebar.getByRole("link", { name: otherArticle.title })).toHaveCount(0);
    await search.fill(`nothing ${uid()}`);
    await expect(sidebar.getByText(/No articles match/)).toBeVisible();
    await search.fill("");

    // CT2: the list row opens the article.
    await page.locator("main, body").getByRole("link", { name: article.title }).last().click();
    await expect(page).toHaveURL(new RegExp(`/help/articles/${article.name}-`));
    // AR26: the sidebar marks the article being read.
    await expect(sidebar.getByRole("link", { name: article.title })).toHaveAttribute("aria-current", "page");
  });
});

test.describe("article page", () => {
  usePersona("customer");
  test.use({ permissions: ["clipboard-read", "clipboard-write"] });

  test("AR1 AR2 bare and stale links settle on the slug, keeping the hash", async ({ page, api }) => {
    const category = await createCategory(api);
    const article = await createArticle(api, category.name, { title: `Slug test ${uid()}` });
    const slug = article.title.toLowerCase().replace(/\s+/g, "-");
    await page.goto(`/help/articles/${article.name}#part`);
    await expect(page).toHaveURL(`/help/articles/${article.name}-${slug}#part`);
    await page.goto(`/help/articles/${article.name}-an-old-title`);
    await expect(page).toHaveURL(`/help/articles/${article.name}-${slug}`);
  });

  test("AR3 a heading link opens at that heading (finding 2)", async ({ page, api }) => {
    const category = await createCategory(api);
    const filler = "<p>" + "word ".repeat(600) + "</p>";
    const article = await createArticle(api, category.name, {
      content: `<h2>First part</h2>${filler}<h2>Deep part</h2>${filler}`,
    });
    await page.goto(`/help/articles/${article.name}#deep-part`);
    const heading = page.getByRole("heading", { name: "Deep part" });
    await expect(heading).toBeVisible();
    await page.waitForTimeout(1000);
    await expect(heading, "the page should scroll to the linked heading").toBeInViewport({ timeout: 2000 });
  });

  test("AR6 AR7 AR9–AR12 meta line, view count and copy actions", async ({ page, api, context }) => {
    const category = await createCategory(api);
    const article = await createArticle(api, category.name, { title: `Copy me ${uid()}`, visibility: "Customers" });
    await page.goto(`/help/articles/${article.name}`);
    await expect(page.getByText("1 minute to read")).toBeVisible();
    await expect(page.getByText("Administrator").last()).toBeVisible();
    await expect.poll(async () => (await api.get("HD Article", article.name)).views).toBe(1);

    await page.getByText("Copy link").click();
    await expect(page.getByText("Link copied")).toBeVisible();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(page.url());

    await page.getByRole("button", { name: "Copy for LLM" }).click();
    await expect(page.getByText("Copied as Markdown")).toBeVisible();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toContain(`# ${article.title}`);

    await page.getByRole("button", { name: "More ways to use this article with an LLM" }).click();
    await expect(page.getByRole("menuitem", { name: "Copy as Markdown" })).toBeVisible();
    // AR12: a Customers article is never offered to outside LLMs.
    await expect(page.getByRole("menuitem", { name: "Open in ChatGPT" })).toHaveCount(0);
    const popup = context.waitForEvent("page");
    await page.getByRole("menuitem", { name: "View as Markdown" }).click();
    const markdown = await popup;
    await expect(markdown.locator("body")).toContainText(`# ${article.title}`);
    await markdown.close();

    // AR7: a second visit within the hour adds no view.
    await page.reload();
    await expect(page.getByRole("heading", { name: article.title, level: 1 })).toBeVisible();
    await page.waitForTimeout(500);
    expect((await api.get("HD Article", article.name)).views).toBe(1);
  });

  test("AR17 AR18 AR22 a vote can change, clear, and is rate limited", async ({ page, api }) => {
    const category = await createCategory(api);
    const article = await createArticle(api, category.name);
    const no = page.getByRole("button", { name: "No, it wasn't helpful" });
    const yes = page.getByRole("button", { name: "Yes, it was helpful" });
    const feedback = async () =>
      (await api.list("HD Article Feedback", { filters: { article: article.name, user: personas.customer.email }, fields: ["feedback"] }))[0]?.feedback;
    await page.goto(`/help/articles/${article.name}`);
    await no.click();
    await expect(no).toHaveAttribute("aria-pressed", "true");
    await expect.poll(feedback).toBe("2");
    await yes.click();
    await expect.poll(feedback).toBe("1");
    await yes.click();
    await expect(yes).toHaveAttribute("aria-pressed", "false");
    await expect.poll(feedback).toBe("0");
    await no.click();
    await yes.click();
    await expect(page.getByText("Thanks for your feedback!").first()).toBeVisible();
    // The sixth vote on one article within an hour is refused.
    await expect.poll(feedback).toBe("1");
    const refused = page.waitForResponse(
      (response) => response.url().includes("set_article_feedback") && /"value":\s*2/.test(response.request().postData() || "")
    );
    await no.click();
    expect((await refused).status()).toBe(429);
    await expect(page.locator("[data-sonner-toast][data-type=error]")).toBeVisible();
    expect(await feedback()).toBe("1");
  });

  test("AR14 below xl the inline On this page jumps to a heading", async ({ page, api }) => {
    await page.setViewportSize({ width: 1024, height: 800 });
    const category = await createCategory(api);
    const filler = "<p>" + "word ".repeat(400) + "</p>";
    const article = await createArticle(api, category.name, {
      content: `<h2>Alpha part</h2>${filler}<h3>Beta part</h3>${filler}<h2>Gamma part</h2>${filler}`,
    });
    await page.goto(`/help/articles/${article.name}`);
    await page.getByRole("button", { name: "On this page" }).click();
    await page.getByRole("button", { name: "Gamma part" }).click();
    await expect(page.getByRole("heading", { name: "Gamma part" })).toBeInViewport();
  });

  test("AR15 at xl a single heading still gets the side contents (finding 4)", async ({ page, api }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    const category = await createCategory(api);
    const article = await createArticle(api, category.name, { content: "<h2>Only part</h2><p>Body</p>" });
    await page.goto(`/help/articles/${article.name}`);
    await expect(page.getByRole("heading", { name: "Only part" })).toBeVisible();
    const toc = page.getByRole("navigation").filter({ hasText: "On this page" });
    await expect.soft(toc.getByRole("button", { name: "Only part" }), "finding 4: one heading still shows the xl TOC").toBeVisible();
  });

  test("AR25 AR27 related articles open and reset the article scroll", async ({ page, api }) => {
    const category = await createCategory(api);
    const filler = "<p>" + "word ".repeat(800) + "</p>";
    const created = [];
    for (let i = 0; i < 8; i++) created.push(await createArticle(api, category.name, { title: `Related ${i} ${uid()}`, content: filler }));
    await page.goto(`/help/articles/${created[0].name}`);
    const related = page.getByText("Related articles").locator("xpath=..");
    await expect(page.getByText("Related articles")).toBeVisible();
    const rows = page.locator('[data-component-id="container-gi1caqqm1"]').getByRole("link", { name: /^Related \d/ });
    await expect(rows).toHaveCount(6);
    const panel = page.locator('[data-component-id="container-gi1caqqm1"]');
    await panel.evaluate((el) => el.scrollTo({ top: el.scrollHeight }));
    const target = rows.first();
    const title = (await target.innerText()).split("\n")[0];
    await target.click();
    await expect(page.getByRole("heading", { name: title, level: 1 })).toBeVisible();
    await expect.poll(() => panel.evaluate((el) => el.scrollTop)).toBe(0);
    void related;
  });

  test.describe("phone", () => {
    test.use({ viewport: PHONE });

    test("AR13 the Article actions menu holds the copy actions", async ({ page, api }) => {
      const category = await createCategory(api);
      const article = await createArticle(api, category.name);
      await page.goto(`/help/articles/${article.name}`);
      await expect(page.getByText("Copy link")).toBeHidden();
      await page.getByRole("button", { name: "Article actions" }).click();
      for (const name of ["Copy for LLM", "Copy link", "View as Markdown"]) {
        await expect(page.getByRole("menuitem", { name })).toBeVisible();
      }
    });
  });
});

test.describe("article page, public knowledge base", () => {
  usePersona("customer");

  test("AR12 a public article offers Open in ChatGPT and Claude", async ({ page, api, kb, context }) => {
    await kb({ public_knowledge_base: 1 });
    const category = await createCategory(api);
    const article = await createArticle(api, category.name);
    await page.goto(`/help/articles/${article.name}`);
    await page.getByRole("button", { name: "More ways to use this article with an LLM" }).click();
    await expect(page.getByRole("menuitem", { name: "Open in ChatGPT" })).toBeVisible();
    const popup = context.waitForEvent("page");
    await page.getByRole("menuitem", { name: "Open in Claude" }).click();
    const claude = await popup;
    expect(decodeURIComponent(claude.url())).toContain(`get_article_markdown?name=${article.name}`);
    await claude.close();
  });
});

test.describe("knowledge base settings", () => {
  usePersona("admin");

  test("S30–S34 the Knowledge Base panel saves toggles, pins, banner and links", async ({ page, api, kb, context }) => {
    await kb({ allow_anonymous_article_voting: 0, banner_preset: "" });
    const category = await createCategory(api);
    await createArticle(api, category.name);
    const label = `E2E Link ${uid()}`;
    try {
      await page.goto("/help");
      await accountMenu(page).click();
      await page.getByRole("menuitem", { name: "Settings" }).click();
      const dialog = page.getByRole("dialog");
      await dialog.getByRole("tab", { name: "Knowledge Base", exact: true }).click();
      await expect(page).toHaveURL(/#settings\/knowledge-base$/);

      // Switches save as they flip, without the Save button.
      await dialog.getByText("Allow guests to vote on articles").locator("xpath=../..").getByRole("switch").click();
      await expect.poll(async () => (await api.get("HD Settings", "HD Settings")).allow_anonymous_article_voting).toBe(1);
      await expect(dialog.getByText("Unsaved")).toBeHidden();
      await dialog.getByRole("radio", { name: "Blue" }).click();
      await expect(dialog.getByText("Unsaved")).toBeVisible();
      await dialog.getByRole("button", { name: "Choose categories" }).click();
      await page.getByRole("combobox").last().fill(category.category_name);
      await page.getByRole("option", { name: new RegExp(category.category_name) }).click();
      await page.keyboard.press("Escape");
      await dialog.getByRole("button", { name: "Add link" }).click();
      await dialog.getByPlaceholder("Contact sales").fill(label);
      // S33: an unsafe address is refused on Save.
      await dialog.getByPlaceholder("https://example.com/contact").fill("javascript:alert(1)");
      await dialog.getByRole("button", { name: "Save" }).click();
      await expect(page.getByText(`${label}: use a web address`)).toBeVisible();
      await dialog.getByPlaceholder("https://example.com/contact").fill("https://example.com/e2e");

      // S34: Preview opens the portal with the draft.
      const popup = context.waitForEvent("page");
      await dialog.getByRole("button", { name: "Preview" }).click();
      const preview = await popup;
      await expect(preview).toHaveURL(/\/help\/?\?preview=1/);
      await expect(preview.getByRole("link", { name: label })).toBeVisible();
      await preview.close();

      await dialog.getByRole("button", { name: "Save" }).click();
      await expect(dialog.getByText("Unsaved")).toBeHidden();
      const settings = await api.get("HD Settings", "HD Settings");
      expect(settings.banner_preset).toBe("Blue");
      expect((await api.get("HD Article Category", category.name)).pinned).toBe(1);
      expect((await api.get("HD Form Script", QUICK_LINKS)).script).toContain(label);
    } finally {
      await api.update("HD Article Category", category.name, { pinned: 0, pinned_order: 0 });
      if (await api.exists("HD Form Script", { name: QUICK_LINKS })) await api.delete("HD Form Script", QUICK_LINKS);
    }
  });
});

