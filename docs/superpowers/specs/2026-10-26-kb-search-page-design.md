# Knowledge base search page: design

Settled with the user on 2026-10-26. Builds on `2026-10-25-kb-subcategories-design.md`. Terms are defined in `CONTEXT.md`.

## Problem

The portal has no page for search results. The home search box shows at most 5 articles in a dropdown. The sidebar search box only filters the article titles already in the sidebar. A reader cannot see every match, and cannot search inside one Category.

## Decisions

### Page

1. A new Studio page `search` at route `/search`. The full URL is `/help/search`.
2. The page uses the same layout as the category and article pages: `PortalArticleSidebar` on the left, results on the right.
3. Breadcrumbs read Help › Search.
4. The URL holds the state: `?q=<query>&category=<name>`. The page reads both on load. Typing and filter changes update the URL with `router.replace`, so a search result link can be shared and Back leaves the page.
5. The page title is "Search". With a query, it is "<query> – Search".

### Search box

6. A sticky text input at the top of the results column. It gets focus when the page opens.
7. Search runs as the reader types, with the existing debounce. Enter is not needed. The minimum query length stays `MIN_QUERY_LENGTH` (3).
8. A clear button (X) shows when the box has text. It empties the query and the URL `q`.
9. The `/` shortcut focuses the box.

### Category filter

10. One filter: Category. It is a MultiSelect, with an article count next to each option.
11. The options list Categories and Subcategories that have at least one result for the query. Subcategories read "Category › Subcategory".
12. Selecting a Category also matches the articles of its Subcategories.
13. With no query, the filter is hidden.
14. "Search inside a Category": on a category page, the sidebar search opens `/search?category=<that category>`. The filter starts with that Category selected, so it shows as a removable chip.

### Results

15. Each result row has the same look and height as an article row on the category page.
16. A row shows the highlighted title, the category label ("Category › Subcategory"), the highlighted excerpt and the reading time.
17. Above the list, a summary reads "1 article" or "{0} articles". The number is the total match count, not the count loaded so far.
18. Results load 20 at a time. A "Load more" button under the list adds the next 20. The button shows while more results exist.
19. While a new query loads, the old rows stay visible and dim. The new rows replace them.
20. With no results, the page shows the existing empty state from `PortalArticleSearch`: "No articles match “{0}”" and a "Raise a ticket" button. The ticket gets origin `{ from: "search", q }`.
21. With no query, the page shows "Recently viewed" from `useRecent`, the same list as the home dropdown. With no history, it shows a short hint: "Type to search articles".

### Entry points

22. Sidebar: the search box becomes a button that looks like a search box. Click, or `/`, opens `/search`. On a category page it adds `category` (decision 14).
23. On the search page, the sidebar has no search box. The page box replaces it.
24. The sidebar loses its title filter. The search page replaces it.
25. Home dropdown: no change, except a footer row "See all results" when the query has results. It opens `/search?q=<query>`. Enter on a highlighted row still opens that article.

### Backend

26. `search_articles` gets three optional parameters: `category`, `start` (default 0) and `page_length` (default `SEARCH_LIMIT`). Without them, it answers as it does now, so the home dropdown and the new-ticket suggestions do not change.
27. It still allows guests, keeps its rate limit, and returns only articles the reader can read.
28. Paging works on the final article list, not on RediSearch hits. One article has many section hits, and some hits get dropped by the access check, so a RediSearch offset does not map to an article offset. Each call does this:
    1. Search RediSearch for up to `MAX_PAGE_HITS` (200) section hits.
    2. Remove duplicate articles. The first hit for an article wins.
    3. Remove articles the reader cannot read.
    4. Count the articles per Category for the filter.
    5. Apply the `category` filter, with each Category expanded to its Subcategories.
    6. Return the slice `[start, start + page_length]`.
29. The response for a call with `start` or `category` is `{results, total, categories}`. `categories` maps each Category name to its article count, counted before the `category` filter. A call without these parameters keeps the list response.
30. `page_length` is at most 50.
31. The fallback searches (noun phrases, then OR) run the same way as now: only when the first search returns too few articles.
32. "Load more" calls the API again with the next `start`. The search runs again on each call. This is acceptable because RediSearch is fast and the results are capped at 200 hits.
33. A query with more than 200 section hits shows at most the articles in those 200 hits. The summary count is then the count of those articles.

### Out of scope

34. Tags. Articles have no tags, and the editor has no way to add them. Tags need an editor field, indexing, and a public or internal flag, so customers do not see internal tags. This is a separate feature.
35. Author and date filters, a spelling-corrected query, a results cache in local storage, and a feedback button. Gameplan has these. Add them only when readers ask for them.
36. Moving article search to the SQLite index that ticket search uses.

## Acceptance criteria

- [ ] Clicking the sidebar search box opens `/search` with the box focused.
- [ ] Typing a query shows results with highlighted titles and excerpts, and the URL holds `q`.
- [ ] Reloading `/search?q=refund` shows the same results.
- [ ] "Load more" adds the next 20 results and goes away when none are left.
- [ ] The Category filter lists only Categories with results, with counts. Selecting a parent includes its Subcategories.
- [ ] Searching from a category page starts with that Category selected.
- [ ] A guest never sees an article, a count or a Category from an article the guest cannot read.
- [ ] No results shows "Raise a ticket", and the new ticket keeps the query.
- [ ] The home dropdown and the new-ticket suggestions behave as before.
- [ ] The home dropdown shows "See all results", which opens the page with the query.
