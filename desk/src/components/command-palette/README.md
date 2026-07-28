# Command Palette (Cmd/Ctrl + K)

A contextual command palette for the agent portal. It leads with the actions for
whatever you're looking at — on a ticket, that ticket's actions; on the ticket
list, that list's filters and views — then falls back to search, recents and
navigation.

Mounted once, in `layouts/AppSidebar.vue`. Not rendered on mobile or in the
customer portal.

---

## Why it changed

The previous palette did four things: "Tickets", "Knowledge Base", `#234`, and a
"Search for…" link that navigated to the search page. No actions, no context, no
inline results.

It was also mounted **twice** — `AppSidebar.vue` (bound to `v-model`) and
`DesktopLayout.vue` (bound to nothing) — so Cmd+K toggled two instances, and
`CPGroupResult.vue` was dead code that nothing imported.

The largest gap: `modals/ShortcutsModal.vue` already documents a full
Linear-style action set on a ticket (`A` assign, `S` status, `P` priority, `R`
reply, `C` comment, `⌘.` copy id …) that the palette knew nothing about. Those
actions are now palette rows that print the same key — same handlers, second
entry point, no duplicated business logic.

---

## Files

### New

| File | Lines | Purpose |
|---|---|---|
| `useCommandPalette.ts` | 183 | Engine: open state, drill-down stack, scoring, grouping, FTS search |
| `commands.ts` | 255 | Root command assembly + navigate / create / account / recents / settings |
| `ticketCommands.ts` | 217 | Ticket-detail context and its drill-downs |
| `ticketListCommands.ts` | 134 | Ticket-list context (filters, views) |
| `searchCommands.ts` | 51 | Maps FTS hits onto rows |
| `optionCommands.ts` | 45 | Status / priority pickers, shared by both contexts |
| `paletteTypes.ts` | 55 | Shared `Command` / `SearchItem` types, group names, weights |
| `fuzzyScore.ts` | 35 | Dependency-free subsequence scorer |
| `fuzzyScore.check.ts` | 38 | Runnable assertion check for the scorer |
| `recentTickets.ts` | 33 | localStorage MRU for tickets and commands |
| `CommandPaletteRow.vue` | 55 | Row renderer |

`CommandPalette.vue` (231 lines) was rewritten. `CPGroup.vue` and `CPGroupResult.vue` were
deleted — `CommandPaletteRow.vue` replaces both.

### Modified outside this folder

- `layouts/AppSidebar.vue` — renders `<CommandPalette />` with no model; sidebar Search
  button calls the shared `openPalette()`.
- `layouts/DesktopLayout.vue` — removed the second, unbound `<CommandPalette />`.
- `components/index.ts` — dropped the `CommandPalette` barrel export. `CommandPalette.vue` is
  now a singleton that registers its own global shortcut; a second mount would
  give two `Cmd+K` handlers on one `isOpen`.
- `pages/ticket/TicketAgent.vue` — records ticket visits for the Recent list.
- `components/ListViewBuilder.vue` — split view-loading from filter-applying
  (see [Ticket list context](#ticket-list-context)).

---

## Architecture

```
CommandPalette.vue     dialog, keyboard handling, rendering
  └── useCommandPalette.ts   state + scoring + search   (no Vue components)
        ├── commands.ts            root assembly
        │     ├── ticketCommands.ts
        │     └── ticketListCommands.ts
        ├── paletteTypes.ts        shared types (no import cycle)
        ├── fuzzyScore.ts
        └── recentTickets.ts
```

State lives at **module scope** in `useCommandPalette.ts`, not in the component.
That's what lets the sidebar button, the keyboard shortcut and the dialog all
drive one instance — and it's what fixed the double-mount.

`paletteTypes.ts` exists purely to break a cycle: the engine needs
`buildRootCommands`, and the command modules need the `Command` type. Shared
types live in their own module so nothing imports in both directions.

### The `Command` shape

```ts
interface Command {
  id: string
  title: string
  group: string
  icon?: Component
  iconProps?: Record<string, unknown>   // props for data-driven icons
  subtitle?: string        // muted right-aligned text
  keywords?: string        // matched at a scoring penalty
  hint?: string            // combo string, e.g. "Mod+." — see note below
  weight?: number          // multiplies fuzzy score; <1 sinks a row
  dotClass?: string        // leading colour dot (status rows)
  rank?: number            // fixed score, bypasses the scorer
  children?: () => Command[] | Promise<Command[]>   // drill-down
  perform?: () => void
}
```

A command either drills in (`children`) or acts (`perform`). `run()` in the
engine picks based on which is present.

`iconProps` exists so rows can reuse the app's own data-driven icons instead of
a flat lucide glyph — priority rows render `TicketPriority.vue`
(`{ priority, iconOnly: true }`), so Bug/Critical get the badge and High/Medium/
Low get graduated bars, exactly as in the list column.

Hints render through the app's own `components/ShortcutKey.vue` (also used by
`AssignTo`, `Tags`, `FilterFieldList`), not frappe-ui's `KeyboardShortcut`.
frappe-ui's `bg` variant fills with `bg-surface-gray-2` — the same colour as the
active row — so chips vanished on hover and read as heavy blobs elsewhere.
`ShortcutKey` is outlined on `surface-base` and holds up in both states.
`CommandPaletteRow.vue` converts the combo string to the space-separated keys it expects,
resolving `Mod` to `⌘`/`Ctrl` per platform.

**Only set `hint` when the key reaches the same end result as the row** — not
when it reaches it the same way. `S` opens the status dropdown in the header
while the row drills into a list here; both change the status, so the hint is
honest. `Filter by status` has no hint because the app's `f` opens the whole
filter popover, which is a different outcome, not a different route to the same
one.

Every hinted key is a **page** shortcut and is inert while the palette is open —
`disableShortcuts()` bails inside `[role="dialog"]`. That's deliberate: it's what
stops `s`/`p`/`a` firing as you type a query. The chip teaches the key for next
time; it isn't an accelerator for this dialog.

### Ranking

`fuzzyScore(text, term)` — prefix (1000) beats word-boundary substring beats
mid-word substring beats scattered subsequence; `-1` means no match. Written by
hand rather than pulling `fuzzysort`, which is present but only as a transitive
dependency of `frappe-ui` (relying on hoisting is fragile).

Scoring rules:

- **`rank`** wins outright — server search hits arrive already relevance-ordered
  from SQLite BM25 and are not re-scored locally.
- **`weight`** multiplies the score. Context rows use `CONTEXT_WEIGHT = 1.2` so
  they beat search hits *deliberately*, not by luck. Nav links use `0.7` so they
  sink once you've typed something real.
- Group order follows the best score inside the group, so groups reorder rather
  than sitting in a fixed sequence.

Run the scorer's check with:

```bash
cd desk && ../node_modules/.bin/tsx src/components/command-palette/fuzzyScore.check.ts
```

(`tsx` lives in the repo-root `node_modules`. There is no test runner in `desk/`,
so no framework was added.)

---

## Contexts

Which commands appear is decided in `buildRootCommands()` from
`router.currentRoute`.

### Ticket detail (`route.name === "TicketAgent"`)

Change status · Change priority · Assign to · Change team · Change type · Reply ·
Add comment · Copy ticket ID · Copy ticket link

Each prints the shortcut the app already binds (`S`, `P`, `A`, `Shift+T`, `T`,
`R`, `C`, `Mod+.`, `Mod+Shift+.`). Mutations go through the same primitive the
UI uses — `useTicket(id).ticket.setValue.submit({ field: value })` — which is a
module-level cache, so the palette reaches the live resource the page is already
bound to. No prop drilling, no injection.

Assignment uses `frappe.desk.form.assign_to.add`, matching `AssignTo.vue`.

### Ticket list (`route.name === "TicketsAgent"`)

Filter by status · Filter by priority · Show tickets assigned to me · Switch
view · Clear filters

**These navigate rather than calling the list directly.** The palette lives in
the sidebar, outside `ListViewBuilder`'s `provide()` chain, so it cannot
`inject("listViewActions")`. But `ListViewBuilder` already reads
`route.query.filters` and merges it over the active view — so filters travel
through the URL and the palette stays fully decoupled. No registry, no lifted
state.

`ListViewBuilder.vue` had to be restructured for this. It previously ran one
function, `handleViewChanges()`, for everything — and that function reassigns
`order_by`, `columns` and `rows` from the view before applying URL filters. So
routing filters through it made every filter reset the user's sort. It is now
split:

- `switchToView()` owns sort, columns and rows, and runs only when `?view=`
  actually changes.
- `applyUrlFilters()` touches `filters` alone, layering the URL over
  `viewFilters` (the view's own) rather than over the previous result, so
  repeated pushes can't accumulate.

Two smaller gaps closed at the same time: the watcher didn't track
`route.query.filters` at all, and an empty array was read as "no override"
rather than "clear". An unresolvable `?view=` now redirects with `replace` and
keeps the filters, instead of pushing to the bare route and dropping them.

`_assign` is a comma-joined column, so "assigned to me" filters with
`["_assign", "like", "%<user>%"]`.

Filters layer onto the active view — `currentViewQuery()` preserves `?view=` so
filtering inside a saved view keeps you in it.

### Everywhere

Recent (recent commands, then recently visited tickets) · Navigate · Create ·
Account (theme, availability, Settings, log out) · `#234` jump.

Settings is a drill-down built from the `tabs` computed in
`Settings/settingsModal.ts`, which is already permission-filtered — so there is
no second copy of who-can-see-what. It keeps that file's own section headers
(My settings / Email Settings / App Settings) as palette groups. Typing "sla"
jumps straight to SLA Policies.

---

## Search

Uses the existing **SQLite FTS5** index — no new backend.

- Endpoint: `helpdesk.api.search.search` (`helpdesk/api/search.py`)
- Implementation: `helpdesk/search_sqlite.py`, indexing `HD Ticket`,
  `HD Ticket Comment` and `Communication`, permission-filtered by accessible
  tickets
- Called with `title_only: true` — a flag that already existed for exactly this
  fast path
- 200 ms debounce, minimum 2 characters (the server rejects shorter)
- Stale responses dropped by an incrementing token, so a slow reply can't
  overwrite a newer one
- Results sliced to 6 client-side, because `api/search.py` accepts a `limit`
  parameter but never forwards it to `search()`

Row titles are `stripTags()`-ed: the server wraps matches in `<mark>` and the
palette renders plain text rather than `v-html`-ing server content.

Rows render `status · #id` with a status colour dot. This matters more than it
sounds — demo data contains many tickets sharing a subject ("Unable to login to
the portal" ×N), and without status they look like duplicates when they are
genuinely distinct tickets.

---

## Keyboard model

| Key | Behaviour |
|---|---|
| `Cmd/Ctrl+K` | Toggle. Works from inputs and from inside the palette |
| `↑` / `↓` | Move selection |
| `Enter` | Drill in, or run |
| `Backspace` | On an empty query, pop one level |
| `Esc` | Peels one layer: clear query → pop level → close |

**The shortcut uses `useShortcut` from `frappe-ui`, not `@/composables/shortcuts`.**
The local one calls `disableShortcuts()`, which bails whenever focus is in any
input/textarea/contenteditable or inside `[role="dialog"]`, `[role="menu"]`,
`.dropdown-options` or `.form-control`. That meant Cmd+K could not open while a
filter box was focused, and could not close the palette once open. frappe-ui's
version takes `allowInInput` and `allowInDialog`.

A `condition` bows out inside `.ProseMirror` — the editor binds `Mod-k` for
insert-link and the palette must not steal it.

The page's own single-key shortcuts (`s`, `p`, `a`, …) remain suppressed while
the palette is open, because they still go through the local `useShortcut` and
its dialog guard. That's the desired behaviour: typing "assign" must not fire
`a`.

`shortcutsList` in `@/composables/shortcuts` has no consumers outside that file,
and `ShortcutsModal.vue` keeps its own hardcoded list, so dropping the local
Cmd+K registration changes nothing user-visible.

---

## Recents

`recentTickets.ts` — one list, `hd_recent_tickets:<user_id>`: the last 5 visited
tickets, recorded by a watcher in `TicketAgent.vue` once `ticket.doc.subject`
resolves. The ticket currently open is filtered out.

The key is per-user via `userStorage.ts`, which reads the session cookie rather
than the auth store — it runs at module load, before pinia exists. Subjects
carry customer names, and desks hot-desk.

There is deliberately no recent-**commands** list. It covered ~15 commands that
were all visible anyway, and burned rows a short list cannot spare.

---

## Prior art

Patterns were taken from Frappe Builder's palette
(`frontend/src/components/CommandPalette.vue` on `frappe/builder@develop`):
reka-ui `DialogRoot` with a manual `activeIndex` instead of headlessui, explicit
`inputRef.focus()` on open, the step-label button with chevron, the `esc` chip in
the input row, the bordered footer key chips, and a reserved
`max-h-[380px]`, no min-height — a single result shouldn't sit above 100px of
void. Rows track `mousemove`, not `mouseenter`: arrowing scrolls rows under a
stationary cursor, and hover would otherwise drag the highlight back to the
mouse.

Dropping headlessui also removed two workarounds this component needed while it
used `Combobox`: a `:key="depth"` remount to reset the input, and an `autofocus`
attribute that only fires on the dialog's initial open.

Behavioural direction came from Linear (context-first ordering, drill-down with
Backspace, shortcut hints on rows) and Raycast (fallback commands that receive
the typed text). Notably **Linear has no prefix grammar** — `>`/`#`/`@` is
GitHub's. Prefixes are a memorisation tax, so the only one kept is `#234`, which
this palette already taught users.

---

## Open items

Not done, deliberately or otherwise. The three known bugs listed here
previously — filtering resetting sort, filtering needing a default view, and the
watch-source type error — were fixed by the `ListViewBuilder` split above.

### Deliberately skipped

- **Delete ticket** — needs a confirm dialog, and `$dialog` is only reachable via
  `globalStore()`, which calls `getCurrentInstance()` and is unsafe from module
  scope. Marked with a `ponytail:` comment in `ticketCommands.ts`. The ticket
  header already offers it.
- **Sort from the palette** — `applySort` isn't reachable via the URL
  (`order_by` is not a route param). It's the one list action that would need a
  module-level registry, and a second mechanism isn't worth one command.
- **Bulk actions on selection** — the Linear-style win (select N, Cmd+K, act on
  all). The selection set only exists inside `ListSelectBanner`'s slot scope
  (`#actions="{ selections, unselectAll }"`); `ListViewBuilder` never holds it.
  Needs selection state lifted out of the banner — a real refactor.
- **Customer / Contact context** — worth adding as *pivots* ("Tickets from this
  customer", "New ticket for this contact"), not field edits. Those pages are
  lookup surfaces; their fields are low-frequency admin edits.
- **Merge / split ticket** — modal state is a local `ref` in `TicketHeader.vue` /
  `EmailArea.vue`, not module-level.
- **Search index fallback** — if the FTS index is missing, `search()` throws and
  the palette shows no rows (the "Search all of Helpdesk" fallback still routes
  somewhere). A `subject like` degradation would be needed for unindexed sites.
  Marked with a `ponytail:` comment in `useCommandPalette.ts`.
- **Mobile and customer portal** — palette is desktop-agent only, as before.

---

## Environment note

`desk/package.json` declares `"@framework/ui": "link:../../frappe/ui"`, but the
symlink did not exist in `node_modules` — `yarn build` failed on
`TicketField.vue` resolving `@framework/ui/components/Link/index.ts`. This was
confirmed pre-existing on a clean tree, unrelated to this change.

Worked around by creating the link manually:

```bash
mkdir -p desk/node_modules/@framework
ln -s "$(pwd)/../frappe/ui" desk/node_modules/@framework/ui
```

A proper `yarn install` in `desk/` is the real fix.

## Build and deploy

```bash
cd desk && yarn build                        # → helpdesk/public/desk
bench --site cc.localhost clear-website-cache
```

Then unregister the PWA service worker in the browser, or the old bundle keeps
being served.
