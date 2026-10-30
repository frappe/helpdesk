# Setting up the helpdesk

Most of this needs the Agent Manager role. Agents can manage teams and saved replies.

## Agents

Invite agents by email. They get a link to set a password.

```sh
frappectl -s <p> method call frappe.core.api.user_invitation.invite_by_email \
  -f emails="jane@example.com,raj@example.com" -F 'roles:=["Agent"]' \
  -f redirect_to_path=/helpdesk -f app_name=helpdesk
```

`roles` is `["Agent"]`, `["Agent", "Agent Manager"]`, or both plus `"System Manager"` for an admin. To change an existing agent's role:

```sh
frappectl -s <p> method call helpdesk.helpdesk.doctype.hd_agent.hd_agent.update_agent_role -f user=<user> -f new_role=Manager
```

`new_role` is `Agent` or `Manager`. To deactivate an agent, set `is_active` to 0 on their `HD Agent`.

## Teams and assignment

```sh
frappectl -s <p> doc create "HD Team" --input team.json
```

```json
{"team_name": "Billing", "users": [{"user": "jane@example.com"}, {"user": "raj@example.com"}]}
```

A new team gets an `Assignment Rule` named `<team> - Support Rotation`, which assigns the team's tickets to its members in turn. Changing the team's `users` updates the rule. Edit the rule itself (Agent Manager) to change how tickets are shared out.

`doc update "HD Team" <team> --input team.json` replaces the whole `users` list with the one you send. To add or remove one agent, `doc get` the team first and send its full list with that change. To move an agent, do that on both teams. The reply marks each row `__unsaved`; the team is saved all the same, as `doc get` shows. Their open tickets stay assigned to them; reassign those only if the human asks.

## SLAs

An SLA needs a holiday list. Create the list first:

```json
{
  "holiday_list_name": "India 2026",
  "from_date": "2026-01-01",
  "to_date": "2026-12-31",
  "holidays": [{"holiday_date": "2026-01-26", "description": "Republic Day"}]
}
```

```sh
frappectl -s <p> doc create "HD Service Holiday List" --input holidays.json
frappectl -s <p> doc create "HD Service Level Agreement" --input sla.json
```

```json
{
  "service_level": "Acme Premium",
  "description": "Faster targets for Acme",
  "holiday_list": "India 2026",
  "condition": "doc.customer == 'Acme'",
  "condition_json": "[[\"customer\", \"==\", \"Acme\"]]",
  "apply_sla_for_resolution": 1,
  "default_ticket_status": "Open",
  "ticket_reopen_status": "Open",
  "priorities": [
    {"priority": "High", "response_time": 3600, "resolution_time": 28800, "default_priority": 1},
    {"priority": "Low", "response_time": 14400, "resolution_time": 86400}
  ],
  "support_and_resolution": [
    {"workday": "Monday", "start_time": "09:00:00", "end_time": "18:00:00"},
    {"workday": "Tuesday", "start_time": "09:00:00", "end_time": "18:00:00"}
  ]
}
```

- Times are in seconds of working time.
- `condition` is what the ticket is matched on. `condition_json` is the same condition as the app's filter editor shows it; set both so the app can display and edit it.
- Set `default_sla` 1 instead of a condition for the SLA that catches every other ticket. Set `rank` to choose between SLAs whose conditions overlap. `sla.md` explains the order.
- A ticket whose priority has no row in the SLA does not get it.

## Ticket priorities, types and statuses

```sh
frappectl -s <p> doc create "HD Ticket Priority" --input priority.json   # {"name": "Critical", "level": "Urgent"}
frappectl -s <p> doc create "HD Ticket Type" --input type.json           # {"name": "Refund", "priority": "High"}
```

- A priority's `level` is Urgent, High, Medium or Low. Add the new priority to every SLA that should cover it, or its tickets get no SLA.
- A ticket type's `priority` is the priority its new tickets get when none is given.
- Statuses (`HD Ticket Status`, Agent Manager) have `label_agent`, `label_customer` (what the customer sees), and a `category`: Open, Paused or Resolved. The category decides how the SLA treats the status.

## Saved replies

```json
{
  "title": "Refund issued",
  "message": "<p>We have refunded you for \"{{ subject }}\".</p>",
  "scope": "Team",
  "teams": [{"team": "Billing"}],
  "actions": "[{\"action_type\": \"Set Status\", \"value\": \"Resolved\"}, {\"action_type\": \"Add Tag\", \"value\": \"refund\"}]"
}
```

```sh
frappectl -s <p> doc create "HD Saved Reply" --input reply.json
```

- `scope` is Global (every agent), Team (the agents in `teams`) or Personal (only you).
- `message` is a Jinja template over the ticket's fields. See the saved reply trap in `SKILL.md`.
- `actions` is a JSON string. `action_type` is Set Status, Set Priority, Set Team, Set Ticket Type, Assign Agent, Assign to Me (no value), Add Tag, Remove Tag or Add Comment. Each runs when the reply is sent.

## Email accounts

Ask the human to add the support inbox in the app, under Settings, Email Accounts. Connecting needs the mailbox's password or an OAuth sign-in, which should not pass through your shell.
