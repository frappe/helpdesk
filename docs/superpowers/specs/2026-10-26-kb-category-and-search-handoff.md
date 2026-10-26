# Design handoff: KB category page with subcategories + search page

Design (Sketch v3): https://sketch.netchamp.dev/u/aerodeval/kb-category-subcategories
- Category page: `#/categories/billing` (parent) and `#/categories/invoices` (subcategory)
- Search page: `#/search`, or click the sidebar search box on a category page

Baseline: `develop` (`github-upstream/develop` @ `4f41f4c21`).
Values come from the live portal on `e2e.localhost:8020` (Chrome, light theme) and from frappe-ui. **This spec overrides the prototype's sizes.**
Widths are not specified: keep develop's page grid, column, sidebar width and gutters as they are. Alignment is described by what lines up with what.

---

## 1. Summary of changes from develop

| Area | develop | Target |
|---|---|---|
| Data | No subcategories | Build on `feat/kb-subcategories`: it adds `parent_article_category`, branch counts, `label` and the sidebar fields. |
| Category header | h1, description, byline + "N articles" | + breadcrumbs · + category icon before the h1 · + "· N subcategories" |
| Category body | One list of articles | The category's own articles first (no label) → one section for each subcategory |
| Article rows | `PortalArticleIcon` at the end of the row | Chevron at the end of the row (category page and search page) |
| Sidebar | Category → article titles (expandable). The search box filters titles. | Categories only. The open parent shows its subcategories. The search box is a link to the search page. |
| Search | Home dropdown only (5 results) | New page `/help/search` (spec: branch `feat/kb-search-page`, `docs/superpowers/specs/2026-10-26-kb-search-page-design.md`) |

Change these on `feat/kb-subcategories`:
- `b84dba432`: cards. **Replace with sections.**
- `a5311a41b`: "Articles" label. **Remove it.**
- The sidebar nests articles and subcategories with folder icons and chevrons. **Replace it with the tree in section 4.**

**Ship order:** the sidebar change and the search page ship together. The new sidebar has no title filter, so it needs the search page.

---

## 2. Alignment rules (both pages)

1. **One left text edge.** Breadcrumbs, the h1 icon, description, byline, section-head icons, the search box, the filter row, row titles and excerpts all start on the column's left edge.
2. **Rules use the content width exactly.** Section-head borders and row dividers run from the left text edge to the column's right edge. Rows bleed `10px` each side only for the hover fill (`-mx-2.5 px-2.5`). Dividers are inset back by the same amount (`after:inset-x-2.5`).
3. **One trailing icon column.** Row chevrons, the section head's "View all" arrow, the search box's clear X and the result count all end on the column's right edge. The ghost "View all" button pulls its padding out with `-me-2`, so the arrow sits flush.
4. **One centre line for each inline row.** Heads and toolbars use `items-center` in a fixed-height box, so items with and without a button line up and keep the same height.
5. **One type ladder:** 20 bold (h1) → 16 semibold (section name, search input) → 14 medium (row title) → 13 regular (meta, labels, counts, excerpt). No other sizes.

---

## 3. Category page

### 3.1 Header

Items stack with `gap-3` (12).

| Element | Height | Spec |
|---|---|---|
| **Breadcrumbs (new)** | 17.5 | `PortalBreadcrumbs` (on the branch). `text-sm` 13/17.55, `gap-x-1`. Earlier crumbs are links in `ink-gray-5` (hover `ink-gray-7`), the last crumb is `ink-gray-8`. Top level: `Help › Billing`. Subcategory: `Help › Billing › Invoices`. |
| h1 row | 27 | **New:** category `icon` 20×20, `ink-gray-6`, `shrink-0`, vertically centred on the h1 line (top offset 3.5). Fall back to `lucide-folder`. Then `gap-2.5` (10), then the h1: `text-3xl` 20/27, `font-bold`, `ink-gray-8`. A long h1 wraps under its own first letter, not under the icon. |
| Description | 21 | no change: `text-p-base` 14/21, `ink-gray-6` |
| Byline | 24 | no change: avatars 24 (overlap −6, 2px `surface-base` ring), text `text-sm` `ink-gray-5`. **New:** after the article count, `· 3 subcategories`, using the byline's existing dot (`text-ink-gray-3`). Singular is "1 subcategory". Hide it when there are none. |

Header total: 125.5. Spacing above the header: develop's scroll padding (`pt-6` / `sm:pt-10`).

### 3.2 Body rhythm

| Block | Spacing above | Height |
|---|---|---|
| The category's own articles | `mt-6` (24) after the header | rows only, no label |
| Each subcategory section | `mt-8` (32) after the previous block | head 37 + `gap-1` (4) + rows |

- No own articles → hide that block. The first section takes `mt-6` (24).
- No own articles and no subcategories → develop's empty state "No articles in this category" (`py-16`).

Worked example, measured from the top of the header (2 own articles, then subcategories with 5, 3 and 2 articles):
own rows 149.5–294.3 → Section 1 at 326.3 (head to 363.3, rows 367.3–656.9) → Section 2 at 688.9 (rows 729.9–947.1) → Section 3 at 979.1 (rows 1020.1–1164.9).

### 3.3 Article row (one row, used on both pages)

| Part | Spec |
|---|---|
| Row | `flex items-center gap-4 py-4 -mx-2.5 px-2.5 rounded-4`. **Height 72.4** = 16 + 18.9 + 2 + 19.5 + 16. Hover `bg-surface-gray-1`, radius 8. |
| Title | `text-base font-medium` 14/18.9, `ink-gray-8` (hover `ink-gray-9`), `truncate`. Below 640: 2-line clamp. |
| Excerpt | `text-p-sm` 13/19.5, `ink-gray-5`, 2px below the title (`gap-0.5`), `truncate`. Below 640: 2-line clamp. |
| Chevron | `lucide-chevron-right` 16, `ink-gray-4` (hover `ink-gray-6`), `shrink-0`, `aria-hidden`. Vertically centred (top offset 28.2), on the trailing icon column. It replaces `PortalArticleIcon`. |
| Divider | 1px `--outline-gray-1` under every row except the last. Hidden on the hovered row and on the row above it (develop's classes). |

### 3.4 Subcategory section head (new)

```
▣  Invoices  5 ································ View all →     28px box, items-center
───────────────────────────────────────────────────────────    pb-2 (8) + 1px border = 37
```

| Part | Spec |
|---|---|
| Container | `h2`. `flex items-center gap-2 h-7 box-content pb-2 border-b border-outline-gray-1`. **37px total, for every head.** |
| Icon | subcategory `icon` (fallback `lucide-folder`), 16, `ink-gray-6`, `shrink-0`, `aria-hidden`. On the left text edge, top offset 6. |
| Name | link to the subcategory page. `text-lg font-semibold` 16/21.6, `ink-gray-8`, `truncate min-w-0`. 8px after the icon. Hover `ink-gray-9`, no underline. `focus-visible:focus-ring`, radius 4. |
| Count | `article_count`, `text-sm` 13/17.55, `ink-gray-5`, `tabular-nums`, `shrink-0`, 8px after the name. |
| View all | only when `article_count > 4`. `Button variant="ghost" size="sm"` (height 28, padding 0 8, radius 8, label 14/18.9), label "View all", `iconRight="lucide-arrow-right"` 16, `ms-auto -me-2 shrink-0`. `aria-label="View all {n} articles in {name}"`. |
| Rows | the first 4 (`sub.articles.slice(0, 4)`), newest first. |

Order: the `sidebar.data` order (`category_name` ascending).

**Data gap:** `sidebar.data[].articles` has no `excerpt`. A row without an excerpt is 50.9, not 72.4, and breaks the rhythm. The backend must give each subcategory's first 4 articles with `excerpt`, using `get_articles`' filters. Do not add excerpts to `get_kb_sidebar`.

### 3.5 States

| State | Behaviour |
|---|---|
| Loading | develop's `category-rows` skeleton (8 rows) until `articles` and `sidebar` are both loaded |
| Subcategories only | No own list. The sections start at `mt-6`. |
| Subcategory with 0 readable articles | Not in `sidebar.data`, so no section and no sidebar row |
| Subcategory page | Same page. No sections, because a subcategory has no children. |
| Not found | develop's empty state, no change |

---

## 4. Sidebar (both pages)

The sidebar navigates **categories**. The page lists the articles.

```
[ Search articles            / ]   ← link styled as the search box
[ ▣  Getting started           ]
[ ▣  Billing                   ]   ← open parent: icon + label ink-gray-8, no fill
  │ [Invoices                  ]   ← current: bg-surface-gray-2, ink-gray-8
  │ [Payment methods           ]
  │ [Refunds                   ]
[ ▣  Account & security        ]
```

| Part | Spec |
|---|---|
| Search box | A **link** (`RouterLink`) styled like develop's `TextInput size="sm" variant="outline"`: height 28, radius 8, `border-outline-gray-2` (hover `outline-gray-3`), search icon 16 `ink-gray-4`, placeholder "Search articles" `ink-gray-4`, and a `/` key hint (`kbd`, `text-2xs`, `border-outline-gray-2`, radius 4) at the end. On a category page it goes to `/search?category=<current>`, elsewhere to `/search`. `/` does the same, and on the search page it focuses the page box. **Hidden on the search page.** Same top and bottom spacing as develop. |
| Top-level row | `SidebarItem` with a route (link). Height 28, radius 8, `pl-2` (8), rows 2px apart (`gap-0.5`). Icon 16, label `text-sm` 13 after an 8px gap, `truncate`. **No chevron.** |
| Child group | Only under the **open parent**: the current category, or the parent of the current subcategory or of the current article's category. `ml-4` (16) + 1px `border-l border-outline-gray-2` + `pl-[7px]`, `mt-0.5` (2), `mb-1.5` (6), `gap-0.5`. **The guide line runs through the centre of the parent's icon.** |
| Subcategory row | Same row, **no icon**. The label starts **exactly under the parent's label**: the 1px line + 7px + the row's 8px padding equal the parent's icon half-width plus its gap. The guide line and the fill start show the nesting. |
| Right edge | Every row and fill at every level ends on the same right edge. No `pr-1` on the child group. |
| Current | Current category row (on a category page, or the category of the article being read): `bg-surface-gray-2`, no shadow, label and icon `ink-gray-8`. Open parent of a current subcategory: icon and label `ink-gray-8`, no fill. Other rows: `ink-gray-6`, hover `bg-surface-gray-1`. |
| Phone | Bottom sheet: rows `h-11` (44), icons 18, labels 15, the same indent rules |

Removed: article lists under categories, expand and collapse chevrons, folder icons on subcategories, "show more", `PortalCollapse` in the sidebar, and the title filter.

---

## 5. Search page (new)

Behaviour follows the spec on `feat/kb-search-page` (decision numbers in brackets). Route `/search`. Same layout as the category page: sidebar plus content column, with develop's grid and scroll padding.

### 5.1 Top of the page

```
Help › Search                                          ← breadcrumbs
┌────────────────────────────────────────────────┐
│ 🔍  invoice                                  ✕ │     ← sticky box, 40
└────────────────────────────────────────────────┘
[≡ Category · 1]  [Billing ✕]               5 articles   ← toolbar, 28
```

| Element | Height | Spacing above | Spec |
|---|---|---|---|
| Breadcrumbs | 17.5 | scroll padding | `PortalBreadcrumbs`: `Help › Search` [3]. Not sticky. |
| Sticky block | — | `gap-3` (12) | `sticky top-0 z-10 bg-surface-base`, `pt-3 pb-3` (12/12), so it has 12px of air when stuck. It holds the box and the toolbar. |
| Search box | **40** | 0 | `TextInput size="lg" variant="outline"`: height 40, `text-lg` 16, radius 10. Prefix: search icon 16 `ink-gray-4`. Suffix: when there is text, a clear button `Button variant="ghost" size="xs" icon="lucide-x"` with `aria-label="Clear search"` [8]. Focused when the page opens [6]. `aria-label="Search articles"`. Search runs as the reader types (existing debounce, minimum 3 characters) [7]. |
| Toolbar | **28** | `mt-3` (12) | Only when the query has 3 or more characters [13]. `flex flex-wrap items-center gap-2`: the filter button, then the chips, then the count with `ms-auto`. When it wraps, rows are 8px apart (`gap-2`). |

### 5.2 Toolbar parts

| Part | Spec |
|---|---|
| Category filter | `MultiSelect hide-search` with a `#trigger`: `Button size="sm"` (28), `iconLeft="lucide-list-filter"`. Label "Category", or "Category · N" when N are selected [10]. Options: categories and subcategories that have results, labelled "Billing › Invoices" [11]. `#item-suffix`: count, `text-sm tabular-nums ink-gray-5`. A parent's count includes its subcategories, because selecting it includes them [12]. |
| Chip | One for each selected category: `Button size="sm" variant="subtle"` (28), label = category label, `iconRight="lucide-x"`, `aria-label="Remove filter {label}"`. A click removes it [14]. |
| Result count | `text-sm` 13, `ink-gray-5`, "1 article" / "{0} articles", `ms-auto`. It is the total match count, not the number loaded [17]. |

### 5.3 Results

| Part | Spec |
|---|---|
| List | `gap-1` (4) after the sticky block. **The same article row as 3.3** [15]: 72.4 tall, chevron, dividers. |
| Title line | title (flexible, `truncate`) + meta on the same line: `{Category › Subcategory} · {n} min read`, `text-sm` 13, `ink-gray-5`, `shrink-0 truncate max-w-[50%]`, `gap-3` (12) from the title [16]. The meta never takes more than half the line, so the title always shows. |
| Highlight | Matches in the title and excerpt: `<mark class="rounded-sm bg-surface-amber-2 px-0.5 text-ink-gray-9">` (develop's sidebar highlight style) [16]. |
| Load more | When more results exist: centred `Button` (default variant, size md, 32), `mt-4` (16) below the list [18]. Loads 20 more. |
| Updating | While a new query loads, the old rows stay and fade to `opacity-50` (`transition-opacity`). The new rows replace them [19]. |

### 5.4 States

| State | Spec |
|---|---|
| No query, has history | "Recently viewed" [21]: label `h2 text-sm ink-gray-5 pb-2 border-b border-outline-gray-1` (17.5 + 8 + 1), `mt-3` (12) after the box, then the same rows (with meta, no highlight). |
| No query, no history | Empty state, `py-16`: search icon in a 48px circle (`bg-surface-gray-2`, icon 24 `ink-gray-5`), "Type to search articles" `text-base ink-gray-7`, "Use at least 3 characters." `text-sm ink-gray-5`, items `gap-3` (12) [21]. |
| No results | `PortalArticleSearch`'s existing empty state: "No articles match “{0}”" + `Raise a ticket` (solid gray, `mt-2`). The ticket gets origin `{ from: "search", q }` [20]. |
| URL | `?q=&category=` read on load. Typing and filters update it with `router.replace` [4]. |
| Page title | "Search", or "{q} – Search" [5] |

### 5.5 Phone (<640)

- The sticky block stays. The toolbar wraps, and the count drops to its own line on the right.
- Rows: title and excerpt clamp to 2 lines. The meta stays on the title line, capped at half the line.
- The entry point is the sidebar sheet's search link.

---

## 6. Strings

`__()`/`t()`: "View all", "View all {0} articles in {1}", "1 subcategory", "{0} subcategories", "Search", "Search articles", "Clear search", "Category", "Category · {0}", "Remove filter {0}", "1 article", "{0} articles", "{0} min read", "Load more", "Recently viewed", "Type to search articles", "Use at least 3 characters.", "No articles match “{0}”", "Raise a ticket".

## 7. Check before done (at 1440, 768 and 375 on `e2e.localhost`, with Playwright from `apps/helpdesk`)

- Left edge: crumbs, h1 icon, description, section icons, search box, toolbar and row titles share one edge.
- Right edge: row chevrons, the "View all" arrow, the clear X and the result count share one edge. Every border and divider spans exactly the content width.
- Heights: section heads 37, rows 72.4, search box 40, toolbar items 28. Gaps: 24 after the header, 32 between blocks, 12 inside the sticky block.
- Sidebar: only the open parent shows its subcategories, the subcategory labels sit under the parent label, every fill ends on the same edge, and the current category is filled. The search link opens `/search?category=<current>` on a category page.
- Search: `/` opens and focuses search, the URL keeps `q` and `category`, Load more adds 20, old rows dim while loading, and there is no search box in the sidebar on `/search`.
