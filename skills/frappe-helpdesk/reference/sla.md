# How the SLA works

An SLA (`HD Service Level Agreement`) has:

- `priorities`: one row per ticket priority, with `response_time` and `resolution_time` in seconds. One row is the `default_priority`.
- `support_and_resolution`: the working hours, one row per `workday` with a `start_time` and `end_time`.
- `holiday_list`: an `HD Service Holiday List` whose dates do not count.
- `condition`: a Python expression on the ticket, written against `doc`, such as `doc.customer == 'Acme'`.
- `default_sla`, `rank`, `enabled`, `start_date`, `end_date` and `apply_sla_for_resolution`.

## Which SLA a ticket gets

Every save of the ticket picks its SLA again. The candidates are the enabled SLAs inside their `start_date` and `end_date` that have a row for the ticket's priority. They are tried in this order:

1. SLAs with a `rank`, lowest first.
2. SLAs without one, oldest first.
3. The default SLA, last. It needs no condition.

The first one whose `condition` is true wins. A non-default SLA with no condition never matches. When nothing matches, the ticket's SLA fields are cleared.

So changing a ticket's priority, or any field a condition reads, can move it to another SLA.

## Due dates

- **The clock starts** at `service_level_agreement_creation`, stamped when an SLA first attaches. It does not move when the ticket switches to another SLA.
- **`response_by`** is the clock start plus the priority's `response_time`, counting only working hours and skipping holidays. A ticket raised at 17:30 against hours of 09:00 to 18:00 and a 1 hour target is due at 09:30 on the next working day.
- **`resolution_by`** is worked out the same way from `resolution_time`, plus the time the ticket has spent on hold (`total_hold_time`).
- Dates are worked out again on every save, against the current SLA and priority.

## Pauses

- Moving the ticket to a status in the Paused category sets `on_hold_since` and clears the resolution target.
- Moving it back out adds the paused working time to `total_hold_time`, which pushes `resolution_by` later.
- When a resolved ticket is reopened, the time it spent resolved also counts as hold.

## First response

`first_responded_on` is set by the first agent reply. It is also set when the ticket moves to a Paused status, or straight from Open to Resolved, before anyone replied.

## Status

`agreement_status` is worked out in this order:

1. **Failed**: the first response, or the resolution when `apply_sla_for_resolution` is set, came after its due date, or is still missing after it.
2. **Paused**: the ticket is on hold.
3. **First Response Due**: no agent has replied yet.
4. **Resolution Due**: replied, not resolved, and the SLA tracks resolution.
5. **Fulfilled**: otherwise.

`first_response_failed_by` and `resolution_failed_by` say how late each was, in working seconds. They are measured against the current targets, so a change of SLA or priority measures them again.

## Answering "why is this ticket late?"

1. `get_one` the ticket. Read `sla`, `priority`, `service_level_agreement_creation`, `response_by`, `resolution_by`, `first_responded_on`, `total_hold_time` and `overdue_by`.
2. `doc get "HD Service Level Agreement" <sla>` for its targets, working hours and holiday list. Reading it needs the Agent Manager role. Then `doc get "HD Service Holiday List" <holiday_list>` for the dates that don't count.
3. `get_activity_timeline` with `-F 'visible_types:=[{"version": ["status"]}]'` for when the status changed, which explains pauses.
4. `helpdesk.api.ticket_analytics.get_ticket_analytics -f ticket=<t>` sums it up: each target, when it was met, and by how much it was missed.
