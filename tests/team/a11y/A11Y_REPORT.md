# Usability and accessibility evaluation

Baseline: helpdesk 16.1.0 (commit e326986) on frappe 16.56.0, local site,
synthetic accounts from `tests/team/seed.sh`. No participants: every task and
scan is scripted.

| Tool | Version | Used for |
|---|---|---|
| Playwright (Chromium 159 headless shell) | 1.65.1 | task tests, keyboard test, driving the scans |
| axe-core via @axe-core/playwright | 4.14.0 | full rule set, every rule axe ships |
| Lighthouse (Node API) | 13.6.0 | accessibility, best practices, SEO; desktop preset |

Scripts: `e2e/usability/*.spec.mjs` (task tests), `e2e/a11y/scan.mjs` (both
tools). Reports: `a11y/evidence/before/` and `a11y/evidence/after/`, one
`.axe.json`, `.lighthouse.html` and `.lighthouse.json` per screen, plus
`summary.md`. The Playwright HTML report is written to `reports/e2e/html/`.

## 1. Task tests

| Test | Workflow | What it checks | Result |
|---|---|---|---|
| `task_raise_ticket.spec.mjs` | A | Submits a subject of spaces, which the rule rejects. Asserts the message "Value missing for HD Ticket: Subject", no ticket created, the description kept. Corrects the subject; asserts the new ticket page, Status Open and the stored record. | pass |
| `task_close_and_rate_keyboard.spec.mjs` | B | Opens the rating dialog with Enter, chooses a rating with the arrow keys and Space, the reason with Enter, types a comment, reaches Submit with Tab and submits with Enter. Asserts focus reached rating, reason, comment, Submit in that order, then the Closed status and the stored rating. | pass |

Observations from the keyboard test (not failures of the test):

* The rating group is a single tab stop: arrow keys move between 1-5, which
  is the expected radio-group pattern.
* Submit is not in the tab order until a rating and a reason are chosen,
  and nothing tells a keyboard or screen-reader user it exists. The visible
  "Select a rating *" and "Pick an option *" labels are the only hint.
* On the New Ticket form, the 15 editor toolbar buttons sit between the
  description and Submit in the tab order.

## 2. Scans: before

Lighthouse is run while logged in: Playwright logs the seeded account in
inside a Chromium started with a remote-debugging port, and Lighthouse
connects to that browser with storage reset disabled. axe-core runs in
legacy mode on every screen, because the default frame handling never
returns on the agent page's message iframe; legacy mode still scans inside
the iframe.

| Screen | Use cases | LH accessibility | LH best practices | LH SEO | axe rules | axe elements |
|---|---|---|---|---|---|---|
| S1 Customer: New Ticket form | UC-01 | 94 | 100 | 90 | 6 | 9 |
| S2 Customer: ticket page (resolved) | UC-02, UC-05 | **82** | 100 | 90 | 6 | 36 |
| S3 Customer: Rate this ticket dialog (axe only) | UC-02 | - | - | - | 1 | 9 |
| S4 Customer: ticket list | UC-06 | 85 | 100 | 90 | 6 | 8 |
| S5 Agent: ticket page | UC-03, UC-04 | 85 | 100 | 90 | 7 | 45 |

## 3. Issue catalogue

An issue reported by both tools is counted once. Priority: **P1** blocks or
seriously hinders a step of a use case for assistive-technology users;
**P2** degrades navigation; **P3** no direct user impact.

| ID | Issue (axe rule / Lighthouse audit) | Found by | Screens | Element(s) | User impact | Proposed fix | Pri | Status |
|---|---|---|---|---|---|---|---|---|
| A11Y-01 | Icon-only buttons with no name (`button-name`, critical) | both (S2, S4, S5); axe only (S1) | S1, S2, S4, S5 | S1 first editor toolbar button (attach); S2 sidebar envelope button; S4 sort-direction toggle; S5 four "..." buttons next to the Public Views items | A screen reader announces just "button"; the user cannot tell attach, reply, sort or view options apart | `aria-label` on each icon button | P1 | fixed on S2; open S1, S4, S5 |
| A11Y-02 | Description editor has no name (`aria-input-field-name`, serious) | axe | S1 | `.tiptap` contenteditable | The main field of UC-01 is announced as an unlabelled text box | `aria-label="Description"` (or `aria-labelledby`) on the editor | P1 | open |
| A11Y-03 | Text below 4.5:1 contrast (`color-contrast`, serious) | both | S1, S2, S3, S5 | breadcrumb "Tickets" link; "Please enter a subject to continue" (S1); message time stamps and the Ticket details labels (S2, S3); tab labels, panel heading (S5) | Low-vision users cannot read labels and times | use `text-ink-gray-7` instead of `-5` for this text | P1 | fixed on S2/S3; open S1, S5 |
| A11Y-04 | Message iframes have no title (`frame-title`, serious) | both | S2 | each `iframe.prose-f` in the conversation | A screen reader announces an unnamed frame for every message | `title` on the iframe | P1 | fixed (shared component, so S5 too) |
| A11Y-05 | ARIA attributes on a `div` popover trigger (`aria-allowed-attr`, critical) | both | S4, S5 | `#reka-popover-trigger-*` around the Filter and Sort controls (S4) and the Assignee / Priority pickers (S5) | Expanded/collapsed state is not exposed reliably, so the user does not know a picker opened | render the trigger as the button itself (`as-child`) so the ARIA state sits on a button | P1 | open |
| A11Y-06 | Visible text not in the accessible name (`label-content-name-mismatch`, serious) | both | S4 | Filter button, `aria-label="Filter"`, visible text "Filter 2" | A voice-control user saying the visible text ("click Filter 2") is not understood | drop the `aria-label` or include the count in it | P2 | open |
| A11Y-07 | No main landmark (`landmark-one-main`, moderate) | both | S1, S2, S4, S5 | `html` | Screen-reader users cannot jump to the main content | wrap the page body in `<main>` | P2 | fixed on S2; open elsewhere |
| A11Y-08 | No level-one heading (`page-has-heading-one`, moderate) | axe | S1, S2, S4, S5 | `html` | Heading navigation has no entry point naming the page | an `h1` (visually hidden if needed) with the page or ticket name | P2 | fixed on S2; open elsewhere |
| A11Y-09 | Content outside landmarks (`region`, moderate) | axe | S1, S2, S4, S5 | quick filters, sidebar, conversation blocks | Landmark navigation skips that content | follows from A11Y-07 | P2 | fixed on S2; open elsewhere |
| A11Y-10 | Two unnamed `nav` landmarks (`landmark-unique`, moderate) | axe | S5 | the two sidebar `nav` elements | The landmark list shows two identical "navigation" entries | `aria-label` on each nav ("Main", "Views") | P2 | open |
| A11Y-11 | No meta description (`meta-description`, SEO) | Lighthouse | all | `head` | Search results show no summary; small effect because pages need sign-in | `<meta name="description">` in the page shell | P3 | fixed (shared shell, all screens) |
| A11Y-12 | No source maps for large scripts (`valid-source-maps`, best practices) | Lighthouse | all | built JS bundles | None for users; harder production debugging | publish source maps, or accept | P3 | open (accepted) |

Usability findings from the task and use-case tests:

| ID | Finding | Evidence | Impact | Proposed fix | Pri |
|---|---|---|---|---|---|
| UX-01 | The customer's ticket list opens filtered to "Status is Open", so a ticket an agent has just resolved is not listed | UC-06 AF2 | The customer thinks the ticket has vanished | show all statuses by default, or label the filter clearly | P2 |
| UX-02 | Rating dialog: Submit stays out of reach until rating and reason are chosen, with no explanation | task B | Keyboard and screen-reader users cannot find how to finish | keep Submit focusable and explain what is missing on activation | P2 |
| UX-03 | Typing a subject raises an "Internal Server Error" toast | UC-01, server log `unknown command 'FT.SEARCH'` | Alarming error during a normal task; article suggestions need Redis with RediSearch, which this install lacks | handle the missing search module quietly; install Redis Stack in deployment | P2 |
| UX-04 | 15 toolbar buttons between the description and Submit | task B probe, New Ticket form | Slow keyboard completion of UC-01 | make the toolbar a single tab stop with arrow-key navigation | P3 |

## 4. The fix: customer ticket page (S2)

Chosen because it had the lowest accessibility score (82) and serves two use
cases (UC-02 close and rate, UC-05 reply). The change is in the Helpdesk
source and was rebuilt with `bench build --app helpdesk`; the diff is
`a11y/evidence/fix.diff`.

| File | Change | Issues |
|---|---|---|
| `desk/src/pages/ticket/TicketCustomer.vue` | page root `div` -> `main`; visually hidden `h1` with the ticket subject; breadcrumb text to `text-ink-gray-7` | A11Y-07, -08, -09, -03 |
| `desk/src/components/EmailContent.vue` | `:title="__('Message')"` on the message iframe | A11Y-04 |
| `desk/src/pages/ticket/TicketCommunication.vue` | time stamp `text-ink-gray-5` -> `text-ink-gray-7` | A11Y-03 |
| `desk/src/components/ticket/TicketCustomerSidebar.vue` | `aria-label="Write a reply"` on the envelope button; field labels to `text-ink-gray-7` | A11Y-01, -03 |
| `desk/index.html` | `<meta name="description">` | A11Y-11 |

## 5. After

| Screen | LH accessibility | LH SEO | axe rules | axe elements |
|---|---|---|---|---|
| S1 New Ticket form | 94 -> 94 | 90 -> 100 | 6 -> 6 | 9 -> 9 |
| **S2 Customer ticket page (fixed)** | **82 -> 100** | **90 -> 100** | **6 -> 0** | **36 -> 0** |
| S3 Rate this ticket dialog | - | - | 1 -> 0 | 9 -> 0 |
| S4 Customer ticket list | 85 -> 85 | 90 -> 100 | 6 -> 6 | 8 -> 8 |
| S5 Agent ticket page | 85 -> 85 | 90 -> 100 | 7 -> 7 | 45 -> 45 |

Best practices stayed 100 on every screen (the source-map audit fails but
carries no weight in the score).

* Every accessibility issue on S2 is gone in both tools, including the
  landmark and heading issues axe reported inside the message iframes.
* S3 (the rating dialog over S2) is clean because its only issue was the
  time-stamp and label contrast fixed on S2.
* SEO rose on every screen because the meta description is in the shared
  page shell.
* The other screens are unchanged, as expected: their issues are open.
* No regression: all 32 use-case flows and both task tests pass against the
  fixed build (34 passed).

## How to rerun

```
cd ~/frappe-bench/apps/helpdesk/tests/team/e2e
node a11y/scan.mjs before     # or: after
npx playwright test usability
```
