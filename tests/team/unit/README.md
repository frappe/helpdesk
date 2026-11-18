# Unit tests (white-box)

Run from the app folder (`~/frappe-bench/apps/helpdesk`):

    bash tests/team/run_unit.sh

The tests need no site, database or running server. The functions under test
are the real ones from the baseline; `frappe`, `is_agent` and the clock are
replaced by test doubles (see `conftest.py`).

## Coverage scope

"Server-side business logic" for this project is the code that implements the
four business rules of the ticket workflows:

| Scope item | File | Rule |
|---|---|---|
| `close_tickets_after_n_days` | `hd_ticket.py` | BR1 auto-close after N days (boundary) |
| `HDTicket.validate_feedback` | `hd_ticket.py` | BR2 feedback required to resolve (5 conditions, critical module) |
| `HDTicket.is_valid_status_transition`, `HDTicket.set_resolution_date` | `hd_ticket.py` | BR3 resolution date on change of state |
| whole file | `customer_edit_controller.py` | BR4 what a customer may fill and change |
| whole file | `hd_ticket_status.py` | status records the rules depend on |

The rest of `hd_ticket.py` (email, SLA wiring, list views, telemetry) is
outside the two workflows' rules and is excluded; `tools/scoped_coverage.py`
reports and gates on exactly the scope above.

## BR2 condition coverage

`ACCEPT = A or B or C or D or E`; the ticket is rejected only when all are False.

| | Condition (True means "accept") |
|---|---|
| A | `feedback_rating` is set |
| B | `status_category != "Resolved"` |
| C | session user is an agent |
| D | no agent has replied |
| E | feedback is not mandatory in HD Settings |

MCC: all 32 rows, `test_mcc_every_condition_combination[FFFFF..TTTTT]`
(the id is the A-E truth values).

MC/DC pairs taken from the MCC table (each pair differs in one condition only
and flips the outcome):

| Condition | Row 1 | Outcome | Row 2 | Outcome |
|---|---|---|---|---|
| A | FFFFF | reject | TFFFF | accept |
| B | FFFFF | reject | FTFFF | accept |
| C | FFFFF | reject | FFTFF | accept |
| D | FFFFF | reject | FFFTF | accept |
| E | FFFFF | reject | FFFFT | accept |

Minimum MC/DC set: 6 rows (n + 1).
