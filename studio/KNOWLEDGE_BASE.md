# Knowledge base

Agents write articles in the desk at `/helpdesk/kb`. Customers and guests read them in the portal at `/help`. This file follows an article from the database to both apps. For how the portal itself is built, read [`README.md`](README.md).

## Data

| DocType | Folder under `helpdesk/helpdesk/doctype/` | Holds |
|---|---|---|
| `HD Article` | `hd_article` | title, category, content, excerpt, author, `status`, `visibility`, `title_slug`, views |
| `HD Article Category` | `hd_article_category` | name, description, icon, `pinned`, `pinned_order` |
| `HD Article Feedback` | `hd_article_feedback` | one vote per user or guest visitor: 0 none, 1 like, 2 dislike |

`HD Settings` holds the site-wide switches on its knowledge base tab:

- `public_knowledge_base`: guests can read the KB. If it is off, guests must sign in.
- `prefer_knowledge_base`: the customer home is the KB (`/help`), not the ticket list (`/help/my-tickets`).
- `allow_anonymous_article_voting`: guests can vote.
- `banner_image`, `banner_preset`: the banner on the KB home.

## Who can read what

Only `Published` articles are readable outside the desk. `visibility` then decides who sees an article:

| Visibility | Guest | Customer | Agent |
|---|---|---|---|
| `Public` | yes, if `public_knowledge_base` is on | yes | yes |
| `Customers` | no | yes | yes |
| `Private` | no | no | yes |

Agents see every article, in every status. A signed-in user without a customer role sees only `Public`.

The rules live in `hd_article/hd_article.py`:

- `make_article_filters()` builds the filters that every list query uses.
- `can_view_article()` checks one article.
- `permission_query` and `has_permission` apply the same rules to Frappe permissions. `helpdesk/hooks.py` registers them.

A category has no visibility field. `get_category_visibility()` in `hd_article_category.py` reads it from the category's articles. An article that joins a category can only get stricter visibility, never wider (`get_stricter_visibility()`).

The `General` category is reserved. It cannot be renamed or deleted.

## APIs

`helpdesk/api/knowledge_base.py` has the KB endpoints.

- **Reads** (guests allowed, `GET`): `get_categories`, `get_articles`, `get_kb_sidebar`, `get_article`, `get_article_markdown`, `search_articles`.
- **Guest writes** (`POST`, rate limited): `vote_on_article`, `increment_views`. A guest voter is known by the `hd_visitor` cookie.
- **Agent only**: `create_category`, `delete_articles`, `move_to_category`, `merge_category`, `get_category_visibility`, `set_category_visibility`, `get_general_category`.

Every guest endpoint calls `validate_public_access()` first. Keep that call in any new guest endpoint.

Other files:

- `helpdesk/api/article.py`: `get_related` (articles for a ticket), `get_article_stats` and search helpers.
- `helpdesk/search.py`: the RediSearch index for articles. `after_migrate` and a scheduled job build it.
- `helpdesk/api/config.py`: `get_config` gives the portal its KB flags, banner and KB form scripts.

## Desk: authoring

| What | Where |
|---|---|
| Article and category list | `desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue` (`/helpdesk/kb`) |
| Read and edit an article | `desk/src/pages/knowledge-base/Article.vue` (`/helpdesk/kb/articles/:articleId`) |
| New article | `desk/src/pages/knowledge-base/NewArticle.vue` |
| Category, access, move and merge dialogs | `desk/src/components/knowledge-base/` |
| Desk KB state | `desk/src/stores/knowledgeBase.ts` |
| KB settings tab | `desk/src/components/Settings/KnowledgeBase/KnowledgeBase.vue` |

The desk links to the portal copy of an article with `CUSTOMER_PORTAL_ROOT + ROUTES.article(...)` from `@helpdesk/shared`.

## Portal: reading

| Page | URL | Data |
|---|---|---|
| `public_kb` | `/help` | `get_categories`, `get_articles` (popular or recent) |
| `categories` | `/help/categories` | `get_categories` |
| `category` | `/help/category/:category` | `get_articles` for one category |
| `article` | `/help/articles/:name-slug` | `get_article`, `increment_views`, `vote_on_article`, `get_article_markdown` |
| `search` | `/help/search` | `search_articles` with `start`, `page_length` and `category` |

All four pages allow guests and use `useKnowledgeBaseHeader` and the `kb_settings` Studio Component. The sidebar, the article cache and hover prefetch are in `studio/helpdesk/stores/knowledgeBase.ts`. The article parts (body, contents, feedback, sidebar, "copy for LLM") are in `studio/helpdesk/components/knowledge_base/`.

Search (`PortalArticleSearch`) and the article suggestions on the new ticket form both use `useArticleSearch`, which calls `search_articles`.

## Settings shared by both apps

The KB look and feel (banner, pinned categories, header links) has one form, `shared/src/settings/KnowledgeBaseForm.vue`. The desk Settings tab and the portal Settings dialog both render it.

`shared/src/settings/knowledgeBaseDraft.ts` holds the unsaved draft. It writes `HD Settings`, the category pins and the header links. Header links are stored in an `HD Form Script` with `apply_to_knowledge_base` set.

`?preview=1` on the KB home shows the unsaved draft (`shared/src/knowledgeBasePreview.ts`).

## Old URLs

`website_redirects` in `helpdesk/hooks.py` keeps the URLs of the old portal working:

| Old | New |
|---|---|
| `/helpdesk/kb-public` | `/help` |
| `/helpdesk/kb-public/articles/<name>` | `/help/articles/<name>` |
| `/helpdesk/kb-public/<category>` | `/help/category/<category>` |

## Tests

- Backend: `helpdesk/tests/api/test_knowledge_base.py` (public reads, customer-only articles, permissions, category access, search), `helpdesk/tests/api/test_article.py`, `helpdesk/tests/test_search.py`, and the DocType tests in `hd_article` and `hd_article_category`.
- End to end: `e2e/tests/knowledge-base/` has the portal walkthrough and the agent spec. `e2e/helpers/portal.ts` makes categories and articles over REST.

When you add a guest endpoint, add a test that a guest is refused while `public_knowledge_base` is off.
