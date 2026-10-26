# Customer portal

The customer portal is a Studio app (Studio ships with frappe). Customers use it at `/help` to read the knowledge base, raise tickets and reply to them. Agents use the desk app at `/helpdesk`.

This file explains how the portal is built, where its code lives and how to work on it. For the knowledge base from end to end (DocTypes, APIs, desk authoring), read [`KNOWLEDGE_BASE.md`](KNOWLEDGE_BASE.md).

## How Studio runs the portal

Studio is a Frappe app that renders pages from JSON. Each page is a tree of blocks: Vue components with props, events and styles. A page can also have a TypeScript setup script. The values that the script returns are available to the blocks through `{{ }}` expressions.

Helpdesk ships the portal as a **standard app**: the pages live as files in this folder, not only in the database.

- The files in git are the source of truth. `bench migrate` imports them into the `Studio App`, `Studio Page` and `Studio Component` DocTypes. It also deletes pages that have no file.
- With `developer_mode` on, a save in the Studio editor writes the JSON back to these files. Commit the file diff.
- Page scripts (`.ts`) and Vue components (`.vue`) live only on disk. The database never holds them.
- `bench build-studio-app helpdesk --site <site>` builds the production bundle into `helpdesk/public/app_builds/helpdesk/` (gitignored). `bench build --app helpdesk` also builds it.

Studio documents its own rules. Read them before you change a page:

| Topic | File in `apps/frappe` |
|---|---|
| Dev server and `watch-studio` setup | `studio/frontend/README.md` |
| File layout, page JSON, `setup(context)`, custom Vue components, sync loop | `skills/studio-app-building/SKILL.md` |
| Runtime rules: `{{ }}`, event scripts, v-model, Repeater, icons, tokens | `skills/studio-app-building/RULES.md` |
| Routing and the global `boot` | `skills/studio-app-building/ROUTING.md` |
| Visual design language | `skills/studio-app-building/DESIGN.md` |

## What is where

```
studio/helpdesk/
  helpdesk.json          Studio App record: route "help", app_home = public_kb
  router.ts              opens the Settings dialog at <page>/settings/<screen>
  studio_page/<page>/    <page>.json (block tree) + <page>.ts (setup script)
  studio_components/     Studio Components: reusable block trees with inputs
  components/            custom Vue components, by area
  stores/                module-level state shared between pages
  composables/           page logic, one concern per file
  tailwind.config.js     adds shared/src to Studio's Tailwind scan
  tsconfig.json          @app/* alias. Studio rewrites it on every app save
```

### Pages

| Page | URL | Guest | Shows |
|---|---|---|---|
| `public_kb` | `/help` | yes | KB home: banner, search, pinned categories, popular and recent articles |
| `categories` | `/help/categories` | yes | All categories with a filter |
| `category` | `/help/category/:category` | yes | Articles in one category |
| `article` | `/help/articles/:name` | yes | Article body, contents, feedback, related articles |
| `search` | `/help/search` | yes | Article search with a Category filter; `?q=&category=` hold the state |
| `customer_tickets` | `/help/my-tickets` | no | Ticket list with saved views, filters, sort and export |
| `new_ticket` | `/help/tickets/new` | no | New ticket form with article suggestions |
| `ticket` | `/help/tickets/:name` | no | Ticket thread, reply composer, details and feedback |

The `article` URL param is `<name>-<slug>`. `articleName()` in `stores/knowledgeBase.ts` reads the name from it.

### Studio Components

Every page embeds `header` and `kb_settings`.

- `header`: the top bar. It has the brand, breadcrumbs, quick links, the theme toggle and the account menu. Its inputs (`crumb`, `parentRoute`, `drawerToggle` and others) are listed in the JSON.
- `kb_settings`: the portal Settings dialog. It has profile, members, knowledge base and portal settings tabs. It has no inputs and binds to `useSettingsModal`.
- `category_grid`: a Repeater of category cards. `public_kb` and `categories` use it.

### Custom Vue components

Under `components/`, by area: `ui`, `header`, `list`, `ticket`, `knowledge_base` and `settings`. A block uses one with `isCustomVueComponent: true` and the file name as `componentName`.

- Portal-only components start with `Portal`.
- The file name must be unique in `studio/helpdesk/` and must not match a Studio built-in component. Studio skips a clash and writes an Error Log.
- The desk imports `NewTicketForm.vue` and `CustomActions.vue` from here by relative path. Test the desk when you change them.

### Stores

The stores are module-level singletons, not Pinia.

- `settings/index.ts`: `useSettingsModal(context)`. Every page spreads it into its return value. It binds the router and socket, and it exposes `t` (translate) and `routes` (`ROUTES`) to the blocks.
- `session.ts`: user and site flags from `helpdesk.api.config.get_config` (`isGuest`, `isAgent`, `isPublicKnowledgeBase`, brand).
- `router.ts`: holds the router, because page scripts get it only through `context`. Use `navigateTo()` from here.
- `knowledgeBase.ts`: the KB sidebar, an article cache and hover prefetch.
- `views.ts`: saved ticket list views (`HD View`).
- `ticketMeta.ts`: ticket statuses and priorities, loaded lazily because guests cannot read them.
- `recent.ts`, `conversationLayout.ts`: per-browser preferences in localStorage.

### Composables

- `useKnowledgeBaseHeader`: the header for the four KB pages. It runs KB form scripts into header links and custom actions.
- `useArticleSearch`: debounced article search, used by the search box and the new ticket form. `usePagedArticleSearch`: the search page's pages of 20, with counts per Category.
- `useDrawer`: the ticket page's mobile side drawer. `useBottomSheet`: open state for the knowledge base sidebar, a frappe-ui `BottomSheet` on phones.
- `useTicketThread`, `useReplyComposer`, `useTicketDetails`, `useTicketFeedback`, `useOutsideHoursBanner`, `useChatRows`: the parts of the `ticket` page.
- `useRememberedCount`: remembers a list's length so its skeleton keeps the same size.

### Shared code: `@helpdesk/shared`

`shared/src` holds the code that the portal and the desk both use. The root `package.json` links it as `@helpdesk/shared`, so run `yarn install` in `apps/helpdesk` before the first build.

- `portalRoutes.ts`: `ROUTES`, every portal path. The desk uses it to link into the portal.
- `translation.ts`: `__()` and `fetchTranslations()`.
- `utils.ts`: dates, `CUSTOMER_PORTAL_ROOT`, `updateTicket`, `addHeadingIds`, `countLabel` and more.
- `settings/`: `KnowledgeBaseForm` and `PortalPermissionsForm`, used by both the desk Settings and the portal Settings dialog.
- `filter/`, `ticketCells.ts`, `ticketStatus.ts`, `tiptap.ts`, `formScripts.ts` and shared icons.

Put code in `shared/src` only when both apps use it. Inside `shared/src`, use relative imports.

### Backend and serving

- `helpdesk/hooks.py`:
  - `studio_app_boot` sets the global `boot` (timezone, home page, brand).
  - `update_website_context` sets the portal title and favicon.
  - `website_redirects` sends the old `/helpdesk/my-tickets` and `/helpdesk/kb-public` URLs to `/help`.
- `helpdesk/helpdesk/hooks/studio_app.py`: the two hook functions.
- `helpdesk/www/helpdesk/index.py`: sends a customer who opens `/helpdesk` to the portal.
- `helpdesk/api/`: the portal calls `config.py`, `knowledge_base.py`, `article.py` and `customer.py`. Ticket calls go to `helpdesk/helpdesk/doctype/hd_ticket/api.py`.

## Set up for development

1. Do the "Frontend Development & Exported Apps" setup in `apps/frappe/studio/frontend/README.md`: `developer_mode`, `ignore_csrf`, `bench setup requirements --dev` and `yarn dev --host` in `apps/frappe/studio/frontend`. In developer mode `bench watch` starts the same dev server.
2. Run `yarn install` in `apps/helpdesk`. This links `@helpdesk/shared`.
3. Start the watcher and keep it running: `bench --site <site> watch-studio`.
4. Open `/dev/help` on the Vite dev server, for example `http://<site>:8080/dev/help`.

Use `/dev/help` while you work. `/help` serves the last production build, so it does not show your changes until you build again.

What reloads by itself:

- `.ts` and `.vue` files: Vite hot-reloads them.
- Page and component JSON: `watch-studio` imports it.
- `tailwind.config.js`: restart Vite.
- A new folder under `studio/`: restart `watch-studio`.

Do not run `bench migrate` or `build-studio-app` in the edit loop. Build only to check the production bundle.

## Make a change

### Change a page

1. Read the page's `.json` and `.ts` together. The blocks bind only to what `setup` returns, to `route`, to `inputs` (inside a Studio Component) and to `dataItem` (inside a Repeater).
2. Put the logic in the `.ts` file, a composable or a store. Keep each `{{ }}` expression to a name or a short call.
3. Edit the block tree in the Studio editor or in the JSON file. If you edit the JSON while the page is open in the editor, refresh the editor before you save there.
4. Check the page at `/dev/help` as a guest, a customer and an agent where they apply.

### Add a page

1. Make the page in the Studio editor, inside the Helpdesk app. In developer mode the save writes `studio_page/<page>/<page>.json`.
2. Add `<page>.ts` next to it with `export default function setup(context)`. Spread `useSettingsModal(context)` (or `useKnowledgeBaseHeader(context)` on a KB page) into the return value.
3. Add `header` and `kb_settings` blocks, like the other pages.
4. Add the path to `ROUTES` in `shared/src/portalRoutes.ts`.
5. Set `allow_guest` only if guests must see the page.

### Add a component

1. Add `components/<area>/Portal<Name>.vue`. Use frappe-ui components and Tailwind with the semantic tokens.
2. Use it in a block with `isCustomVueComponent: true` and `componentName: "Portal<Name>"`.
3. Make it a Studio Component (`studio_components/`) only if it is a block tree that pages repeat. Make it a Vue component when it has its own logic.

### Rename or retitle a page

Keep `page_name` the same. Move the `.json` and `.ts` to the new folder name together. A new title also changes the route name, so search for `router.push({ name: ... })` callers.

## Conventions

- **Routes**: use `ROUTES` in scripts and `{{ routes.x(...) }}` in blocks. Navigate with `navigateTo()` from `stores/router.ts`.
- **Translation**: use `__('literal string')` from `@helpdesk/shared/translation` with `{0}` placeholders. In blocks, use `{{ t('...') }}`. Build labels inside a function or computed, so they follow a language change.
- **Imports**: `@app/...` for code in `studio/helpdesk`, `@helpdesk/shared/<module>` for shared code.
- **Comments**: one line, only for a reason the code cannot show.
- **Guest APIs**: `@frappe.whitelist(allow_guest=True, methods=["GET"])`, with `validate_public_access()` and a `@rate_limit` where it can be abused.
- **Commits**: conventional commits with the `portal` or `kb` scope, for example `fix(portal): send a reply that has only attachments`.

## Gotchas

- If you edit `helpdesk.json` or a Studio Component JSON by hand, increase its `modified` value. `bench migrate` skips the file otherwise. `watch-studio` imports it anyway.
- `watch-studio` does not sync deletions. `bench migrate` deletes pages and apps that have no file. It never deletes Studio Components.
- A database patch does not change these files. When a patch changes Studio records, change the files too.
- The Studio file explorer cannot edit exported JSON. Edit it in the editor or on disk.
- A component in a block tree that Studio does not know fails the build.

## Tests

- **End to end**: Playwright specs in `e2e/tests/`. Portal specs sit next to their desk page: `knowledge-base/`, `tickets/customer/`, `tickets/list/`, `tickets/new/` and `settings/portal-settings-walkthrough.spec.ts`. Read `e2e/README.md` for how to run and write them.
- **Backend**: `helpdesk/tests/api/test_knowledge_base.py`, `test_article.py`, `test_customer.py` and `test_auth.py`. Read `helpdesk/tests/AGENTS.md` for the rules.
