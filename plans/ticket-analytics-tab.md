# Plan: Per-Ticket "Analytics" Tab

Branch: `feat/ticket-analysis` (off `develop` @ `563d22a20`). Desktop only for v1.

Design source of truth: Figma file `1O9g7yTXrouZbWnXIzeLMU` ("Ticket-Analysis",
node 0-1, available via local Figma MCP) + the approved interactive mockup artifact
https://claude.ai/code/artifact/75f1e184-cb45-410b-b150-0c6f497a3b5f (journeys, all SLA
states, copy rules baked in). Where they conflict, the artifact is newer and wins.

## Context

Managers reviewing a single ticket today must reconstruct "what went wrong" from the raw
Activity feed. This tab answers three questions at a glance: was the customer served on
time (timeline), who caused the delay (attribution metrics), and what did it cost
(conversation summary). Competitive research (Zendesk, Freshdesk, Zoho, Help Scout,
Intercom, Front, BoldDesk, Gorgias, HubSpot) confirmed no product renders a visual SLA
timeline on a ticket and none ships agent-response-gap / customer-hold-time as named
per-ticket metrics — both are differentiators, and all data already exists.

Design reference: Figma `1O9g7yTXrouZbWnXIzeLMU` + approved interactive mockup
(claude.ai artifact `75f1e184`).

## Locked product decisions

- Visible to **all agents**, **always** (open tickets show pending nodes + "–" metrics).
- **Zero redundancy** with existing UI: no first-response/resolution cards (sidebar SLA
  section owns status), no SLA banner, no rating/feedback display (right sidebar owns it),
  no data from `HD Ticket Activity`.
- All durations **business hours only** (SLA `calc_elapsed_time`), wall-clock fallback
  when the ticket has no SLA. No calendar toggle.
- Tab contents top-to-bottom: SLA timeline stepper → 3 attribution cards (avg agent
  response gap, customer hold time, longest agent silence) → response gap chart →
  conversation summary (customer/agent messages, total exchanges, internal comments,
  agents involved).

## Backend — `helpdesk/api/ticket_analytics.py` (new, ~230 lines)

One whitelisted method, one round-trip. Convention follows `helpdesk/api/ticket_stats.py`
(`@frappe.whitelist()` + `@agent_only` from `helpdesk/utils.py:179`, plus
`frappe.has_permission("HD Ticket", "read", ticket, throw=True)` like
`get_ticket_activities` in `hd_ticket/api.py:743`).

```python
@frappe.whitelist()
@agent_only
def get_ticket_analytics(ticket: str) -> dict: ...
```

Port from `git show 3949f3fa8:helpdesk/integrations/flow/quality.py` (unmerged
`flow-integration` branch) — copy `_working_seconds_fn`/`_elapsed`/`_average` logic
(wraps `HD Service Level Agreement.calc_elapsed_time`, wall-clock fallback), renamed
without the underscore prefix: `working_seconds_fn`, `elapsed`, `average`. Never
reimplement the business-hours walk.

Conventions (repo notes): `frappe.get_list` (not `get_all`), no `_`-prefixed function
names, tabs, type hints. Comments: minimal, very short, only where the code can't
explain itself (e.g. the pause-window Version parsing); no narration, no obvious
comments.

### Response schema

```jsonc
{
  "has_sla": true,
  "timeline": [                     // ordered stepper nodes
    {"key": "created", "state": "done", "timestamp": "...", "badge": null},
    {"key": "first_response", "state": "done|breach|pending", "timestamp": "...",
     "eta": "...",                  // response_by, for pending nodes
     "progress": 0.52,              // pending only: elapsed/target in business hours,
                                    // clamped 0..1 — fills the incoming segment
     "badge": {"text": "Within SLA · 4h target", "tone": "green|red|amber|gray"}},
    {"key": "hold", "state": "hold", "timestamp": "...", "active": false,
     "badge": {"text": "3h 20m paused", "tone": "amber"}},
    {"key": "exchanges", "state": "done", "count": 22,   // node "22 exchanges",
     "timestamp": null, "range": "May 6 – May 9"},       // omitted when < 2 messages
    {"key": "resolution", "state": "done|breach|pending", "timestamp": "...",
     "eta": "...", "badge": {"text": "2h to spare", "tone": "green"}}
  ],
  // milestone nodes (first_response, resolution) also carry, when applicable:
  //   "took": 73500, "target": 50400,          // business seconds for the leg
  //   "leg_label": "took 20h 25m · 14h target" // server-formatted mid-segment label
  //   "progress": <fraction>  // pending: elapsed/target; breach: target/(target+failed_by)
  "metrics": {                      // seconds; null = no data yet
    "avg_agent_gap": 4320, "customer_hold_total": 9900, "longest_agent_silence": 18600
  },
  "gaps": [                         // one bar per agent reply after a customer message
    {"replied_at": "...", "agent": "jane@x.com", "gap_seconds": 3600}
  ],
  "first_response_target": 14400,   // business seconds; feeds badges + progress,
                                    // NOT drawn on the chart (chart line = median of gaps)
  "summary": {
    "customer_messages": 12, "agent_messages": 10, "total_exchanges": 22,
    "internal_comments": 4,
    "agents_involved": [{"user": "jane@x.com", "full_name": "Jane Doe"}],
    "churn": {                      // routing churn; frontend hides below thresholds
      "sla_changes": 1,             // show when >= 1
      "team_changes": 2,            // show when >= 2
      "reassignments": 2            // show when >= 2
    }
  }
}
```

### Internal functions (small, typed)

- `conversation(ticket)` — single `frappe.get_list("Communication", ...)` ordered
  `creation asc`, fields `sent_or_received, sender, creation`. Feeds gaps, metrics, and
  summary (prior art queried twice; fold reply counting in).
- `gap_series(messages, working_seconds)` — direction-flip walk: Received→Sent flip
  appends `{replied_at, agent, gap_seconds}`; Sent→Received flips collect customer holds.
  Consecutive same-direction messages produce no gap.
- `compute_metrics(agent_rows, customer_holds)` — `average` for the agent gap;
  `sum` of customer holds for `customer_hold_total`; `max` for longest silence.
- `summary(ticket, messages)` — counts by direction; `total_exchanges = len(messages)`;
  `internal_comments = frappe.db.count("HD Ticket Comment", {"reference_ticket": ticket})`
  (verify link fieldname); `agents_involved` = ordered-unique Sent senders enriched with
  `full_name` (`frappe.utils.get_fullname`).
- `churn(ticket)` — routing churn, all from existing data (HD Ticket has
  `track_changes: 1`, so Version rows record structured field diffs):
  - `sla_changes` / `team_changes`: `frappe.get_list("Version", filters={"ref_doctype":
    "HD Ticket", "docname": ticket}, fields=["data"])`, parse `json.loads(data)["changed"]`
    entries, count changes to `sla` / `agent_group`. Initial values at insert produce no
    Version diff, so any counted sla change is a real mid-flight goalpost move. SLA is
    condition-based (any field per `get_sla()`), so this catches swaps priority alone
    would miss.
  - `reassignments`: Zendesk assignee_stations model — `frappe.get_list("ToDo",
    filters={"reference_type": "HD Ticket", "reference_name": ticket},
    fields=["allocated_to"])`; unassignment cancels ToDos but keeps rows →
    `max(0, distinct allocated_to - 1)`. Caveat: simultaneous multi-assignee tickets
    inflate it; acceptable for v1, note in docstring.
  Frontend shows churn rows only above thresholds (sla >= 1, team >= 2, reassign >= 2) —
  a visible row IS the red flag; healthy tickets show nothing.
- `first_response_target(details)` — `working_seconds(creation, response_by)` when both
  exist, else `None`.
- `build_timeline(details, working_seconds)` — pure function of HD Ticket fields,
  mirroring the case analysis in `desk/src/composables/useSLA.ts` (fulfilled / failed /
  due / overdue / hold / no-SLA, incl. the pausedBeforeBreach nuance):
  - **created**: always `done`.
  - **first_response**: `first_responded_on` vs `response_by` → done/breach; badge uses
    `first_response_failed_by` for "Failed by X". Unresponded → pending with ETA;
    past due → breach "Overdue by …".
  - **hold**: node only when `total_hold_time > 0` or currently paused. Paused seconds =
    `cint(total_hold_time)` + live `working_seconds(on_hold_since, now)` when
    `status_category == "Paused"` (total only accumulates on resume). NO "resumed"
    node — there is no stored resume timestamp, and `on_hold_since` is CLEARED on
    resume. Pause window timestamps ("11:40 AM – 2:30 PM") come from Version status
    diffs (same Version query as churn — parse `status` changes into/out of
    Paused-category statuses, mapping via HD Ticket Status.category). Fallback when
    Versions are pruned: duration-only hold node, no timestamps. One aggregated span
    in v1 even if multiple pauses (sum windows; per-pause spans deferred).
  - **exchanges** (node included when >= 2 messages): "N exchanges" with first→last
    message date range from the already-fetched conversation — narrates what happened
    between milestones (per Figma); the summary row keeps the per-direction split.
  - **resolution**: `resolution_date` → done ("X to spare" via
    `working_seconds(resolution_date, resolution_by)`) or breach
    (`resolution_failed_by`). Resolved/Closed with **no** `resolution_date` (auto-closed)
    → done with gray "Closed without resolution" — never fabricate a duration. Open →
    pending with ETA (while paused, `resolution_by` is cleared: pending + no ETA + active
    hold node tells the story).
  - Badge durations formatted server-side with `frappe.utils.format_duration`.

## Backend tests — `helpdesk/api/test_ticket_analytics.py` (~250 lines)

`FrappeTestCase` + `make_ticket` from `helpdesk/test_utils.py` (test SLA Mon–Fri
10:00–18:00 → deterministic business-hours assertions). Helper `add_message(ticket,
direction, when)` inserting a Communication with forced `creation`.

Cover: gap walk (alternating / consecutive same-direction / empty); weekend-spanning gap
(Fri 17:00 → Mon 11:00 = 2h business); no-SLA wall-clock fallback + `has_sla=False`;
timeline states (open+ETA, within-SLA, breached FR, resolved-with-spare, breached-then-
resolved, on-hold-now with live span, resumed with cumulative hold only, closed-without-
resolution); summary counts + `agents_involved` dedupe; churn (priority change that
re-selects SLA increments sla_changes; team change via Version; reassignment via ToDo);
exchanges node present only when >= 2 messages; `progress` fraction correct for pending
(elapsed/target) and breach (target/(target+failed_by)); pause window reconstructed from
Version status diffs + duration-only fallback when Versions absent;
non-agent PermissionError.

Run: `bench run-tests --site hd-tests --module helpdesk.api.test_ticket_analytics`

## Frontend — `desk/src/components/ticket-agent/analytics/` (new dir, 5 files)

Only the container fetches; children are props-only.

1. `TicketAnalyticsTab.vue` (~90) — `createResource({url:
   "helpdesk.api.ticket_analytics.get_ticket_analytics", cache: ["ticket-analytics", id],
   auto: true})`; loading spinner → SlaTimeline → cards grid → chart → summary.
2. `SlaTimeline.vue` (~120) — header is "SLA Timeline" + info icon with frappe-ui
   `Tooltip` (same pattern as the SLA settings list view) containing the date range and
   time basis ("May 6 – May 9 · business hours"); no inline hint text beside the
   heading. Body: pure CSS/flex stepper from `timeline[]`; state→color map
   (done green, hold amber dashed segment, breach red, pending gray); frappe-ui `Badge`
   under nodes, `Tooltip` with raw timestamp; pending shows "ETA …". The segment into a
   pending node is a progress bar: filled to `progress` (elapsed/target, from server) via
   a two-stop linear-gradient — half the FR budget gone reads at a glance before
   anything is overdue. The segment into a **breach** node uses the same gradient with
   red as the remainder color: green for the budget portion, red for the overage
   (fraction = target / (target + failed_by), computed server-side into the same
   `progress` field). Invariant: every segment is a time bar colored by what happened
   during it (green = within budget, red = overage, amber dashes = paused, gray =
   not yet elapsed). Legs are NOT width-proportional to time (steppers encode sequence,
   not scale), so absolute durations go in text: a small mid-segment label
   ("took 20h 25m · 14h target", or "Xh elapsed · Yh target" on pending legs) — the API
   sends `took` and `target` seconds per node, server-formatted. Edge nodes: badges and
   labels on the first/last node anchor left/right respectively (not centered) so they
   never overflow the card border.
3. `AnalyticsMetricCards.vue` (~70) — 3 cards (avg agent gap, customer hold **total**,
   longest silence — always rendered, null → "–"); adapt markup + `durationOrNull` from
   `git show 3949f3fa8:desk/src/components/ticket/QualityMetrics.vue`.
4. `ResponseGapChart.vue` (~90) — `import { ECharts } from "frappe-ui"` (already used by
   `ChartCardBase.vue:122`; no new deps). Bar per gap; dashed `markLine` at the
   **median** of this ticket's gaps (labeled "median Xm" — robust baseline so outlier
   bars pop; the SLA target only governs the first reply, so it is NOT drawn). Bars
   over 1.5× median tinted red ("abnormally slow for this ticket"); the metric card
   keeps the **avg** (total-impact number) — the two centers are deliberate and
   labeled. Tooltip shows agent + humanized gap. Y-axis: NEVER decimal hours ("5.2h") —
   set `yAxis.interval` to a round duration step (15m/30m/1h/2h…) and format ticks with
   the shared duration formatter ("2h 30m", "45m"); median markLine label likewise
   ("median 1h 07m"). markLine label: `position: "insideEndTop"` with a
   `backgroundColor` chip and padding so bars never slice through the text (never
   left-positioned where it can collide with bar #1). Open wording question: label the
   line "median" or the friendlier
   "typical" (Facebook-style, same math) — default to "median" unless product says
   otherwise.
5. `ConversationSummary.vue` (~70) — label/value rows: customer/agent messages, total
   exchanges, internal comments, agents involved (names via existing
   `MultipleAvatar.vue`), then conditional churn rows (SLA changed >= 1,
   team changes >= 2, reassignments >= 2 — hidden below threshold).

Design system rules:
- Spacing, padding, radii, and type sizes follow the Figma design (file
  `1O9g7yTXrouZbWnXIzeLMU`, pull exact values via local Figma MCP during
  implementation), expressed through frappe-ui/espresso tokens (ink-gray text ramp,
  outline-gray borders), not hardcoded hex or arbitrary px.
- Use frappe-ui components wherever one exists: `Badge`, `Tooltip`, `ECharts`,
  `Avatar`/`MultipleAvatar`, `EmptyState`, spinner/loading patterns. Custom markup
  only for what frappe-ui lacks (the stepper track itself).

Copy rules:
- NO em dashes anywhere in UI strings (badges, hints, captions, card descriptions,
  tooltips). Rephrase with commas, periods, or the middot separator
  ("No SLA · durations are wall-clock", "Paused, clock stopped"). En dash stays OK for
  time ranges ("11:40 AM – 2:30 PM").
- NEVER the word "Breached" in UI copy, too strong. Use "Failed by X" for both missed
  first response and missed resolution, matching the sidebar's useSLA wording.
  "Breach"/"breach" survives only as the internal timeline state name in code.

Wiring:
- `desk/src/types.ts:340` — add `"analytics"` to `TicketTab`.
- `TicketActivityPanel.vue` (~78-105) — append tab (icon: `~icons/lucide/chart-no-axes-column`
  or existing chart icon); `#tab-panel` renders `TicketAnalyticsTab` when active.
  Reply box stays visible (same as Calls tab).
- Tab persistence: automatic via `useActiveTabManager` hash handling.
- `useSLA.ts` NOT reused (client-side wall-clock; timeline needs server business-hours).

Edge states: gaps empty → `EmptyState.vue` "No agent replies yet"; null metrics → "–"
cards (grid never jumps); `has_sla=false` → caption "No SLA · durations are wall-clock".

## Milestones (one reviewable commit each)

1. `feat: ticket analytics API` — api + tests (testable without UI)
2. `feat: analytics tab with metrics and summary` — types, panel wiring, container,
   cards, summary
3. `feat: SLA timeline stepper` — SlaTimeline.vue
4. `feat: response gap chart` — ResponseGapChart.vue

## Verification

- `bench run-tests --site hd-tests --module helpdesk.api.test_ticket_analytics`
  (start bench redis first).
- Manual on hd.localhost (QA creds in memory): open a resolved ticket → all sections
  populated; an open ticket → pending nodes + "–"; a paused ticket → amber hold node;
  a no-SLA ticket → wall-clock caption; non-agent portal user → API rejects.
- Check tab deep-link `#analytics` survives reload.

## Performance

No new indexes needed (verified on hd.localhost): Communication
(`comm_ref_type_date_idx`), Version (`ref_doctype_docname_index`), ToDo
(`reference_type_reference_name_index`), and HD Ticket Comment (`reference_ticket`)
already have composite/single indexes covering every per-ticket lookup; HD Ticket is
fetched by primary key. Compute on the fly, no stored analytics field.

## Risks / verify during implementation

- `frappe.get_list` enforces user permissions — verify an ordinary agent can read
  Version and ToDo rows through it; if not, decide between scoped
  `ignore_permissions` on those two internal reads or degrading churn to null.
- `HD Ticket Comment` link fieldname (`reference_ticket`).
- `on_hold_since` staleness after resume → gate live-hold on `status_category == "Paused"`.
- frappe-ui `Badge`/`Tooltip` prop names on pinned beta.24.
- Mobile (`MobileTicketAgent.vue`) untouched — note in PR description.
