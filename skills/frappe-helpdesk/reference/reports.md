# Numbers across tickets

Agents only. A customer's profile is refused ("You are not permitted to access this resource."). For a customer, read the due dates on their own tickets as `customer.md` shows.

These methods count response and resolution time in the SLA's working hours, and read the right statuses for each category. Use them before you add up `doc list` rows yourself. Times come back in seconds.

## The dashboard: the whole helpdesk, a team or an agent

```sh
frappectl -s <p> method call helpdesk.api.dashboard.get_dashboard_data -f dashboard_type=number_card \
  -F 'filters:={"from_date": "2026-01-01", "to_date": "2026-01-31", "team": "<team>", "agent": "<user>"}'
```

| `dashboard_type` | Returns |
|---|---|
| `number_card` | Tickets created, % SLA fulfilled, average first response, average resolution and average feedback, each with the change from the period before |
| `trend` | Tickets opened and closed, and the SLA fulfilled rate, per day |
| `master` | Ticket counts by team, type, priority and other breakdowns |
| `tags` | The most used tags |

All four filters are optional; the dates default to the last 30 days. An agent who is not an Agent Manager can only pass their own user as `agent`, with no `team`. Use their email: `@me` is refused.

## A customer or a contact

```sh
frappectl -s <p> method call helpdesk.api.ticket_stats.get_ticket_stats -f dt="HD Customer" -f dn=<customer> -f period="last 3 months"
```

`dt` is `HD Customer` or `Contact`. `period` is `last week`, `last month`, `last 3 months` or `last 6 months`. It returns the customer's ratings, their SLA violations per week, and their average first response and resolution time. `get_sla_violations`, `get_avg_first_response_time` and `get_avg_resolution_time` in the same module return one of those each.

`get_feedback_received -f scope=<customer|contact|agent> -f value=<name>` gives the count of each rating from 1 to 5 and the average. Only an Agent Manager can read another agent's.

## The signed-in agent

All in `helpdesk.api.agent_home.agent_home`, for the profile's own user:

| Method | Returns |
|---|---|
| `get_agent_tickets -f period="last month"` | Tickets assigned to them, per day, against the period before. `period` is `last 7 days`, `last month` or `last 3 months`. |
| `get_avg_time_metrics -f period=6m` | Their average first response and resolution time per month. `period` is `3m`, `6m` or `1y`, or pass `from_date` and `to_date`. |
| `get_pending_tickets -f ticket_type=upcoming_sla` | Their next 6 tickets by SLA due date, and the total. `ticket_type` can also be `new_tickets` or `pending` (waiting on their reply). For the full list, use `doc list` with the filters in `tickets.md`. |
| `get_recent_activity` | Their latest action on each ticket over the last 3 days: replied, commented or updated |
