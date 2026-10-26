# KB category sections, category sidebar and search page: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the design handoff: the category page lists its own articles and then one section per subcategory, the sidebar lists categories only, and a new `/help/search` page replaces the sidebar title filter.

**Architecture:** Part A (Tasks 1–3) changes the category page on `feat/kb-subcategories`. Then `feat/kb-search-page` is rebased onto it. Part B (Tasks 4–7) adds paged search, the search page, and the category-only sidebar on `feat/kb-search-page`, because the sidebar and the search page ship together. One Vue row list (`PortalArticleList`) draws article rows on both pages.

**Tech Stack:** Frappe (Python, RediSearch via `helpdesk/search.py`), Studio portal (page JSON + setup `.ts`, Vue 3 custom components, frappe-ui 1.0.1 from `apps/frappe/studio/frontend/node_modules`), Playwright e2e.

**Spec:** `docs/superpowers/specs/2026-10-26-kb-category-and-search-handoff.md` (the handoff, binding for sizes and states). Search behaviour: `docs/superpowers/specs/2026-10-26-kb-search-page-design.md` on `feat/kb-search-page` (decisions 1–36; the handoff wins on any visual conflict).

## Global Constraints

- Repo `/Users/sydneygomes/studio-bench/apps/helpdesk`. Read `studio/AGENTS.md`, `studio/README.md`, `studio/KNOWLEDGE_BASE.md` and `apps/frappe/skills/studio-app-building/{SKILL,RULES}.md` before editing page JSON or a page script.
- Commit messages: conventional, scope `portal` or `kb`. **NEVER add Claude trailers: no `Co-Authored-By: Claude`, no `Claude-Session:`, no "Generated with Claude Code".**
- Never run tests against `studio.localhost`. Backend tests: `cd /Users/sydneygomes/studio-bench && bench --site e2e.localhost run-tests --app helpdesk --module <module> --skip-before-tests`.
- e2e: from `apps/helpdesk`, `BASE_URL=http://e2e.localhost:8020 npx playwright test <spec> -g "<name>"`. Before it, sync and build: `cd /Users/sydneygomes/studio-bench && bench --site e2e.localhost execute frappe.studio.sync.sync_studio_apps --args "['helpdesk']" && bench build-studio-app helpdesk --site e2e.localhost`. The :8020 server, worker and socketio already run; after a Python change ask the controller to restart serve and worker (do not start your own).
- Page JSON: write with `json.dumps(d, indent=1, ensure_ascii=False) + "\n"`, no `sort_keys`. Bump the page's `modified`.
- Guest endpoints: `@frappe.whitelist(allow_guest=True, methods=["GET"])  # nosemgrep`, call `validate_public_access()` first, filter with `make_article_filters()`, and add a test that a guest is refused while `public_knowledge_base` is off.
- Strings: `__()` in `.ts`/`.vue`, `{{ t('...') }}` in blocks, exactly the handoff's section 6 strings.
- Type ladder (handoff 2.5): 20 bold / 16 semibold / 14 medium / 13 regular. No other text sizes.
- Icons in Vue: `Icon` from frappe-ui with `lucide-<name>` strings, or `lucide-*` span classes as the file already does.

## Review Focus

1. A subcategory with more than 4 readable articles where a guest can read fewer than 4: the section shows only readable rows and the count matches `article_count` (Task 1 test).
2. Search with a `category` filter that names a parent: subcategory articles are included, and counts are computed before the filter (Task 4 test).
3. A paged search where hits from one article span pages: an article appears once across `start=0` and `start=20` (Task 4 test).
4. A reader opens `/search?q=ab` (2 characters) or `/search?category=<unknown>`: no request, no crash, the hint state shows / the unknown chip is dropped (Task 5 e2e).
5. The article page sidebar opens the article's category's parent and fills the category row, with no article list loaded (Task 6 e2e).

---

## Part A — branch `feat/kb-subcategories`

### Task 1: `get_subcategory_articles` API

**Files:**
- Modify: `helpdesk/api/knowledge_base.py` (next to `get_articles`, ~:194)
- Test: `helpdesk/tests/api/test_knowledge_base.py`

**Interfaces:**
- Produces: `get_subcategory_articles(category: str, limit: int = 4) -> dict[str, list[dict]]` — keys are the names of `category`'s Subcategories (`get_subcategories(category)`) that have at least one readable article; values are up to `min(cint(limit) or 4, 4)` rows `{name, title, excerpt}`, `published_on desc`, filtered with `make_article_filters(category=<sub>)`. Guest allowed, GET.

- [ ] **Step 1: Write the failing tests**
  - `test_subcategory_articles_are_newest_first_and_capped`: a parent with one Subcategory of 5 Public articles → `len(result[sub]) == 4`, names in `published_on desc` order, rows have `excerpt`.
  - `test_subcategory_articles_hide_unreadable_rows_from_guests`: Subcategory A has 1 Public + 1 Private, Subcategory B has only Private → as Guest, `result == {A: [<public row>]}`.
  - `test_subcategory_articles_skip_other_categories`: an article in the parent itself is not in any value.
  - Add `get_subcategory_articles` to the guest-refused list near :84–95 (`(get_subcategory_articles, (<category>,))`).
- [ ] **Step 2: Run, expect FAIL** (`ImportError`). `--module helpdesk.tests.api.test_knowledge_base`
- [ ] **Step 3: Implement** with one `frappe.get_all` per Subcategory (Subcategories are few).
- [ ] **Step 4: Run the module, expect all OK.**
- [ ] **Step 5: Commit** `feat(kb): give the first articles of each subcategory`

### Task 2: one article row list, chevrons, header icon and subcategory count

**Files:**
- Create: `studio/helpdesk/components/knowledge_base/PortalArticleList.vue`
- Modify: `studio/helpdesk/studio_page/category/category.json`, `category.ts`
- Modify: `studio/helpdesk/components/ui/PortalBreadcrumbs.vue` (link hover `text-ink-gray-7`, last crumb `text-ink-gray-8`)

**Interfaces:**
- Produces: `PortalArticleList.vue` props `{ articles: { name: string; title: string; title_slug?: string; excerpt?: string; meta?: string }[]; marked?: boolean }`. Renders a `div` of rows exactly as handoff 3.3: each row a `PortalLink` to `ROUTES.article(article)` with today's `article-row` classes from `category.json` (`group flex cursor-pointer items-center gap-4 py-4 -mx-2.5 px-2.5 rounded-4 transition-colors hover:bg-surface-gray-1 relative after:absolute after:inset-x-2.5 after:bottom-0 after:h-px after:bg-[--outline-gray-1] last:after:hidden hover:after:opacity-0 [&:has(+*:hover)]:after:opacity-0 focus-visible:focus-ring`), `mouseenter` → `prefetchOnHover(article.name)`. Title line: title `text-base font-medium text-ink-gray-8 group-hover:text-ink-gray-9 truncate max-sm:whitespace-normal max-sm:line-clamp-2`, plus, when `meta` is set, a `text-sm text-ink-gray-5 shrink-0 truncate max-w-[50%]` span with `gap-3` (handoff 5.3). Excerpt `text-p-sm text-ink-gray-5 truncate max-sm:whitespace-normal max-sm:line-clamp-2`, `gap-0.5` below. Trailing `lucide-chevron-right size-4 shrink-0 text-ink-gray-4 group-hover:text-ink-gray-6`, `aria-hidden`. With `marked`, title and excerpt render with `v-html` (the API already escapes all but `<mark>`) and `[&_mark]:rounded-sm [&_mark]:bg-surface-amber-2 [&_mark]:px-0.5 [&_mark]:text-ink-gray-9`; otherwise text interpolation.
- Produces (category.ts): `subcategoryCount: string` (`countLabel(n, __('1 subcategory'), __('{0} subcategories'))`, n = `subcategories.length`), `categoryIcon: string` (`category.icon || 'lucide-folder'`).

- [ ] **Step 1:** Replace the `Repeater-m7atz02fl` row Repeater in `category.json` with one `PortalArticleList` block (`isCustomVueComponent`, `articles: "{{ articles.data || [] }}"`, same visibility). Delete the `articles-heading` ("Articles" label) block.
- [ ] **Step 2:** Header: wrap the h1 `TextBlock` in a container `flex items-start gap-2.5` with an `Icon` block first (`icon: "{{ categoryIcon }}"`, classes `size-5 shrink-0 text-ink-gray-6 mt-[3.5px]`). After `category-article-count` add a `·` TextBlock (`text-ink-gray-3`) and a `{{ subcategoryCount }}` TextBlock (`text-sm text-ink-gray-5`), both visible only when `subcategories.length`.
- [ ] **Step 3:** Update `e2e/tests/knowledge-base/portal-walkthrough.spec.ts` D32: drop the "Articles" heading assertions; assert the header shows "1 subcategory".
- [ ] **Step 4:** Sync, build, run D32 and `-g "CT2"`: expect PASS (CT2 still passes on rows).
- [ ] **Step 5: Commit** `feat(portal): draw category rows with a chevron and show the category icon`

### Task 3: subcategory sections replace the cards

**Files:**
- Create: `studio/helpdesk/components/knowledge_base/PortalSubcategorySection.vue`
- Modify: `studio/helpdesk/studio_page/category/category.json`, `category.ts`
- Test: `e2e/tests/knowledge-base/portal-walkthrough.spec.ts` (D32)

**Interfaces:**
- Consumes: Task 1 `get_subcategory_articles`; Task 2 `PortalArticleList`.
- Produces: `PortalSubcategorySection.vue` props `{ category: { name: string; category_name: string; icon?: string | null; article_count: number }; articles: Row[] }` → `<section>` with the h2 head of handoff 3.4 (icon, name `PortalLink` to `ROUTES.category(name)`, count, "View all" ghost Button only when `article_count > 4` with `:route` or a `PortalLink` wrapper and `aria-label` `__('View all {0} articles in {1}', [count, name])`), then `gap-1` and `PortalArticleList` of `articles.slice(0, 4)`.
- Produces (category.ts): `sections` = `subcategories` (sidebar order) that have rows in `subcategoryArticles.data`, each `{ category, articles }`.

- [ ] **Step 1:** Add a page resource `subcategoryArticles` (API Resource, GET, `helpdesk.api.knowledge_base.get_subcategory_articles`, params `{"category": "{{ route.params.category }}"}`, auto).
- [ ] **Step 2:** Restructure the body: one container `flex flex-col gap-8 mt-6 w-full` holding (a) the skeleton (visible until `articles.data`, `sidebar.data` and `subcategoryArticles.data` all exist), (b) the own `PortalArticleList` (visible when it has rows), (c) a Repeater over `sections` (classes `w-full !flex-col !flex-nowrap !gap-8`) with one `PortalSubcategorySection` child (`category: "{{ dataItem.category }}"`, `articles: "{{ dataItem.articles }}"`), (d) the empty state (no own rows and no sections). Delete `category-subcategories` (heading + `category_grid-subcategories`). Remove `subcategories` from the empty-state condition only if `sections` replaces it.
- [ ] **Step 3:** D32: assert a level-2 heading `visible.category_name` holds a link to the subcategory and the subcategory's article title; the hidden subcategory has no heading. Add a 5-article subcategory and assert the "View all 5 articles in …" link exists and opens the subcategory page; a 1-article subcategory has none.
- [ ] **Step 4:** Sync, build, run D32 and CT2: PASS.
- [ ] **Step 5: Commit** `feat(portal): list each subcategory's articles in its own section`

**Then (controller):** `git rebase feat/kb-subcategories feat/kb-search-page`, check out `feat/kb-search-page`.

---

## Part B — branch `feat/kb-search-page`

### Task 4: paged search with category counts

**Files:**
- Modify: `helpdesk/api/article.py` (`search`, `search_with_enough_results`, `search_accessible_articles`, `search_titles`), `helpdesk/search.py` (`search()` passes `page_length`), `helpdesk/api/knowledge_base.py` (`search_articles`)
- Test: `helpdesk/tests/api/test_article.py`, `helpdesk/tests/api/test_knowledge_base.py`

**Interfaces:**
- Produces: `helpdesk.search.search(query, qtype="and", limit=NUM_RESULTS)`; `article.search(query, limit=NUM_RESULTS)`; `search_accessible_articles(query, limit=NUM_RESULTS)`; `search_titles(words, limit=NUM_RESULTS)`. Defaults keep today's behaviour exactly.
- Produces: `search_articles(query, limit=SEARCH_LIMIT, category=None, start=None, page_length=None)`. `MAX_PAGE_HITS = 200`, `PAGE_LENGTH_LIMIT = 50`. When `start` and `category` are both None → today's list response. Otherwise → `{"results": [...hit rows as today...], "total": int, "categories": {name: count}}` per spec decision 28: search up to 200 section hits (fallbacks as now, triggered when fewer than `NUM_RESULTS` articles), dedupe, access-filter, count per category with each parent also counting its Subcategories' articles, then filter by `category` (a name, a list, or a JSON list string; each name expanded to itself + `get_subcategories(name)`), then slice `[start : start + min(cint(page_length) or SEARCH_LIMIT, 50)]`. Load the hit rows' fields only for the slice.

- [ ] **Step 1: Failing tests** (mock `hd_search` the way `test_article.py` already does):
  - `test_search_passes_the_hit_limit` (article.search with `limit=200` calls `hd_search` with that page length).
  - `test_paged_search_counts_before_the_filter_and_expands_parents`: parent P with sub S; hits in P, S and another top-level C → `categories == {P: 2, S: 1, C: 1}`; `category=P` → results are the P and S articles, `total == 2`.
  - `test_paged_search_slices_articles_not_hits`: 25 articles, several sections each → `start=0,page_length=20` gives 20, `start=20` gives 5, no name in both.
  - `test_paged_search_caps_page_length_at_50`.
  - `test_unpaged_search_keeps_the_list_response` (existing tests stay green).
  - Guest: a Private article's category never appears in `categories`.
- [ ] **Step 2:** Run `--module helpdesk.tests.api.test_article` and `...test_knowledge_base`: FAIL.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Both modules OK.
- [ ] **Step 5: Commit** `feat(kb): page article search and count matches per category`

### Task 5: search page

**Files:**
- Create: `studio/helpdesk/studio_page/search/search.json`, `search.ts`
- Create: `studio/helpdesk/components/knowledge_base/PortalSearchResults.vue`
- Modify: `studio/helpdesk/composables/useArticleSearch.ts` (add `usePagedArticleSearch`), `shared/src/portalRoutes.ts` (`search`), `studio/helpdesk/components/knowledge_base/PortalArticleSearch.vue` ("See all results")
- Test: `e2e/tests/knowledge-base/portal-search.spec.ts` (new)

**Interfaces:**
- Consumes: Task 4 paged `search_articles`; `PortalArticleList` (`marked`, `meta`); `useRecent`; `PortalBreadcrumbs`; `useKnowledgeBase().sidebar` (labels: `row.label`).
- Produces: `ROUTES.search = (query?: { q?: string; category?: string | string[] }) => ({ path: '/search', query: <empty values dropped> })`.
- Produces: `usePagedArticleSearch(query: Ref<string>, categories: Ref<string[]>)` → `{ rows, total, counts, hasMore, loadMore(), isCurrent, isLoading }`; debounced like `useArticleSearch` (same abort/settle rule), `page_length` 20, new query or filter resets rows, `loadMore` appends with `start = rows.length`; nothing fetched below `MIN_QUERY_LENGTH`.
- `search` page: route `/search`, `allow_guest: 1`, `page_title` "Search", unique `page_name`, `tab_title` `{{ tabTitle }}` ("Search" or "{q} – Search"); blocks copied from `category.json`'s frame (header, `PortalSectionBar` labelled "Search", page-wrapper, `PortalArticleSidebar` with `showSearch: false`, main-layout grid, column, `kb_settings`). The column holds `PortalBreadcrumbs` (Help › Search) and `PortalSearchResults`.
- `PortalSearchResults.vue` owns everything in handoff 5.1–5.5: reads `q`/`category` from `useRoute().query` on mount, writes them back with `router.replace`, sticky block, `TextInput size="lg"` autofocused, clear button, `/` focuses it (`useKeyboardShortcut`), toolbar (MultiSelect `hide-search` with `#trigger` and `#item-suffix`, options from `counts` labelled with sidebar `label`, chips, total), results with meta `{label} · {n} min read` (`__('{0} min read')`), `opacity-50` while not current, Load more, Recently viewed, empty hint, no-results state with "Raise a ticket" (`ROUTES.newTicket({ from: 'search', q })`). Unknown `category` names (not in `counts`) are dropped from the chips but kept out of the request only after the first answer.
- Home dropdown: when results exist, the footer starts with a `See all results` link to `ROUTES.search({ q })`; the key hints follow.

- [ ] **Step 1: Write e2e** `portal-search.spec.ts` (customer persona): type a query → URL has `q`, rows show `<mark>`; reload keeps results; Category filter lists only categories with results and selecting a parent keeps a subcategory article; chip removal; 25 matching articles → 20 rows, Load more → 25, button gone; `/search?q=zzzz-none` → "Raise a ticket" opens new ticket with `q`; `/search` with no history → "Type to search articles"; home dropdown "See all results" opens `/search?q=`.
- [ ] **Step 2:** Implement route, composable, component, page; sync, build.
- [ ] **Step 3:** Run the spec: PASS. Run `-g "CT1"` (home search) and the new-ticket suggestions spec: PASS.
- [ ] **Step 4: Commit** `feat(portal): add the knowledge base search page`

### Task 6: category-only sidebar

**Files:**
- Modify: `studio/helpdesk/components/knowledge_base/PortalArticleSidebar.vue`, `studio/helpdesk/stores/knowledgeBase.ts` (`sidebarState`: drop `query`, `openSubName`, `shown`), `studio_page/{category,article,categories}/*.json` (props)
- Test: `e2e/tests/knowledge-base/portal-walkthrough.spec.ts` (CT2–CT5, AR26)

**Interfaces:**
- Consumes: `ROUTES.search`.
- Produces: `PortalArticleSidebar` props `{ categories, activeCategory?: string, open, loading, showSearch?: boolean (default true), searchShortcut?: boolean (default true) }`; `activeName` removed. Article page passes `activeCategory: "{{ article.data.category }}"`. Rows per handoff section 4: top-level `SidebarItem` with `:route="ROUTES.category(name)"`, icon, no chevron; the open parent's child group `ml-4 border-l border-outline-gray-2 pl-[7px] mt-0.5 mb-1.5 flex flex-col gap-0.5`, child rows without icon; current row `bg-surface-gray-2 shadow-none text-ink-gray-8`; open parent `text-ink-gray-8` no fill. Search link: `PortalLink`/`RouterLink` styled as the outline input with a `ShortcutKey` "/", to `ROUTES.search(activeCategory ? { category: activeCategory } : undefined)`; `/` pushes the same route when `searchShortcut`. Phone: `h-11`, icons `size-[18px]`, labels `text-[15px]`. Keep the scroll restore and current-row scroll-into-view. Remove `PortalCollapse`, `createReusableTemplate`, `splitMatch`, show-more, and the "No articles match" line.

- [ ] **Step 1:** Rewrite CT2–CT5 in the walkthrough: the category page sidebar fills the current category; a subcategory page shows its siblings under the open parent and only that parent's children; other parents show no children; the sidebar search link on a category page opens `/help/search?category=<name>` and `/` does the same; on `/help/search` the sidebar has no search link. AR26: on an article page the article's category row is filled (`aria-current` or `data-current`).
- [ ] **Step 2:** Implement; sync, build.
- [ ] **Step 3:** Run the whole `e2e/tests/knowledge-base/` folder: PASS.
- [ ] **Step 4: Commit** `feat(portal): navigate categories in the knowledge base sidebar`

### Task 7: handoff check at three widths (controller)

- [ ] Playwright script from `apps/helpdesk` at 1440, 768 and 375 on `/help/category/<Demo Billing>`, a subcategory page and `/help/search?q=invoice&category=<Demo Billing>`: measure the handoff section 7 values (left edge, right edge, heights 37 / 72.4 / 40 / 28, gaps 24 / 32 / 12) with `getBoundingClientRect`, save screenshots to the scratchpad, fix any miss in the owning task's files, commit `fix(portal): …`.
- [ ] Backend modules `test_knowledge_base`, `test_article`, `hd_article_category` and the KB e2e folder: all PASS.
