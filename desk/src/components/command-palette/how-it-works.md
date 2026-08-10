# How the Command Palette Works

One sentence: **the palette is a single module-scope state machine
(`useCommandPalette.ts`) that turns `query` + `stack` + `context` into a ranked
list of `Command` objects, and `run()` decides what Enter does — perform,
drill in, or toggle.**

All paths are under `desk/src/components/command-palette/`.

## The cast

| File | Job |
|---|---|
| `useCommandPalette.ts` | The engine. All state, ranking, `run()`, server search. |
| `CommandPalette.vue` | The dialog. Renders `groups`, owns keyboard/mouse, calls `run()`. |
| `CommandPaletteRow.vue` | One row: icon, title, tick, hint. |
| `paletteTypes.ts` | The `Command` interface + shared constants. Exists to break import cycles. |
| `commands.ts` | Global root commands (nav, create, account, recents, `#123` jump). |
| `ticketCommands.ts` | Commands scoped to the open ticket (status, priority, assign…). |
| `tagCommands.ts` | The tag toggle list (the `keepOpen` case). |
| `searchCommands.ts` | Turns server FTS hits into `Command` rows. |
| `fuzzyScore.ts` | The local scorer. |

## State (module scope, not component scope)

`useCommandPalette.ts:20-39` — everything lives at module level so the sidebar
button, `Cmd+K`, and the dialog all drive **one** instance:

```ts
export const isOpen = ref(false);
export const query = ref("");
const stack = shallowRef<Level[]>([]);   // drill-down levels, empty = root
```

Three values decide what you see:

- **`query`** — what you typed.
- **`stack`** — a stack of `Level`s. Empty stack = root list. "Change status" →
  pushes a level whose commands are the status options. Backspace pops it
  (`back()`, `useCommandPalette.ts:98`).
- **`context`** (`useCommandPalette.ts:59`) — the ticket you have open, derived
  from the route (never stored, so it can't go stale). Non-null means the chip
  is up and ticket commands are prepended.

## The list: `groups` (useCommandPalette.ts:173)

A single computed produces everything on screen. In order:

1. **Inside a level?** Just score and group that level's commands. Done.
2. **At root with a chip?** Build `ticketCommands(context.id)` as untitled
   scoped groups.
3. **Empty query + chip** → scoped rows, then recents.
   **Empty query, no chip** → the global root (`buildRootCommands` + search).
4. **Typed query** → `[...scoped, ...global, ...fallback]`. Scope **ranks but
   never gates**: scoped rows win via `CONTEXT_WEIGHT = 1.2`
   (`paletteTypes.ts:92`), but global search stays reachable underneath.
5. **Fallback** (`useCommandPalette.ts:212`) — `Search for "…"` and
   `Create ticket "…"` are *pinned* under any query ≥ 2 chars, not shown only
   when nothing matched (subsequence matching means something almost always
   matches, so a last-resort fallback would never appear).

Ranking inside `groupCommands` (`useCommandPalette.ts:226`): each command gets
`scoreCommand(command, term)` — prefix beats word-boundary beats mid-word beats
scattered subsequence (`fuzzyScore.ts`), `keywords` match at a penalty,
`weight` multiplies, `rank` (server hits) bypasses scoring entirely. Sort,
bucket by `group`, render.

`flatItems` (`useCommandPalette.ts:246`) flattens the groups back into one
array — that's what arrow keys and Enter index into
(`CommandPalette.vue:313`):

```ts
const command = flatItems.value[activeIndex.value];
run(command);
```

## Enter: `run()` (useCommandPalette.ts:112)

```ts
if (!command || running) return;      // double-Enter guard
if (command.children) { ...push a level... return; }
if (command.keepOpen)  { ...toggle, back()... return; }
closePalette();
command.perform?.();                  // the plain case
```

A command declares which path it takes by shape: `perform` only → act and
close; `children` → drill in; `keepOpen + perform` → act, then pop back a level.

---

## Example 1 — no nesting: "Toggle theme"

Defined in `commands.ts:130`:

```ts
{
  id: "toggle-theme",
  title: __("Toggle theme"),
  group: GROUP.account,
  icon: currentTheme.value === "dark" ? LucideSun : LucideMoon,
  keywords: "dark light appearance",
  perform: () => toggleTheme(),
}
```

Full trace of `⌘K → "them" → Enter`:

1. `Cmd+K` → `openPalette()` (`useCommandPalette.ts:78`) sets `isOpen = true`
   (and logs telemetry).
2. Each keystroke → `onQueryChange("them")` (`useCommandPalette.ts:284`) →
   `groups` recomputes → `fuzzyScore("Toggle theme", "them")` gives a
   word-boundary match → the row surfaces near the top.
3. Enter → `CommandPalette.vue:313` → `run(command)`.
4. No `children`, no `keepOpen` → `closePalette(); command.perform()` →
   theme flips. **The palette closes first** so the action lands on a clean
   screen.

`Set status: Open` (a *flat option row*, `ticketCommands.ts:256`) is the same
non-nested path — it exists so typing "open" sets the status in one Enter
without visiting the drill-down. It's `hideWhenEmpty` (`paletteTypes.ts:36`)
because on an empty query every score is 0 and weights can't separate ties.

## Example 2 — nested: "Change status" → "Open"

Defined in `ticketCommands.ts:56`:

```ts
{
  title: __("Change status"),
  ...
  children: () => statusChildren(ticketId),   // ← makes it a drill-down
}
```

Trace of `⌘K → "status" → Enter → "op" → Enter` on ticket #247:

1. Root list: "Change status" wins (scoped, ×1.2 weight).
2. Enter → `run()` sees `children` → sets `loadingChildren` (drives the 2px
   loading bar), awaits `statusChildren("247")`
   (`ticketCommands.ts:270`), which builds one `Command` per status, the
   current one carrying `checked: true`.
3. Pushes `{ title: "Change status", commands }` onto `stack`, clears the
   query. `groups` now takes branch 1 (inside a level) — you see only
   statuses; the breadcrumb shows where you are.
4. Type "op" → same scorer, now over 5 rows instead of the whole world.
5. Enter on "Open" → that row has only `perform` → **Example 1's path**:
   close, write the status.
6. Backspace on an empty query instead? `back()` pops the level and you're at
   the root again.

So nesting is nothing special: a parent whose `children()` returns more
commands, and a stack the UI renders the top of. Leaf rows are ordinary
non-nested commands.

## Example 3 — nested + `keepOpen`: Tags

Toggling a tag shouldn't close the palette — but once it lands you're done
with the list, so the palette pops back to the ticket's commands.
`tagCommands.ts:20`:

```ts
{
  id: `tag-${tag.name}`,
  checked: applied.has(tag.name),   // tick = currently on the ticket
  keepOpen: true,                   // ← don't close on Enter
  perform: () => toggleTag(ticketId, tag),
}
```

Trace of Enter on "billing":

1. `run()` takes the `keepOpen` branch (`useCommandPalette.ts:139`):
   `flipChecked(command)` flips the tick **immediately** — optimistic, no
   waiting on the network.
2. `await command.perform()` → one API call, `update_tags`, whose response
   already carries the new `_user_tags`, so the ticket doc is patched from it
   — no second fetch.
3. If the write **fails**: `perform` re-throws, `run()`'s catch calls
   `flipChecked` again — the tick reverts, a toast explains.
4. On success `back()` pops the tag list — you land on the ticket's commands,
   palette still open. On failure you stay in the list to retry.

## How context is given

Context is **never set by anyone — it is derived**. There is no
`setContext()` call anywhere. `context` is a computed
(`useCommandPalette.ts:59`) that looks at the router every time it's read:

```ts
export const context = computed<PaletteContext | null>(() => {
  if (contextDismissed.value) return null;        // the one manual override
  const route = router.currentRoute.value;
  if (route.name !== "TicketAgent") return null;  // only ticket pages scope
  const id = String(route.params.ticketId);
  return { id, label: `#${id}`, title: useTicket(id).ticket.doc?.subject ?? "" };
});
```

So "giving" context = **being on the route**. Open ticket #247 → the route is
`TicketAgent` with `ticketId=247` → `context` is
`{ id: "247", label: "#247", title: "Email sync broken" }`. Navigate to the
ticket list → the computed re-evaluates → `null`. The palette never has to
clean up after a navigation it didn't cause, because nothing was stored to go
stale — that's why it's derived instead of set.

The only mutable piece is `contextDismissed` (`useCommandPalette.ts:52`), a
boolean veto. Backspace on an empty query at root calls `dismissContext()`
(`:72`) → veto on → computed returns `null` → chip gone, list widens to the
global root. Closing the palette runs `resetPalette()` (`:92`), which clears
the veto — next open on a ticket page, the chip is back.

What consumes it:

1. **`groups`** (`useCommandPalette.ts:183`) — non-null context prepends
   `ticketCommands(context.id)` as untitled groups (the chip already names the
   ticket, so a "Ticket" header would repeat it). Each scoped row carries
   `weight: CONTEXT_WEIGHT` (1.2, `paletteTypes.ts:92`) — that's *how* scoped
   rows lead once you type: they outrank, they don't exclude.
2. **The chip** (`CommandPalette.vue:24`) — renders `label + title` above the
   input. Inert by design; removal is Backspace, advertised by the footer's
   esc label.
3. **The command builders** — `ticketCommands(ticketId)` closes over the id,
   so every `perform` ("Set status", "Assign to me", tag toggles) knows which
   document to write without any global "current ticket" variable.

To scope a future page the same way (say a customer page), the extension point
is this one computed: return a `PaletteContext` for `route.name ===
"CustomerAgent"` too, and hand `groups` a matching command builder. (Distinct
from the `routeCommands` map in `commands.ts`, which mixes extra rows into the
global list without the chip posture.)

## Scoring, in detail (fuzzyScore.ts)

Two layers: `scoreCommand` decides **which fields** of a command compete;
`fuzzyScore` decides **how well one string matches** the term.

### Layer 1 — `scoreCommand` (fuzzyScore.ts:9)

```ts
if (command.rank !== undefined) return command.rank;  // server hits: pre-ranked, skip scoring
const base = Math.max(
  fuzzyScore(title, term),
  fuzzyScore(keywords, term) - 50,    // a title match always beats a keyword tie
  fuzzyScore(subtitle, term) - 100,
);
return base * (command.weight ?? 1);  // nav 0.7 sinks, context 1.2 lifts
```

The row's score is the **best field minus that field's penalty, times weight**.
`groupCommands` (`useCommandPalette.ts:226`) then drops rows scoring `< 0` and
sorts descending; ties keep source order (`a.index - b.index`).

### Layer 2 — `fuzzyScore` (fuzzyScore.ts:26): three match classes

| Class | Score | Example for term `con` |
|---|---|---|
| Prefix | `1000` | `Contacts` |
| Substring | `900 − offset` (+60 if it starts a word) | `configure` inside Settings' keywords → 900 − 12 + 60 = **948** |
| Scattered subsequence | `400 + 20·longestStreak − gaps` (gaps capped at 200) | see below |
| No match | `−1` (row filtered out) | `Settings` title for `con` |

### How letters are "stored": they aren't

There's no trie, no index, no preprocessing. Both strings are lowercased per
call and the needle is walked left-to-right over the haystack with plain
`indexOf`, carrying four counters:

```ts
let position = 0;   // where in the haystack the next letter may start
let streak = 0;     // current run of consecutive hits
let longestStreak;  // best run seen (rewards clustered letters)
let gaps = 0;       // total characters skipped over (punishes scatter)
```

Each needle letter must be found **at or after** `position` — that's what makes
it an *in-order* subsequence, not a bag of letters. Any letter missing → `-1`.
This is O(needle × haystack) per row, which is nothing: the palette scores
~50 short strings per keystroke. Storing anything smarter would be solving a
problem the input size doesn't have.

### Worked example: why "cont" showed Settings under Contacts

Settings has `keywords: "preferences configure email agents teams sla telephony"`.

Term `cont`, walking the keywords (`·` = skipped, counted into `gaps`):

```
preferen c es  c on figure email agen t s ...
         ↑c    ↑o↑n (streak 1)      ↑t
gaps: 8 (before c) + 4 (to o) + 17 (to t) = 29
score: 400 + 20·1 − 29 = 391 → keyword penalty −50 → 341
```

Contacts: `cont` is a prefix of the title → 1000, × nav weight 0.7 = **700**.
So the list reads Contacts (700) above Settings (341) — both visible, because
a weak match is still a match. One keystroke earlier (`con`) the order was
*reversed*: Settings scored 948 − 50 = **898** via the `configure` substring,
beating Contacts' 700 — which is why the highlight was sitting on Settings,
and the follow-the-row watch (`CommandPalette.vue:388`) kept it there as the
row sank.

## Server search, in one paragraph

Typing ≥2 chars at root fires `onQueryChange` → 200ms debounce →
`helpdesk.api.search.search` (SQLite FTS5). An incrementing token
(`useCommandPalette.ts:266`) drops stale responses; old rows are deliberately
kept on screen during the debounce so the panel never blanks between
keystrokes. Hits arrive BM25-ranked and carry `rank`, bypassing the local
scorer; `<mark>` highlights are split into text runs (`paletteTypes.ts:81`) —
never `v-html`.
