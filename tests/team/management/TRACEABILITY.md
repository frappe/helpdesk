# Traceability matrix

Status as of 2026-11-18, baseline e326986 plus the DEF-01 fix (PR #38) and
the DEF-02/03 fix (PR #41), both merged into `team/sqe-tests` through the CI
gate. Every requirement and business
rule is traced forward to the tests at each level and to the defects found,
and backward to its risk. Test names are abbreviated; the full name is the
function or flow ID in the file shown.

Levels: **U** unit (`unit/`), **A** API and integration (`api/`),
**E** browser use case (`e2e/usecases/`), **X** usability, security,
performance and recovery (`e2e/usability/`, `e2e/security/`, `perf/`,
`api/test_failure_recovery.py`).

Result: **Pass** = every test passes and no open Major defect;
**Pass, minor open** = passes, minor defects open; **Fail** = a test pinned
as expected failure or an open Major defect.

## Requirements and business rules

| ID | Requirement / rule | Risk | U | A | E | X | Defects | Result |
|---|---|---|---|---|---|---|---|---|
| FR-A1 | Customer raises a ticket with subject and description | PR-06, PR-07 | `test_br4_*` insert rules | `test_create_ticket_input` (generated EP/BVA), `test_repeating_a_create_request…` | UC-01 MF, AF1, AF2 | task A; AC-01; R1 recovery | DEF-10, DEF-12, DEF-13 | Pass, minor open |
| FR-A2 | New ticket is Open, Medium, raised by the caller | PR-04 | `test_br4_*` insert rules | `test_new_ticket_gets_the_default_state…`, `test_customer_cannot_set_server_controlled_fields…` | UC-01 MF | AC-01 | – | Pass |
| FR-A3 | Subject mandatory, at most 140 characters | PR-06 | – | generated BVA lengths 0/1/2 and 139/140/141 plus EP cases on `subject` (create and update) | UC-01 AF1, EF1, EF3 | task A (rejected then corrected) | DEF-09 | Pass, minor open |
| FR-A4 | Ticket visible only to its customer and to agents | PR-05 | – | `test_ticket_is_private…`, `test_another_customer_cannot_update…`, `…cannot_assign_the_ticket`, `test_ticket_cannot_be_assigned_to_a_non_agent` (passes since PR #41) | UC-03 EF1, EF2; UC-06 EF2 | AC-02, AC-03, AC-06, AC-07, AC-09, AC-13 | DEF-03 (closed) | Pass |
| FR-B1 | Agent assigns a ticket to an agent | PR-05 | `test_assignment_access` (decision table, caller × target) | `test_assign_agent_input`, `test_repeating_an_assignment…`, `test_customer_cannot_assign_an_agent` (passes since PR #41), `test_agent_can_route_a_ticket_to_a_team` (xfail) | UC-03 MF | AC-08, AC-11 | DEF-02 (closed), DEF-03 (closed), DEF-08 | Pass, minor open |
| FR-B2 | Agent sets priority and ticket type | PR-04 | `test_br4_*` update perms | `test_update_ticket_input` (enum EP) | UC-03 AF1, AF2 | AC-05, CT-05 | – | Pass |
| FR-B3 | Agent changes status; resolution date follows BR3 | PR-02 | `test_br3_*`, `test_ticket_status_rules` | `test_agent_may_make_every_status_change`, `test_one_disallowed_change_from_each_state…`, `test_unknown_status…`, `test_repeating_a_resolve_request…`, `test_resolution_date_cannot_be_written_directly` (xfail) | UC-04 MF, AF1, AF2, EF1, EF2; UC-05 AF2 | AC-04, AC-10; R2 recovery; k6 `get_one` | DEF-05 | Pass, minor open |
| FR-B4 | Customer closes own ticket; rating first if resolved and answered | PR-01 | `test_br2_*` (MCC 32 rows, MC/DC) | `test_customer_may_close…`, `…cannot_close_a_resolved_ticket_without_feedback`, `…closes_a_resolved_ticket_with_feedback`, `test_unknown_feedback_option…`, `test_rating_an_open_ticket…` (xfail) | UC-02 MF, AF1, AF2, EF1, EF2 | task B (keyboard) | DEF-04, DEF-29 | Pass, minor open |
| FR-B5 | Closed or rated ticket locked for the customer | PR-04 | `test_br4_*` | `test_decision_table_closed_or_rated_locks…`, `test_agent_is_not_locked_out…`, `test_repeating_a_close_request…` | UC-02 EF3; UC-05 MF, AF1, EF1, EF2, EF2 with the status list late (xfail) | CT-05 | DEF-04, DEF-35 | Pass, minor open |
| FR-B6 | Waiting ticket auto-closed after N days | PR-03 | `test_br1_*` | `test_three_point_boundary_on_days_of_inactivity`, `test_running_the_job_again…`, `test_only_tickets_in_the_configured_status…`, `test_nothing_is_closed_when…switched_off`, `test_the_threshold_follows_the_setting`, `test_a_new_customer_message_restarts_the_clock`, `test_auto_closed_ticket_gets_a_resolution_date…` (passes since PR #38), `test_inactive_ticket_without_any_message…` (xfail) | – (scheduled job, no screen) | – | DEF-01 (closed), DEF-11 | Pass, minor open |
| BR1 | Auto-close boundary: closed when inactivity > N days (N−1, N, N+1) | PR-03 | `test_br1_*` (cut-off, strictly older, N=0/1/2 wording) | as FR-B6 | – | – | DEF-01 (closed), DEF-11 | Pass, minor open |
| BR2 | Feedback required: reject iff not rated ∧ Resolved ∧ not agent ∧ agent replied ∧ mandatory | PR-01 | `test_br2_*` MCC + MC/DC; mutation 100 % killable | decision-table API tests: one accept case per condition, reject when none holds | UC-02 MF, EF1, EF2 | task B | DEF-04 | Pass, minor open |
| BR3 | Resolution date set on entering Resolved category, cleared on leaving, kept on Resolved→Closed | PR-02 | `test_br3_*` (state transition, every transition) | state-transition tests above; R2 recovery | UC-04 AF2; UC-05 AF2; UC-02 MF postcondition | R2 | DEF-01 (closed), DEF-05 | Pass, minor open |
| BR4 | Customer may not change a closed or rated ticket or agent-only fields | PR-04 | `test_br4_*` (24 tests) | `test_customer_edit_is_refused_and_explained`, decision table | UC-02 EF3; UC-05 EF2 | AC-04, AC-05, CT-05 | – | Pass |

## Coverage summary

| | Count | % |
|---|---|---|
| Requirements and rules in scope | 14 (10 FR + 4 BR) | |
| Traced to at least one executed test | 14 | **100 %** |
| Tested at two or more levels | 14 | 100 % |
| Pass (incl. minor open) | 14 | **100 %** (64 % on the baseline, 86 % after PR #38) |
| Fail (open Major defect or expected-failure test) | 0 | 0 % |

On the baseline, five rows failed on three Major defects. **DEF-01** (BR1 ×
BR3, auto-closed ticket has no resolution date) is fixed by PR #38, which
moved FR-B6, BR1 and BR3 to passing. **DEF-02 / DEF-03** (assignment had no
role or target check) are fixed by PR #41, which moved FR-A4 and FR-B1 to
passing. Minor defects remain open on several rows.

## Test inventory per level

| Level | Tests | Result on 2026-11-17/18 | Evidence |
|---|---|---|---|
| Unit | 167 | 167 pass; scope coverage 100 % statements (144), 100 % branches (68) | `reports/unit/`, CI job "Unit tests + coverage gate" |
| Mutation | 238 mutants (3 custom operators) | 97.1 % killed (baseline 237 mutants, 97.0 %) | `mutation/SURVIVORS.md`, CI job "Mutation score >= 95 %" |
| API and integration | 132 (incl. 58 generated EP/BVA cases, 2 recovery, 5 for the DEF-01 data repair) | 121 pass, 11 expected failures (known weaknesses); D-01 passes since PR #38, W-API-05/06 since PR #41 | `api/`, `run_api.sh` |
| Use cases (Playwright) | 33 flows, 6 use cases | 32 pass; 1 pinned expected failure reproduces DEF-35 | `e2e/usecases/` |
| Usability tasks | 2 (one with keyboard navigation) | pass | `e2e/usability/` |
| Security (Playwright) | 13 access decisions + 5 controls | 13 / 13 decisions as expected since PR #41 (AC-08 failed on the baseline: DEF-02); 6 automated controls pass (CT-08 added with PR #42; it failed on the baseline: DEF-14) | `security/evidence/` |
| Performance | 4 k6 runs | all within limits | `perf/evidence/` |
| Static analysis | SonarQube, 706 files | 189 issues, triaged | `sonar/` |

## Backward trace: risks without a requirement

PR-08 (accessibility), PR-09 (performance) and PR-10 (vulnerable
components) are quality risks, not functional requirements. They trace to
the accessibility scans (A11Y-01…12), the k6 runs and the ZAP/pip-audit
evidence; see `RISK_REGISTER.md`.
