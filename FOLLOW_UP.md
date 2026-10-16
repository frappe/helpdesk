# Follow-up: move article search to SQLite

#3846 / #3847 keep article search on RediSearch (`helpdesk/search.py`) because that code is already proven in production. Move it to Frappe's SQLite search in the next PR, then delete this file.

## Known RediSearch problems shipping with these PRs

- **New and edited articles go stale.** Nothing re-indexes an article when it is saved. The scheduler rebuilds only when the index is missing, or when its document count is more than 10% off. A new article is not found, and an edited one shows its old text in the excerpt, until the index is rebuilt (HD Settings > Regenerate Search Index).
- **The index lives in the cache Redis.** `allkeys-lru` can evict indexed articles without warning, and a restart loses the whole index until the scheduler rebuilds it.
- **It needs the RediSearch module.** Frappe Cloud and CI (`redis-stack-server`) have it. A plain Redis does not, and there `search_articles` and `get_related` return nothing.
- **Hits are filtered after the search.** `search` returns at most `NUM_RESULTS` (5) sections. `filter_public_articles` then drops the ones the reader may not see, so the search box can show fewer than 5 articles.

## Restore the SQLite version

It was built and tested on `feat/public-kb`, then taken out. Start from these commits:

- `3cace6a01` `HelpdeskArticleSearch` and `get_related`
- `40c364c32` prefix matching from three letters
- `13e6f3198` `visibility` in the index, and the `rebuild_article_search_index` patch
- `db57db352` `reindex_articles` after bulk `set_value` (`update_articles`, `move_to_category`)

Also restore:

- The `sqlite_search` hook entry
- The SQLite `TestSearch` and `TestRelatedArticles` tests
- The e2e `indexArticles` helper, which runs `frappe.search.sqlite_search.index_docs_in_queue`
- A rebuild button for the SQLite indexes

## Then remove RediSearch

- `helpdesk/search.py`
- `search`, `search_with_enough_results`, `filter_public_articles`, `sanitize_query`, `get_nouns`, `get_noun_phrases` and `search_readable` in `helpdesk/api/article.py`
- The `helpdesk.search.*` entries in `hooks.py`: `after_install`, `after_migrate` and the scheduler
- The search tab in `hd_settings.json`: `name_weight`, `subject_weight`, `description_weight`, `headings_weight`
- The RediSearch tests in `helpdesk/tests/api/test_article.py` and `test_knowledge_base.py`, and `make_search_hit` / `make_search_page` in `helpdesk/test_utils.py`
- The `textblob` dependency, if nothing else uses it
