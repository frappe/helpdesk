# Endpoint weaknesses found by the API and integration tests

Baseline: helpdesk 16.1.0 (commit e326986) on frappe 16.56.0. Every entry was
observed on the running system and is pinned by a strict expected-failure
test, so it is re-checked on every run. All are GitHub Issues on the fork
(defect IDs and Issue numbers in `management/defects.yaml`). D-01 (PR #38),
W-API-05 and W-API-06 (PR #41) are fixed; their tests are no longer pinned
and now pass.

| ID | Endpoint | Expected | Observed | Proposed severity | Test |
|---|---|---|---|---|---|
| D-01 | daily auto-close job (BR1 x BR3) | an auto-closed ticket gets a resolution date, like any closed ticket | status Closed, category Resolved, `resolution_date` empty; the same change through the API stamps it | Major: resolution analytics miss every auto-closed ticket. **Fixed by PR #38 (DEF-01, Issue #2 closed)** | `test_auto_closed_ticket_gets_a_resolution_date_like_any_closed_ticket` (passes) |
| W-API-05 | assignAgent | only agents assign tickets (403 for a customer) | the ticket's own customer gets 200 and the agent is assigned | Major: role check missing on an agent action. **Fixed by PR #41 (DEF-02, Issue #3 closed)** | `test_customer_cannot_assign_an_agent` (passes) |
| W-API-06 | assignAgent | a ticket can only be assigned to an agent | assigning to a customer account returns 200 and shares the ticket; that customer can then read another customer's ticket | Major: data disclosure through a mis-assignment. **Fixed by PR #41 (DEF-03, Issue #4 closed)**: now 417 "Tickets can only be assigned to agents" | `test_ticket_cannot_be_assigned_to_a_non_agent` (passes) |
| W-API-07 | updateTicket (feedback) | rating belongs to a resolved ticket; rating must not block closing | a customer can rate an Open ticket and is then refused when closing it | Minor | `test_rating_an_open_ticket_does_not_lock_the_customer_out` |
| W-API-08 | updateTicket | `resolution_date` is server-computed | an agent can overwrite it with any date | Minor: reporting data can be falsified | `test_resolution_date_cannot_be_written_directly` |
| W-API-02 | createTicket, getTicket, assignAgent | a missing required argument is a 4xx naming the argument | 500 TypeError with a server traceback in the body | Minor: wrong status class, internals leaked | generated cases + `test_create_without_a_document_is_a_client_error` |
| W-API-03 | updateTicket (feedback_extra) | a number is rejected or stored as text | 500 TypeError from the HTML sanitiser | Minor | generated case |
| W-API-09 | updateTicket (agent_group) | the ticket moves to the team | 500 IndexError (seeded team has no members) | Minor: needs root-cause analysis | `test_agent_can_route_a_ticket_to_a_team` |
| W-API-01 | createTicket, updateTicket (subject) | text only | a number is accepted and stored | Trivial: no type validation | generated cases |
| W-API-04 | createTicket | a repeated identical request does not duplicate | two tickets; no idempotency key | Trivial: normal for POST, but double-submit makes duplicates | `test_repeating_a_create_request_does_not_duplicate_the_ticket` |
| W-API-10 | daily auto-close job | an inactive ticket is closed | a ticket with no messages is never closed (the query inner-joins messages) | Trivial | `test_inactive_ticket_without_any_message_is_closed` |

## Notes

* D-01 is the cross-workflow defect: workflow A/B and the job all change the
  same shared record, and only the job leaves it inconsistent. Root cause
  (confirmed in `management/RCA.md`, RCA-1): the job saves with
  `flags.ignore_validate = True`, which makes Frappe skip `before_save` as
  well as `validate`, and `set_resolution_date` is called from
  `before_save`. (An earlier guess here, that it ran with a stale status
  category, was wrong.)
* Validation failures return **417**, not 400/422. That is the framework's
  convention and is documented in the spec, not counted as a weakness.
* Not reproduced as a test: a customer reply through
  `create_communication_via_contact` returned 500 once during exploration. It
  was not investigated and is not claimed as a finding.
