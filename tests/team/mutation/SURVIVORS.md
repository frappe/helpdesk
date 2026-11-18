# Mutation analysis

Tool: Cosmic Ray 8.9.0, core operators plus three custom operators
(`operators/sqe_operators`). Target: the business-rule scope (the same scope
as the 100% coverage gate). Run with `bash tests/team/run_mutation.sh`.

| | Run 1 | Run 2 (after killing tests) |
|---|---|---|
| Unit tests | 135 | 159 |
| Mutants in scope | 237 | 237 |
| Killed | 206 | 230 |
| Survived | 31 | 7 |
| Mutation score | 86.9% | 97.0% |
| Score excluding the 7 equivalent mutants | 89.6% | 100% |

Raw reports: `evidence/run1_mutation_report.md`, `evidence/run2_mutation_report.md`.

## Custom operators

| Operator | Fault injected | Rule it targets | Mutants | Killed |
|---|---|---|---|---|
| `sqe/SwapTicketStatus` | A status / category literal replaced by the one most easily confused with it (Resolved->Open, Closed->Resolved, Open->Resolved, Paused->Open) | BR1, BR3, BR4 | 10 | 10 |
| `sqe/RevokeAgentExemption` | `is_agent()` -> `False` (agent treated as customer) | BR2, BR4 | 4 | 4 |
| `sqe/GrantAgentExemption` | `is_agent()` -> `True` (customer treated as agent) | BR2, BR4 | 4 | 4 |

All 18 domain mutants were killed in run 1, which is evidence that the tests
written from the decision tables do check the status and role logic.

## The 31 survivors of run 1

Classification: **E** equivalent, **W** weak test data (a test reached the
line but its values could not tell the mutant apart), **M** missing test.

| # | Location | Mutation | Class | Why it survived | Action |
|---|---|---|---|---|---|
| S1 | customer_edit_controller.py:23 | `user != "Guest"` -> `>` | W | test user `customer@...` sorts after "Guest" | killed: user `Alice@example.com` |
| S2 | :23 | `!=` -> `is not` | W | "Guest" literal in the test is the same object as in the source | killed: `fresh("Guest")` |
| S3 | :39 | `status == "Closed"` -> `is` | W | same-object literal | killed: `fresh("Closed")` |
| S4 | :39 | `==` -> `<=` | W | no status sorting before "Closed" was tried | killed: custom status "Awaiting customer" |
| S5 | :84 | set `\|` -> `^` | M | no template row repeated an always-writable field | killed: editable row `feedback` |
| S6 | :90 | `status == "Closed"` -> `is` | W | same-object literal | killed: `fresh("Closed")` |
| S7 | :90 | `==` -> `<=` | W | no status sorting before "Closed" | killed: custom status |
| S8 | :101 | `visible_to != "Agents"` -> `>` | W | "Everyone"/"Customers" both sort after "Agents" | killed: blank `visible_to` |
| S9 | :101 | `!=` -> `is not` | W | same-object literal | killed: `fresh("Agents")` |
| S10 | hd_ticket.py:414 | `status_category != "Resolved"` -> `is not` | W | same-object literal | killed: `fresh("Resolved")` |
| S11 | :414 | `!=` -> `<` | **E** | category is a Select of Open/Paused/Resolved; both other values sort before "Resolved", so `<` and `!=` agree on every valid value | none |
| S12 | :951 | `status != "Closed"` -> `>` | W | all tried statuses sort after "Closed" | killed: custom status |
| S13 | :951 | `!=` -> `is not` | W | same-object literal | killed: `fresh("Closed")` |
| S14 | :954 | `previous.status_category != "Resolved"` -> `is not` | W | same-object literal | killed: `fresh("Resolved")` |
| S15 | :954 | `!=` -> `<` | **E** | as S11 | none |
| S16 | :962 | `status_category != "Resolved"` -> `is not` | W | same-object literal | killed: `fresh("Resolved")` |
| S17 | :962 | `!=` -> `<` | **E** | as S11 | none |
| S18 | :1493 | `auto_close_tickets == 0` -> `<= 0` | **E** | the field is a Check (0 or 1); it is never negative | none |
| S19 | :1544 | `continue` -> `break` | W | the failing ticket could be processed last (`list(set(...))` has no fixed order), so one failure could not show the loop stopping | killed: both tickets fail, both must be logged |
| S20 | hd_ticket_status.py:10 | default `merge=False` -> `True` | **E** | the parameter is never read in the function | none |
| S21 | :11 | `old == "Closed"` -> `is` | W | same-object literal | killed: `fresh("Closed")` |
| S22 | :11 | `==` -> `<=` | W | renamed status sorted after "Closed" | killed: rename "Archived" |
| S23 | :25 | `old_name == "Closed"` -> `is` | W | same-object literal | killed: `fresh("Closed")` |
| S24 | :47 | `old_category != self.category` -> `>` | W | only Paused->Open was tried (old sorts after new) | killed: Open->Paused |
| S25 | :47 | `!=` -> `is not` | W | same-object literal | killed: `fresh("Paused")` |
| S26 | :53 | `count == 0` -> `<= 0` | **E** | a row count is never negative | none |
| S27 | :71 | `count == 0` -> `<= 0` | **E** | as S26 | none |
| S28 | :113 | `name == settings_default` -> `is` | W | same-object literal | killed: `fresh("Replied")` |
| S29 | :113 | `==` -> `<=` | W | setting sorted before the name | killed: setting "Working" |
| S30 | :115 | `name == settings_reopen` -> `is` | W | same-object literal | killed: `fresh("Replied")` |
| S31 | :115 | `==` -> `<=` | W | setting sorted before the name | killed: setting "Working" |

Totals: 7 equivalent, 23 weak test data, 1 missing test. All 24 killable
mutants are killed by `unit/test_survivor_kills.py`; run 2 confirms exactly the
7 equivalent mutants remain.

## What the analysis showed

* 100% statement and branch coverage did not mean the tests were strong:
  31 faults ran through covered lines unnoticed.
* The dominant weakness was test data, not missing scenarios. Literals copied
  from the source hide identity faults, and "convenient" example values hide
  ordering faults. Real values come from the database and from user-defined
  statuses, so both kinds of fault would have reached production behaviour.
* S19 also exposed a hidden order dependence in the code under test
  (`list(set(...))`), which made the original test's verdict depend on hash
  ordering.

## Gate threshold

The CI gate is **95%**. The achievable maximum on this scope is 97.0%
(230 / 237) because 7 mutants are equivalent and cannot be killed by any
test. 95% leaves room for about four new unkilled mutants (roughly one new
untested condition) before the merge is blocked, and is well above the 86.9%
that a coverage-complete but weakly-asserted suite scored.
