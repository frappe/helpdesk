# Command palette — improvements plan

Outstanding work on the `⌘K` palette, ranked. Everything here came out of a
design review, a PM review, and the two arguing with each other; items marked
**shipped** are done and listed only so the plan reads as a whole.

Verdict the plan was written against: the palette is **faster at triage,
unproven at scale, and untouched on replies.** Two of those three have moved —
§5 shipped, so replies are now `⌘K → type → ⏎` like everything else. Scale is
still untouched: §6 is the 300-ticket-queue item and it is deliberately later.

> **Blocked on Custom Side Panel:** §7 (flat rows for team and type) and §15
> (custom fields). Both hardcode a field set that feature is about to make
> configurable. Everything else in this plan is independent — see §15 for why
> waiting is the right call and what to do in the meantime.

---

## Shipped

| Change | Where |
|---|---|
| Customer-portal gate moved to the state, not the mount site | `useCommandPalette.ts` (`isPaletteAvailable`), `layouts/AppSidebar.vue` |
| Assign is add-only, never drops an existing assignee; activity log + `capture` parity with the popover | `ticketCommands.ts` (`assignTicket`) |
| "Assign to me" root row, hidden once you hold the ticket | `ticketCommands.ts` (`assignToMeCommand`) |
| Current value ticked on status / priority / team / type; no-op picks toast instead of closing silently | `optionCommands.ts`, `ticketCommands.ts` |
| Palette writes broadcast `notifyTicketUpdate` so co-viewers see them | `ticketCommands.ts` (`updateTicket`) |
| Highlight follows its row across async result arrival instead of resetting to 0 | `CommandPalette.vue` (`watch(groups)`) |
| Filters merge through the list's own `applyFilters` rather than a one-way URL write | `listViewFilters.ts`, `ListViewBuilder.vue`, `ticketListCommands.ts` |
| Flat option rows: typing `urgent` sets the priority, no drill-down | `ticketCommands.ts` (`flatOptionCommands`), `hideWhenEmpty` + `FLAT_OPTION_WEIGHT` |
| Context chip scopes the palette to the open ticket, with fallthrough to global | `useCommandPalette.ts` (`context`) |
| `esc` moved to the footer, labelled by what it actually does | `CommandPalette.vue` (`escapeLabel`) |
| **§9** scope ranks instead of gating; fallback pinned whenever the query is searchable | `useCommandPalette.ts` (`groups`, `fallback`) |
| **§2** `command_palette_opened` / `command_palette_command_run`; `source` on `ticket_assigned` and `saved_reply_applied` | `useCommandPalette.ts`, `ticketCommands.ts`, `AssignTo.vue`, `SavedRepliesSelectorModal.vue` |
| **§3 + §4** combobox/listbox/option roles, live region; keys bound to the dialog, not the input | `CommandPalette.vue` |
| **§15 "do now"** `FIELD_LABELS` replaced by `getMeta("HD Ticket")` | `ticketCommands.ts` (`fieldLabel`) |
| **§10** recents keyed by session user, old keys dropped from disk | `userStorage.ts`, `recentTickets.ts` |
| **§8** recent-commands MRU deleted; open ticket filtered out of recents | `recentTickets.ts`, `commands.ts` |
| **§5** saved replies: drill-down, per-agent frequency, top-3 flat at root | `savedReplyCommands.ts`, `savedReplyRanking.ts`, `replyComposer.ts` |
| **§11** `<mark>` runs, stale-not-blank results, loading bar, headers, per-level empty state, focus restore, Home/End + Ctrl+N/P, 640px, shortcuts row | `CommandPalette.vue`, `CommandPaletteRow.vue`, `paletteTypes.ts` |
| **§12** README trimmed 380 → 95 lines, two false claims corrected | `README.md` |
| `__()` accepts an array of replacements — `{1}` onwards had been silently dropped app-wide | `translation.ts` |

Covered by runnable checks (`node_modules/.bin/tsx <file>`):
`fuzzyScore.check.ts` (ranking, incl. flat-row vs parent in both directions, plus
`<mark>` run splitting), `savedReplyRanking.check.ts` (promotion thresholds, sort
stability, no mutation), `listViewFilters.check.ts` (merge, same-field replace,
clear, no-list fallback).

**Everything in "What can be done now" has shipped.** What remains below is the
"later" list, unchanged: §1 undo, §6 selection, §7 and §15 behind Custom Side
Panel, §13 SLA, §14 search cost.

---

## 1. Undo on every palette mutation

**Deferred — not now.** Built once and backed out; the design below is kept
intact so the rebuild is short whenever it is picked up.

The case for it: flat rows made a misfire one keystroke cheaper to cause and no
cheaper to reverse. That is a net-negative trade on trust, and it is why flat
rows and undo were originally scoped together. Nothing has changed about that
argument — the exposure stays open until this ships.

Every palette write fires and closes with a success toast: status, priority,
team, type, assign. Arrow one row too far, press Enter, and you have changed a
customer-visible field with no way back.

`toast` supports `action: { label, onClick }` (Sonner underneath). The blocker
is that `useTicket`'s shared `setValue.onSuccess` already toasts
`"Ticket updated successfully."` — a second toast from the palette would stack.

**Approach:** give the shared toast a stable id in `composables/useTicket.ts:35`
(`toast.success(msg, { id: "ticket-update" })`), then have `updateTicket` reuse
that id so Sonner updates the toast in place rather than adding one. The undo
handler writes the previous value back through the same `setValue` path.

Side benefit: repeated field edits stop stacking toasts app-wide.

### Already established — don't re-derive

This was built once and backed out to keep the branch small. Findings worth
keeping:

- **Callback order is favourable.** `frappe-ui/src/resources/resources.js:85` —
  `successFunctions = [options.onSuccess, tempOptions.onSuccess]`. The
  resource-level toast fires first, the per-call handler second, so re-raising
  the same id updates in place. No need to touch other `setValue` callers.
- **A local staleness guard is worthless here, and must be a refetch.**
  `TicketAgent.vue:202`'s `ticket_update` socket listener only calls
  `toast.info(...)` — it never reloads the doc. So after a co-viewer changes a
  field, `ticket.doc` still holds *our* value. A `doc[field] === applied` check
  passes and we overwrite their edit while looking careful. Undo must
  `await ticket.reload()` first, compare, then write or refuse with
  "Changed since — not undone." Same shape for assign via `assignees.reload()`.
- **Undo is per-command, not one branch.** Field writes revert through
  `setValue`; assign reverts through `helpdesk.api.doc.remove_assignments` and
  must also skip the activity-log entry when the agent is already gone,
  or it logs a false "unassigned".
- **Decided: toast action only, no `⌘Z`.** A scoped `⌘Z` was considered and
  rejected — the app has no undo stack, and it collides with ProseMirror's own
  undo in the reply box. Accepted cost: undo needs the mouse, which is a real
  wart on a keyboard-first feature.
- **Decided: one undo slot.** A shared toast id means a second edit replaces the
  first toast, so only the most recent write is undoable. Per-field ids would
  stack three toasts after three quick edits. Matches Linear.
- **8s duration.** Sonner's default is too short to notice a misfire and react.

## 2. Two `capture()` calls

There is not one telemetry call in the palette, while `AssignTo.vue` has one in
the very assign flow the palette duplicates. Until these exist, every ranking
and cut argument below is taste versus taste.

```ts
// openPalette()
capture("command_palette_opened", { data: { context: router.currentRoute.value.name } })
// run(), on the perform branch
capture("command_palette_command_run", {
  data: { command_id: command.id, query_length: query.value.length, depth: depth.value },
})
```

Three signals worth reading at two weeks:

1. **Open rate and `runs ÷ opens`.** Below 0.5 means agents open it, miss, and
   press Esc — which points at ranking or at the invisible fallback row (§9).
2. **Substitution, not addition.** Add a `source` property to the existing
   `ticket_assigned` capture so palette-sourced and dropdown-sourced writes land
   in one funnel. If dropdown usage stays flat while palette usage rises, the
   palette added a path without saving anyone time.
3. **Distance to intent.** Median `query_length` and `depth` at Enter. Long
   queries or depth ≥ 1 on a common action means the ranking is wrong.

## 3. Accessibility — restore what the rewrite removed

This is a **regression**, not a gap. The deleted `CP.vue` used headless-ui
`Combobox`, which supplied the roles for free. Dropping that dependency was
right (it forced a `:key="depth"` remount and broke autofocus), but the ~15
lines it was providing were never written back.

Today the list is plain `<div>`s: no `role="listbox"`, no `role="option"`, no
`aria-selected`, no `aria-activedescendant`, no live region. A screen-reader
user arrows ten times and hears nothing.

- input: `role="combobox" aria-expanded="true" aria-controls="cp-list"
  :aria-activedescendant="..."`
- list: `id="cp-list" role="listbox"`
- row: `role="option" :aria-selected="..."`, stable `:id`
- `<div aria-live="polite" class="sr-only">` for result counts and "No results"

`activeCommand` already exists to drive it. Ship with §4 — same file, same hour.

Helpdesk sells into public-sector and enterprise procurement where this is a
questionnaire gate, so it is commercial, not only ethical.

## 4. Tab escapes the keyboard handler

`@keydown` is bound to the `<input>` (`CommandPalette.vue:53`). Reka's focus
trap lets Tab move focus to the back button or the context chip, and from there
arrows and Enter do nothing — the user is stuck until Shift+Tab or Escape.

**Fix:** move `@keydown="onKeydown"` onto `DialogContent`. Keys then work
wherever focus sits inside the trap.

## 5. Saved replies in the palette

The gap that decides whether this is a shortcut or a workflow. Composing
replies is the bulk of an agent's day and the palette does not touch it —
`Reply to ticket` opens the box and you type the whole message.

Zendesk macros are the volume tool for repetitive requests. Helpdesk's nearest
equivalent is Saved Replies, whose only entry point today is a button inside
the email composer (`EmailEditor.vue`).

Add **"Saved Replies"** on the ticket context: drill into the saved
replies list, pick one, open the composer pre-filled. Not send-on-select — the
agent must see it before it goes to a customer.

### These stay a drill-down, unlike §7

Saved replies fail both flat-row tests, and not marginally. Cardinality is
unbounded — tens to hundreds per desk. Names are pure content ("Refund policy",
"Password reset steps"), so they collide with ticket search on essentially
every useful word.

The reframe that makes this fine: **a drill-down is a scoped search.** Once
inside the level, the query filters saved replies only, with zero collision
against tickets or commands. For an unbounded, content-named set that is the
correct shape, not a consolation. You pay one Enter and buy a clean namespace —
and the namespace is worth more here than it is for a four-value priority list.

**Worth stealing: a prefix to skip the Enter.** Slack's `/` model — typing `/`
drops straight into saved-reply scope without arrowing to a row first. Same
exclusive namespace, one keystroke instead of two. This is the version to build
if the plain drill-down feels slow in use.

### Top-N replies flat at root — ships with this, after §9

**Scheduled, not deferred.** Originally held back for §2 telemetry; decided to
build it alongside §5 instead. Two things make that safe rather than a guess:

**Hard dependency on §9.** Reply names are content-shaped — "Refund policy",
"Password reset". At root that is the same trap as §7: under today's scope rule
a single flat match suppresses global search, so a flat "Refund policy" row
would make "refund" stop finding refund tickets. §9 must land first. This is not
a preference; without it the feature removes search terms.

**Earn the row, don't guess it.** The telemetry question was "is usage
concentrated or long-tail" — substitute a threshold for the answer. Only promote
a reply to root once *this agent* has used it enough to prove it is part of
their core set (start at 5 uses, top 3 rows). An agent with a long-tail habit
never accumulates a qualifying reply and simply never sees root rows, which is
the correct outcome for them. No global tuning needed, and it degrades to
"nothing at root" rather than to noise.

Same rules as the other flat rows: `hideWhenEmpty`, composed titles
("Reply: Refund policy" — a bare "Refund policy" reads as a ticket), and
`FLAT_OPTION_WEIGHT` so they rank below the drill-down parent.

§2 is still worth having first — it tells you whether the threshold is right —
but it is no longer a blocker.

### Order the list by the agent's own usage

**Decided: frequency**, per-agent, most-used first. Build it with the feature —
it is a few lines and it is the difference between scanning 50 rows and reading
the top 3.

**The one rule that decides whether this feels smart or possessed: usage orders
the list only on an empty query. Once the agent types, the match wins and usage
is a tie-breaker only.** Type "refund" and you get the refund reply, never the
most-used reply that happens to fuzzy-match it. Concretely, `scoreCommand`
stays authoritative and usage separates rows that score equally — do not fold a
usage bonus into the score itself.

**One list, re-sorted — not a separate "Recently used" group.** This is the §8
lesson applied: with ~8 visible rows, a duplicate group spends three of them
showing what is also right below. §8 is a deletion precisely because it did that
over a corpus where ordering did not matter.

**Why an MRU is right here when §8 says delete one.** Not a contradiction, and
worth writing down: the command MRU covered ~15 commands that were all visible
anyway. Saved replies are 50–200 with ~8 on screen, so ordering genuinely
determines what an agent sees, and support work is repetitive enough that
concentration is real. The signal has a job here that it never had there.

**Known limitation of frequency, and the upgrade path.** Frequency describes the
stable core set but does not adapt to what the agent is doing right now — five
password resets in a row will not promote that reply until its count catches up.
Frecency (frequency with recency decay) fixes it. Ship frequency, and revisit
only if agents report the batching case; do not build the decay up front.

**Storage: localStorage, keyed by user id from day one.** Do not repeat §10,
where the scoping was an afterthought. Real limitation: it is per-device, and
support desks hot-desk — if that bites, move to a per-agent usage record
server-side. Note that a counter on `HD Saved Reply` is *not* the same thing;
that answers a team-wide question, not a personal one.

**Cold start is worth the few lines.** A new agent has no history and is exactly
the person who does not know which replies exist. If a global usage count is
available, seed their order from the team's most-used until they build their own.

## 6. Act on the current selection

`⌘K` with N tickets selected should act on all N. This is what makes a palette
worth building for a 300-ticket queue; everything today is one ticket at a time.

Out of v1 because selection state lives inside `ListSelectBanner`'s slot scope.
`listViewFilters.ts` is now the precedent for publishing list state
module-scope — do the same for selection.

## 7. Flat rows for team and type — after §9, not before

`flatOptionCommands` covers status and priority only. Team and type are the same
shape of action and should get the same `titlePrefix` + `hideWhenEmpty` +
`FLAT_OPTION_WEIGHT` treatment, so an agent never has to remember which fields
are fast. Consistency is the case for doing it.

**Sequencing is the whole point of this item.** Team and type values are
content-shaped words — "Billing", "Infrastructure", "Bug", "Question" — and
those are exactly what an agent types when *searching*. Under today's scope rule
(§9a) a single flat match suppresses global search, so `Set team: Billing` would
make "billing" stop finding billing tickets. Fix the suppression first; then
this is safe and the flat row simply ranks above the search hits instead of
replacing them.

### Two arguments against this that do not hold

Recording these so they are not re-litigated:

- **"Teams are unbounded, the list will flood."** No. `hideWhenEmpty` keeps them
  out of the empty palette, and once you type only matching teams render.
  Thirty teams produce however many match `bil`, not thirty rows.
- **"Type is rarely changed, so it is not worth a row."** An assumption, never
  measured. Plenty of desks categorise on every triage. §2 telemetry answers
  this — ship type flat and read `command_palette_command_run` rather than
  arguing it.

**Watch out:** teams and ticket types are `createListResource`, not stores, so
the root build must not block on a fetch. Render them only once `.data` is
present. Statuses and priorities are pinia stores with `auto: true`, which is
why the existing flat rows did not hit this.

Keep the drill-down parents in all cases — they are how someone who does not
know the option names discovers them. Raycast does both.

## 8. Delete the recent-commands MRU

Not a fix — a deletion. It is broken four ways in four lines, over a corpus of
~15 commands where an MRU has no job:

- every leaf run is tracked, including `search-HD Ticket-1234` ids
- the window is 3 slots, so three ticket opens empty it permanently
- ids resolve only against `always`, so misses are silently dropped
- drill-down commands never enter it, excluding the five most-used actions

Remove `trackRecentCommand`, `recentCommandIds` and `recentlyRunCommands`.
**Keep recent tickets** — an agent bounces between ~5 tickets a session and it
is the only zero-typing action in the product. Deleting the MRU also buys back
three rows for §11.

While there: `recentTicketCommands` (`commands.ts:78`) lists the ticket you are
currently reading as its own top row. Filter it out.

## 9. Scope must never suppress search — prerequisite for §7

**This gates §7. Do it first.**

Two separate things make a query dead-end, and together they hide whole classes
of search term.

**a. A scoped match suppresses global results entirely.**

```ts
if (context.value) {
  const scoped = groupCommands(ticketCommands(context.value.id), query.value)...
  if (scoped.length || !query.value.trim()) return scoped;   // early return
}
const built = groupCommands(globalCommands(), query.value);  // search lives here
```

One matching ticket command and global search never runs. Not outranked —
suppressed. **This is already a live bug**, shipped with the flat option rows:
type `open` on a ticket and `Set status: Open` matches, so a ticket whose
subject contains "open" is unreachable without dismissing the chip first. It is
narrow today only because status and priority words are rarely what an agent
searches for. It stops being narrow the moment team and type go flat, which is
why §7 cannot land before this.

**Fix:** scope should *rank*, not *gate*. Always build the global list and
append it below the scoped rows, rather than returning early. Scoped rows
already outrank via `CONTEXT_WEIGHT`, so the ordering people want survives —
what changes is that the search results still exist underneath.

**b. The fallback row is effectively never rendered.**

`buildFallbackCommands` only fires when nothing at all matched
(`useCommandPalette.ts:148`). Because `fuzzyScore` does subsequence matching,
almost any real word matches *something*, so the escape hatch stays hidden
exactly when it is needed. Append it as the last group whenever
`query.length >= 2`. Raycast pins its fallback for this reason.

Related: `title_only: true` means the palette searches ticket **subjects only**,
so a phrase from an email body returns a confident `No results` while the
dedicated search page would have found it. The pinned fallback is what makes
that survivable.

## 10. User-scope the recents storage

`recentTickets.ts:10-11` uses bare `hd_recent_tickets` / `hd_recent_commands`
keys, and `stores/auth.ts` `logout()` clears neither. Ticket **subjects** are
stored, and they routinely carry customer names. Shift handover on a shared
support machine leaks them to the next agent.

Suffix both keys with the user id, or clear them on logout. Ten minutes.

## 11. Polish batch

Ship as one pass, after the above.

- **Motion.** No open/close transition; it is the only dialog in the app
  without one (frappe-ui's own `Dialog` fades and scales `0.98 → 1`). Reka
  stamps `data-state`, so it is a Tailwind one-liner —
  `tailwindcss-animate` already ships with the preset. ~120–150ms.
- **Keep matched text bold.** `stripTags` (`paletteTypes.ts:56`) throws away
  the `<mark>` the FTS server already computed, so search rows never show *why*
  they matched. Split on `<mark>…</mark>` and render the runs as text nodes —
  no `v-html`, no sanitiser.
- **Stale results, not empty ones.** `onQueryChange` clears synchronously then
  debounces 200ms, so the list blanks on every keystroke and the panel resizes
  under the cursor. Keep the previous results until the new ones land, and add
  `min-h` to the list container.
- **Loading is invisible mid-list.** `isLoading` only surfaces when the list is
  empty, so a drill-down on a cold store shows 300ms of nothing. Add a 2px
  indeterminate bar under the input, independent of `flatItems.length`.
- **Group headers.** `text-sm` against `text-sm` rows — only colour separates
  structure from content. Go `text-xs font-medium uppercase tracking-wide`.
- **Per-level empty state.** A drilled-in level with no children shows the
  root's "No commands found", which is false. "No tags left to add" is the
  honest string.
- **Focus restore.** There is no `DialogTrigger`, so on close focus lands on
  `<body>` and a keyboard user loses their place. Capture `document.activeElement`
  on open and restore it, unless the command took focus itself.
- **Missing keys.** No Home/End, no `Ctrl+N`/`Ctrl+P`. Four lines in `onKeydown`.
- **Width.** `max-w-[560px]` truncates ticket subjects around 40 chars. Raycast
  is 750, Linear ~640. Go 640.
- **Self-reference.** No "Keyboard shortcuts" row despite `⌘/` existing. The
  palette is the discovery surface for the shortcut system; it should point at it.

## 12. Trim the README

380 lines, and it is a liability rather than documentation: it asserts the
palette is not rendered in the customer portal (it was not guarded until
recently) and that `title_only` is a title-search fast path (it changes the
SELECT clause, not only the MATCH). Both claims were cited by reviewers *instead
of* reading the code.

Keep ~80 lines: the `Command` shape, the contexts, the ranking rules, and the
three non-obvious decisions (module-scope singleton, frappe-ui `useShortcut`
over the local one, list-state-over-URL for filters). The branch history and
the hardcoded `bench --site` commands belong in the PR description.

## 13. SLA — a real gap, deliberately deferred

Nothing in the palette touches SLA: no time-to-first-response, no escalate, no
breach filter, despite SLA Policies being a settings section the palette links
to. "Show tickets breaching SLA" on the list route would likely be the
most-used filter available. Jira Service Management sets the bar here.

## 14. Search cost per keystroke (watch, don't fix yet)

`helpdesk/search_sqlite.py` runs `frappe.get_list("HD Ticket", pluck="name")`
with no limit on every search call, feeding a SQLite `IN (...)`. That was fine
when search was a page you visited deliberately; `⌘K` is now global with a
200ms debounce, making it a per-typing-burst permission scan of the ticket
table.

Not a blocker at 5k tickets. A real problem at 200k. Cap the list or push
permission filtering into the index at build time.

## 15. Custom fields — blocked on Custom Side Panel

**Do not build this before the Custom Side Panel feature lands.** Not because it
is hard, but because that feature is the source of truth this should derive
from, and building first means building twice.

### The situation

Helpdesk already supports custom fields on `HD Ticket`
(`customizations.data.custom_fields`, with `getMeta("HD Ticket")` supplying
label / fieldtype / options). `TicketDetailsTab.vue:182` renders them
dynamically. The palette hardcodes four fields and is blind to everything else.

Custom Side Panel makes this worse *and* fixes it: per-site configurable panels
mean a site may drop `ticket_type` entirely, or relabel it to "Category". The
palette would then offer "Change type" for a field that does not exist, or
announce "Team" over the socket while the UI says "Squad".

### Why waiting is right, and what it buys

The palette's best structural property is that nav comes from
`agentPortalSidebarOptions` and settings from `settingsTabs` — derived, never
copied, so they cannot drift. The side panel config is that same kind of source
of truth for ticket fields. Consume it and you get, with no ongoing maintenance:

- relabel Type → Category, and `⌘K` says "Change category"
- remove a field, its row disappears
- add a custom Select, its row appears

Nobody in the category does this. Zendesk has the deepest custom-field support
and zero palette coverage of them; Jira's palette does navigation and search,
not arbitrary field edits. Configurability is the reason Helpdesk *can*.

### The architectural limit: no input step

`Command` is `children: () => Command[]` — pick from a list. There is no way to
type a value. So the split is fixed, whatever the side panel does:

- **Expressible today:** `Select`, and `Link` to a bounded doctype. Both become
  drill-downs.
- **Not expressible:** `Data`, `Date`, `Int`, `Currency`, `Small Text`. These
  need a "type a value" level the palette cannot represent. Real feature, not a
  tweak — defer explicitly rather than half-supporting it.

Custom fields should be **drill-down, not flat**, regardless of §7: admin-defined
names are arbitrary and collide with everything.

### What the side panel API must expose

Time-sensitive — once it ships as component-level config this is hard to change.
Per field, as plain data:

- `fieldname`, `label`, `fieldtype`, `options`
- **editability, not just visibility.** A field shown in the panel may be
  read-only; one hidden from it may still be editable. If the contract only says
  "render this", the palette offers rows that fail on save — silently, because
  `setValue` errors land in a toast after the palette has already closed.
- `depends_on`, or the palette needs its own `parseField` pass like
  `TicketDetailsTab` does, or it will offer conditionally-hidden fields.

Open question for that feature's design, since the palette inherits the answer:
**is the config per-site only, or per team/role?** If role-scoped, the palette
must apply the same scoping.

### Do now, independent of the wait

**Kill `FIELD_LABELS`** in `ticketCommands.ts`. It is already a hardcoded copy of
`getField(fieldname).label`, and it becomes wrong the day relabelling ships.
`getMeta` is safe from module scope — `tiptap-extensions.ts:26` already calls it
that way. Small, and correct regardless of how the side panel lands.

---

## What was done now — all shipped

Nothing here touched a configurable field, so none of it waited on Custom Side
Panel. Built in this order, one commit each.

| # | Item | Outcome |
|---|---|---|
| 1 | **§9** scope must not suppress search | Scope appends the global list below the scoped rows instead of returning early; fallback pinned once the query is searchable. |
| 2 | **§2** two `capture()` calls | Plus `source` on `ticket_assigned` and `saved_reply_applied`. The popover's existing call was passing the wrong shape and had been reporting no properties at all. |
| 3 | **§3 + §4** ARIA and the Tab trap | Rows carry their flat index, which supplies the option id and replaces identity comparison. Enter on a focused button is left alone so it does not double-fire. |
| 4 | **§15 "do now"** kill `FIELD_LABELS` | Broadcast label from `getMeta`. Row titles stay literal — `getField` is null until meta lands, so deriving them would flash `Change agent_group`. |
| 5 | **§10** user-scope recents keys | `userStorage.ts` reads the session cookie, since this runs before pinia. Old unscoped keys are also dropped from disk. |
| 6 | **§8** delete the recent-commands MRU | Plus the open ticket no longer lists itself in recents. |
| 7 | **§5** saved replies | Drill-down + per-agent frequency, with `replyComposer.ts` as the module-scope channel to the composer. |
| 7b | **§5** top-N replies flat at root | 5 uses, top 3. Titles stored with the counts, so a root row costs no fetch and cannot block the root build. |
| 8 | **§11** polish batch, **§12** README trim | Ten polish items; README 380 → 95 lines with two false claims corrected. |
| — | `__()` array replacements | Not in the plan. Surfaced as the last type errors in the palette: ~50 call sites pass one array, so `{1}` onwards was silently dropped app-wide. Fixed at the source; repo `tsc` errors 952 → 709. |

**§2 is now collecting.** It was supposed to tell you whether the "5 uses"
promotion threshold is right, so that number is the first thing to revisit once
there is data. §7's "type is rarely changed" argument is also waiting on it.

---

## What will be done later

### Blocked on Custom Side Panel

Both hardcode a field set that feature is about to make configurable. Building
first means building twice.

| # | Item | Unblocks when |
|---|---|---|
| **§7** | Flat rows for team and type | Custom Side Panel lands **and** §9 is done. Two dependencies, both hard. |
| **§15** | Custom fields in the palette | Custom Side Panel exposes fields as plain data — `fieldname`, `label`, `fieldtype`, `options`, **editability**, `depends_on`. |

**Time-sensitive, and not a palette task:** that API shape has to be settled
while Custom Side Panel is still being designed. Specifically it must express
*editability*, not only visibility — otherwise the palette will offer rows that
fail on save, silently, because the error toast arrives after the palette has
closed. Raise it there, not here.

### Deferred by choice

| # | Item | Waiting on |
|---|---|---|
| **§1** | Undo on palette mutations | Nothing technical — a scheduling call. It was built once and backed out, and §1 keeps every finding from that build (shared toast id, mandatory refetch, one undo slot), so the rebuild is short whenever it comes back. |
| **§6** | Act on the current selection | The v2 headline. Needs list selection published module-scope, the way `listViewFilters.ts` now does for filters. |
| **§13** | SLA commands | A real gap. Needs product input on which SLA actions belong in a palette. |
| **§14** | Search permission-scan cost | Watch only. Fine at 5k tickets, a problem at 200k. Revisit when a large site appears. |
| — | Input step for freeform custom fields | `Command` is pick-from-a-list only. `Data`/`Date`/`Currency` need a new level type. Real feature, not a tweak. |

---

## Hard dependencies

Only three, and they are the ones that break something if ignored.

- ~~**§9 → §5 top-N root rows.**~~ Satisfied: §9 shipped first, so the root rows
  rank above search hits instead of replacing them.
- **§9 → §7.** Satisfied on the §9 side. §7 still waits on Custom Side Panel.
- **Custom Side Panel → §7, §15.** Both hardcode a field set that feature makes
  configurable. Still open, and still the only hard dependency left.
