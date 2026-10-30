# Numbers across tickets

Agents only. A customer's profile is refused ("You are not permitted to access this resource."). For a customer, read the due dates on their own tickets as `customer.md` shows.

These methods count response and resolution time in the SLA's working hours, and read the right statuses for each category. Use them before you add up `doc list` rows yourself. Read each time's unit from the result: the dashboard gives first response in hours and resolution in days.

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

All four filters are optional; the dates default to the last 30 days. An agent who is not an Agent Manager can only pass their own user as `agent`, with no `team`. Use their email: `@me` is refused. A `delta` of null means the period before had nothing to compare with, not that nothing changed. Here `team` means the tickets in that team. % SLA fulfilled counts only resolved tickets that have an SLA.

## Compare agents (Agent Managers)

```sh
frappectl -s <p> method call helpdesk.api.ticket_stats.get_agent_performance -f team=<team> -f from_date=2026-01-01 -f to_date=2026-01-31
```

Leave out `team` for every active agent, and the dates for the last 30 days. `team` picks the team's members, not the tickets in that team: an empty list means the team has no members, so check `doc get "HD Team" <team>` and tell the human. It returns one row per agent, with `agent_name`, `tickets`, `sla_fulfilled_percent`, `avg_first_response_hours`, `avg_resolution_days` and `avg_feedback_stars`, worked out as the dashboard does. Only an Agent Manager can call it; tell anyone else that comparing agents needs that role.

To answer "who is the best or worst":

1. Show the whole table, with each agent's ticket count. `tickets` counts all of them; `sla_fulfilled_percent` counts only the resolved ones.
2. Before you rank, leave out any agent with fewer than half the median `tickets` of the table, and say why: a 5.0 rating from one ticket says little.
3. Rank the rest. Unless the human says otherwise, rank on `sla_fulfilled_percent`. On a tie, the lower `avg_first_response_hours` wins, then the lower `avg_resolution_days`, then the higher `avg_feedback_stars`. Say what you ranked on. Most tickets handled gives a different answer; offer it.
4. Tickets count for the agents assigned now. A reassigned ticket counts only for its latest agent, and one with two assignees counts for both.

## A customer or a contact

```sh
frappectl -s <p> method call helpdesk.api.ticket_stats.get_ticket_stats -f dt="HD Customer" -f dn=<customer> -f period="last 3 months"
```

`dt` is `HD Customer` or `Contact`. `period` is `last week`, `last month`, `last 3 months` or `last 6 months`. It returns the customer's ratings, their SLA violations per week, and their average first response and resolution time. `get_sla_violations`, `get_avg_first_response_time` and `get_avg_resolution_time` in the same module return one of those each.

`get_feedback_received -f scope=<customer|contact|agent> -f value=<name>` gives the count of each rating from 1 to 5 and the average. Only an Agent Manager can read another agent's.

## The signed-in agent

For their own % SLA fulfilled, average first response, resolution and feedback over any dates, use the dashboard above with `agent` set to their email. The rest are all in `helpdesk.api.agent_home.agent_home`, for the profile's own user:

| Method | Returns |
|---|---|
| `get_agent_tickets -f period="last month"` | Tickets assigned to them, per day, against the period before. `period` is `last 7 days`, `last month` or `last 3 months`. |
| `get_avg_time_metrics -f period=6m` | Their average first response and resolution time per month. `period` is `3m`, `6m` or `1y`, or pass `from_date` and `to_date`. |
| `get_pending_tickets -f ticket_type=upcoming_sla` | Their next 6 tickets by SLA due date, and the total. `ticket_type` can also be `new_tickets` or `pending` (waiting on their reply). For the full list, use `doc list` with the filters in `tickets.md`. |
| `get_recent_activity` | Their latest action on each ticket over the last 3 days: replied, commented or updated |
