# Knowledge base

Agents write articles in the desk at `/helpdesk/kb`. Customers and guests read them in the portal at `/help`. This file follows an article from the database to both apps. For how the portal itself is built, read [`README.md`](README.md).

## Data

| DocType | Folder under `helpdesk/helpdesk/doctype/` | Holds |
|---|---|---|
| `HD Article` | `hd_article` | title, category, content, excerpt, author, `status`, `visibility`, `title_slug`, views, `weight`, `pinned`, `pinned_order` |
| `HD Article Category` | `hd_article_category` | name, description, icon, `pinned`, `pinned_order` |
| `HD Article Feedback` | `hd_article_feedback` | one vote per user or guest visitor: 0 none, 1 like, 2 dislike |

`HD Settings` holds the site-wide switches on its knowledge base tab:

- `public_knowledge_base`: guests can read the KB. If it is off, guests must sign in.
- `prefer_knowledge_base`: the customer home is the KB (`/help`), not the ticket list (`/help/my-tickets`).
- `allow_anonymous_article_voting`: guests can vote.
- `banner_image`, `banner_preset`: the banner on the KB home.
- `banner_title`, `banner_subtitle`: the KB home heading and the text under it. Empty uses the default text.
- `enable_ai_search`, `ai_provider`, `ai_api_key`, `ai_model`: the AI search tab (see [AI search](#ai-search)). System Managers only (permission level 1), and the key is a Password field, so no read path returns it.
- `show_footer`, `footer_tagline`, `footer_copyright`, `footer_items`, `social_links`: the KB footer. `footer_items` is a `Top Bar Item` table, as in Website Settings: a row without `parent_label` is a column; link rows name their column in `parent_label`. `social_links` is a `Top Bar Item` table too. `validate_footer` allows at most four columns with different titles and only web, email and `/` links in both tables.

Within a category, every article list (`get_articles` with a `category`, `get_subcategory_articles`, `get_kb_sidebar`) sorts by `weight` first, heaviest on top. Pins never touch the weight; Featured reads them by `pinned_order`.

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

- **Reads** (guests allowed, `GET`): `get_categories`, `get_articles`, `get_featured_articles`, `get_subcategory_articles`, `get_kb_sidebar`, `get_article`, `search_articles`. `/help/articles/<name>.md` serves an article as plain Markdown (`ArticleMarkdownPage`), the link Copy for LLM and Open in Claude/ChatGPT use.
- **Guest AI search** (`POST`, rate limited): `answer_question`.
- **Guest writes** (`POST`, rate limited): `vote_on_article`, `increment_views`. A guest voter is known by the `hd_visitor` cookie.
- **Agent only**:
  - Categories: `create_category`, `merge_category`, `delete_category`, `get_category_delete_summary`, `get_category_options`, `get_category_visibility`, `set_category_visibility`, `get_category_access`, `get_general_category`.
  - Articles: `move_to_category` (also restores an archived article as a draft), `archive_articles`, `delete_articles`, `bulk_delete` (the list's Delete, in one request), `get_cited_articles`, `set_pinned_articles`.
  - `search_categories` is the link search for HD Article Category, registered in `standard_queries`. It labels a subcategory `Parent › Sub`.

Every guest endpoint calls `validate_public_access()` first. Keep that call in any new guest endpoint.

Other files:

- `helpdesk/api/article.py`: `get_related` (articles for a ticket), `get_article_stats` and search helpers.
- `helpdesk/search.py`: the RediSearch index for articles. `after_migrate` and a scheduled job build it.
- `helpdesk/api/config.py`: `get_config` gives the portal its KB flags, banner, KB form scripts and `ai_search_enabled`.
- `helpdesk/ai_search.py`: AI search, from article indexing to the answer.

## Desk: authoring

| What | Where |
|---|---|
| Article and category list | `desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue` (`/helpdesk/kb`) |
| Read and edit an article | `desk/src/pages/knowledge-base/Article.vue` (`/helpdesk/kb/articles/:articleId`) |
| New article | `desk/src/pages/knowledge-base/NewArticle.vue` |
| Category, access, move, merge and weight dialogs | `desk/src/components/knowledge-base/` |
| Desk KB state | `desk/src/stores/knowledgeBase.ts` |
| KB settings tab | `desk/src/components/Settings/KnowledgeBase/KnowledgeBase.vue` |

The desk links to the portal copy of an article with `CUSTOMER_PORTAL_ROOT + ROUTES.article(...)` from `@helpdesk/shared`.

## Portal: reading

| Page | URL | Data |
|---|---|---|
| `public_kb` | `/help` | `get_categories`, `get_articles` (popular or recent), `get_featured_articles` |
| `categories` | `/help/categories` | `get_categories` |
| `category` | `/help/category/:category` | `get_articles` for one category, 20 at a time as the reader scrolls |
| `search` | `/help/search?q=` | `answer_question` (AI search on), else `search_articles` |
| `article` | `/help/articles/:name-slug` | `get_article`, `increment_views`, `vote_on_article`, `/help/articles/<name>.md` |

All five pages allow guests and use `useKnowledgeBaseHeader` and the `kb_settings` and `footer` Studio Components. The sidebar, the article cache and hover prefetch are in `studio/helpdesk/stores/knowledgeBase.ts`. The article parts (body, contents, feedback, sidebar, "copy for LLM") are in `studio/helpdesk/components/knowledge_base/`.

Search (`PortalArticleSearch`) and the article suggestions on the new ticket form both use `useArticleSearch`, which calls `search_articles`.

With AI search on, Enter in the home search opens the `search` page (`/help/search?q=`), which asks `answer_question` (see [AI search](#ai-search)).

## AI search

An AI answer to a reader's question, from the articles that reader may read, built on Frappe Flow (`frappe.flow`, which ships with the framework). It is off by default. Until Flow can run an agent for portal readers, it returns the best matches by meaning only, and the portal labels it as search, not as an answer (see [Answering](#answering)).

### Settings

The AI search tab of `HD Settings` (desk Settings > Customer Portal > AI search, `desk/src/components/Settings/AISearch/`) has:

- `enable_ai_search`: on or off. The switch saves on its own, as soon as it changes. Turning it on without a saved provider and model is refused, and the switch stays off.
- `ai_provider`: a LiteLLM provider name, such as `openai` or `anthropic`.
- `ai_api_key`: a Password field.
- `ai_model`: the model at that provider, such as `gpt-4.1-mini`.

The provider, model and key save together with Save. All of them are System Manager fields (permission level 1). Saving with AI on writes the Flow records the assistant runs on (`HDSettings.sync_ai_search`):

- a `Flow Provider` named after the provider, created only if the site has none; an existing one keeps its own key;
- a `Flow Model` titled `Helpdesk AI Search`, which carries the key and takes precedence over the provider's;
- a system-generated `Flow Agent`, `helpdesk/kb-assistant`, holding the guardrail instructions and the model.

The agent is limited to the product (`brand_name`, else "Helpdesk") and to the sources it is given, and answers `OFF_TOPIC` to anything else. The guardrails are on by default and live in `INSTRUCTIONS` in `helpdesk/ai_search.py`.

Articles are embedded with the model in **Flow Knowledge Settings**. Set an embedding model there first; turning AI on without one shows a warning and indexes nothing.

### Who is answered from what

`index_article` (`helpdesk/ai_search.py`) keeps every published article in one `Flow Knowledge Source` (type Text, titled with the article's name) in the Flow knowledge base of its audience:

| `visibility` | Knowledge base |
|---|---|
| `Public` | `Helpdesk Articles - Public` |
| `Customers` | `Helpdesk Articles - Customers` |
| `Private` | `Helpdesk Articles - Agents` |

A question searches only the bases its asker may read, a guest or a user without a customer role gets Public, a customer Public and Customers, an agent all three. Flow itself does not check permissions per chunk: the knowledge base is the boundary, so never search a base that was not chosen by role.

Before any passage reaches the model, its article is read again with `make_article_filters`. An article narrowed, unpublished or deleted after it was indexed is dropped even while the index is behind.

Saving or deleting an article queues `index_article` (queue `short`) while AI search is on and an embedding model is set. Turning AI search on queues `index_all_articles` (queue `long`). An unpublished or deleted article leaves the index; a narrowed one moves to the base of its new audience.

### Answering

`answer_question(question)` in `helpdesk/api/knowledge_base.py` (guests allowed, `POST`):

- calls `validate_public_access()`, so a guest is refused while `public_knowledge_base` is off, and is refused while AI search is off;
- is rate limited to 10 requests a minute per user, or per IP for a guest, and cuts the question at `ANSWER_QUESTION_LENGTH` (500) characters;
- retrieves the best 8 passages (`frappe.flow.knowledge.retriever.retrieve`) from the article bases its asker may read, keeps the ones whose article the asker may read now, and returns:

```
{ "refused": bool, "message": "…" (only when refused),
  "related": [{ "name", "title", "title_slug", "excerpt" }] }
```

`related` are the matching articles the asker may read, at most 4. A question nothing readable matches gets `refused` set, "I can only help with <product>." as `message`, and nothing else. No model is called, so there is no answer text or cited sources until the blocker below is fixed.

Until the asker's bases can be searched, `answer_question` throws `AISearchNotReadyError` instead of refusing: while Flow Knowledge Settings has no embedding model, or none of the asker's bases holds a `Completed` source yet. The page then shows its error line and the plain `search_articles` matches, so readers keep search while indexing catches up.

A passage counts as a match only when its cosine similarity is at least `MIN_VECTOR_SCORE` (0.3), so an off-topic question is refused even though articles exist.

**Blocker: off-topic questions are refused only with Flow's Vector search.** Flow's retriever always returns the top passages, and under Hybrid search (Flow's default) their `score` is LanceDB's rank-fused (RRF) score, which says how a passage ranked, not how relevant it is. Helpdesk cannot tell an off-topic question from an on-topic one there, so it applies the threshold only when **Flow Knowledge Settings → Search Type** is Vector. Fix in Flow: return each hit's vector similarity in hybrid mode too, then apply the threshold always.

**Blocker: Flow cannot run an agent for portal readers.** Flow runs agents only as sessions on its flow server (`frappe.flow.lib.agent.Agent.run`). A session needs read access to the `Flow Agent` and `Flow Model` (roles System Manager and Flow User), belongs to a signed-in owner whose callbacks act as that user, and runs asynchronously. Guests and customers have none of that, and Flow has no synchronous call. Calling the model directly with LiteLLM would bypass Flow's runtime, so Helpdesk does not. Once Flow can run an agent for a guest, send the retrieved articles to `helpdesk/kb-assistant`, add `answer` (citing `[n]`) and `sources` to the response, and render them on the portal page with the streamed answer, follow-ups and "Powered by Flow". Until then the portal does not call the page an answer: the search row reads "See the best matches for …", not "Ask AI".

### Portal page

`PortalAnswerPage` (`/help/search?q=`, the `search` page) shows the question, a thinking state (a pulsing ✦ with rotating status lines), then the related articles below, and "Search powered by Frappe Flow". With no question in the URL it shows "What are you looking for?" and makes no call. A refusal shows its line and a "Raise a ticket" button, which opens the new ticket form with the question (`ROUTES.newTicket({ from: 'search', q })`), or sign-in for a guest, and is hidden when `hide_raise_ticket_button` is on; it never lists plain matches. If the call fails, it says so and lists the plain `search_articles` matches.

With AI search on, the search box (`PortalArticleSearch`) is the "glow ring" of the sketch: a subtle gray gradient edge, built from the `--outline-gray-*` and `--ink-gray-*` theme tokens so it follows dark mode, that brightens, with a faint glow, on focus, and ✦ in place of the magnifier. "/" still focuses it. With it off, the box is the plain one. `get_config` gives the portal `ai_search_enabled`, which is on only when AI search is on and the reader may read the knowledge base. With it off, the home search shows today's dropdown and Enter opens no answer page.

## Settings shared by both apps

The KB look and feel (banner, pinned categories and articles, header links, footer) has one form, `shared/src/settings/KnowledgeBaseForm.vue`, in four tabs: Home page, Header, Footer and Access. The desk Settings tab and the portal Settings dialog both render it.

`shared/src/settings/knowledgeBaseDraft.ts` holds the unsaved draft. It writes `HD Settings`, the category and article pins and the header links. Header links are stored in an `HD Form Script` with `apply_to_knowledge_base` set.

`?preview=1` on the KB home shows the unsaved draft (`shared/src/knowledgeBasePreview.ts`). Preview is always available; without edits it shows the saved look.

## Old URLs

`website_redirects` in `helpdesk/hooks.py` keeps the URLs of the old portal working:

| Old | New |
|---|---|
| `/helpdesk/kb-public` | `/help` |
| `/helpdesk/kb-public/articles/<name>` | `/help/articles/<name>` |
| `/helpdesk/kb-public/<category>` | `/help/category/<category>` |

## Tests

- Backend: `helpdesk/tests/api/test_knowledge_base.py` (public reads, customer-only articles, permissions, category access, search, AI answers by role, AI index updates), the AI search tab in `hd_settings/test_hd_settings.py`, `helpdesk/tests/api/test_article.py`, `helpdesk/tests/test_search.py`, and the DocType tests in `hd_article` and `hd_article_category`.
- End to end: `e2e/tests/knowledge-base/` has the portal walkthrough and the agent spec. `e2e/helpers/portal.ts` makes categories and articles over REST.

When you add a guest endpoint, add a test that a guest is refused while `public_knowledge_base` is off.
