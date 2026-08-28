# Command Palette (Cmd/Ctrl + K)

Leads with the actions for whatever you're looking at — on a ticket, that
ticket's actions behind a removable context chip; on the ticket list, that list's
filters and views — then falls back to search, recents and navigation.

Mounted once, in `layouts/AppSidebar.vue`. Desktop agent portal only: the gate is
`isPaletteAvailable` in `useCommandPalette.ts`, which lives with the state rather
than the mount site because AppSidebar is shared with the customer portal.

## The `Command` shape

```ts
interface Command {
  id: string
  title: string            // plain text; this is what gets scored and read out
  group: string
  icon?: Component
  iconProps?: Record<string, unknown>   // props for data-driven icons
  subtitle?: string        // muted right-aligned text
  keywords?: string        // matched at a scoring penalty
  hint?: string            // combo string, e.g. "Mod+."
  weight?: number          // multiplies fuzzy score; <1 sinks a row
  dotClass?: string        // leading colour dot (status rows)
  rank?: number            // fixed score, bypasses the scorer
  marked?: string          // server's <mark> highlighting; rendered as text runs
  checked?: boolean        // trailing tick: this value is already set
  keepOpen?: boolean       // perform, then pop back a level; optimistic tick
  hideWhenEmpty?: boolean  // flat option rows, hidden until the user types
  children?: () => Command[] | Promise<Command[]>   // drill-down
  perform?: () => void
}
```

A command either drills in (`children`) or acts (`perform`); `run()` picks based
on which is present. `keepOpen` is the third path, for toggle rows (tags): the
tick flips before the write returns and flips back if it throws; on success the
palette pops back to the parent level instead of closing.

**Only set `hint` when the key reaches the same end result as the row** — not when
it reaches it the same way. Hinted keys are *page* shortcuts and are inert while
the palette is open, which is what stops `s`/`p`/`a` firing as you type. The chip
teaches the key for next time; it is not an accelerator for this dialog.

## Ranking

`fuzzyScore(text, term)` — prefix (1000) beats word-boundary substring beats
mid-word substring beats scattered subsequence; `-1` means no match.

- **`rank`** wins outright: server hits arrive relevance-ordered from SQLite BM25
  and are not re-scored locally.
- **`weight`** multiplies. `CONTEXT_WEIGHT = 1.2` puts ticket rows above search
  hits deliberately rather than by luck; `FLAT_OPTION_WEIGHT = 1.15` keeps
  "Set priority: Urgent" under the "Change priority" parent; nav links use `0.7`
  so they sink once you have typed something real.
- Scope **ranks, it never gates**: scoped rows are appended above the global list,
  not returned instead of it. Returning early made a ticket whose subject
  contains "open" unreachable, because `Set status: Open` matched.
- On an empty query every score is 0, which is why `hideWhenEmpty` exists — a low
  weight cannot separate rows that all tie.

## Three decisions worth knowing

**State is module-scope**, in `useCommandPalette.ts`, not in the component. That
is what lets the sidebar button, `Cmd+K` and the dialog drive one instance.
`paletteTypes.ts` exists only to break the cycle between the engine and the
command modules.

**The shortcut uses `useShortcut` from `frappe-ui`, not `@/composables/shortcuts`.**
The local one bails whenever focus is in an input or inside `[role="dialog"]`, so
`Cmd+K` could neither open from a filter box nor close the palette once open. A
`condition` bows out inside `.ProseMirror`, which binds `Mod-k` for insert-link.

**List and composer state is published module-scope, not routed through the URL.**
The palette sits outside `ListViewBuilder`'s and `EmailEditor`'s provide chains,
so it cannot inject. `listViewFilters.ts` and `modalStates.ts` each hold a
`shallowRef` the mounted component fills in and clears on unmount, and the
palette handles their absence. Filters merge through the list's own
`applyFilters`, which preserves sort, columns and the active view — an earlier
URL-write approach reset the user's sort on every filter.

## Search

The existing SQLite FTS5 index, via `helpdesk.api.search.search`. 200 ms
debounce, minimum 2 characters, stale responses dropped by an incrementing token,
results sliced to 6 client-side.

`title_only: true` narrows the **SELECT clause**, not the MATCH — so it returns
subjects rather than restricting where the term is looked for. A body phrase can
still produce `No results` in the palette, which is why the `Search for "…"`
fallback is pinned below the results whenever the query is long enough
to search, instead of appearing only when nothing matched. Subsequence matching
means something almost always matched, so the escape hatch used to stay hidden
exactly when it was needed.

Next to it sits `Create ticket "…"`, which lands on the new-ticket page with the
subject pre-filled from the query — suppressed for `#`-prefixed queries, since
`#123` is someone reaching for a ticket, not naming one.

## Telemetry

| Event | Payload | When |
|---|---|---|
| `command_palette_opened` | `context`: current route name | Every open — all paths route through `openPalette()`, so the count is honest |
| `command_palette_command_run` | `command_id`, `query_length`, `depth` | A leaf command executes, tag toggles included; drilling into a sub-list is not captured |
| `ticket_assigned` | `doctype`, `source: "command_palette"` | Assigning an agent via the Assign-to drill-down |
| `saved_reply_applied` | `source: "command_palette"` or `"composer"` | Applying a saved reply; each surface tags its own source so the funnels are separable |

`context` says *where* people reach for the palette, `query_length` separates
browsed-to from searched-for, `depth` says whether drill-downs get used, and
`source` compares the palette against the pre-existing UI for the same action.
Closes, chip dismissals and abandoned opens are not captured — "opened but ran
nothing" is only inferable by differencing the first two counts.

## Checks

No test runner in `desk/`; each pure module leaves a runnable assertion file.

```bash
cd desk && ../node_modules/.bin/tsx src/components/command-palette/fuzzyScore.check.ts
cd desk && ../node_modules/.bin/tsx src/components/command-palette/savedReplyRanking.check.ts
cd desk && ../node_modules/.bin/tsx src/components/listViewFilters.check.ts
```
