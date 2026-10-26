# Tickets

## Fields

| Field | What it holds |
|---|---|
| `name` | The ticket number |
| `subject`, `description` | The title, and the first message as HTML |
| `status`, `status_category` | An `HD Ticket Status`, and its category: Open, Paused or Resolved |
| `priority`, `ticket_type` | An `HD Ticket Priority` and an `HD Ticket Type` |
| `agent_group` | The team, an `HD Team` |
| `_assign` | The assigned agents, as a JSON list of users |
| `raised_by`, `contact`, `customer` | The contact's email, their `Contact`, and their `HD Customer` |
| `first_responded_on`, `resolution_date` | When an agent first replied, and when the ticket was resolved |
| `sla` and its dates | See `sla.md` |
| `feedback_rating`, `feedback`, `feedback_extra` | The customer's rating from 0 to 1 (1 is five stars), the option they picked, and their comment |
| `is_merged`, `merged_with` | Set on a ticket merged into another |
| `ticket_split_from` | Set on a ticket split from another |
| `_user_tags` | The tags, comma-separated |

Sites add their own fields. `frappectl -s <p> doctype show "HD Ticket"` lists them all.

## Filters

```sh
frappectl -s <p> doc list "HD Ticket" -f status_category=Open -f '_assign like %<user>%'        # open and mine
frappectl -s <p> doc list "HD Ticket" --filters-json '[["_assign","is","not set"],["status_category","=","Open"]]'  # unassigned
frappectl -s <p> doc list "HD Ticket" -f agreement_status=Failed -f status_category=Open        # open and past their SLA
frappectl -s <p> doc list "HD Ticket" -f customer=<customer> --order-by "creation desc"
frappectl -s <p> doc list "HD Ticket" -f 'creation>=2026-01-01' -f 'creation<2026-02-01'
frappectl -s <p> api method/frappe.client.get_count -f doctype="HD Ticket" -F 'filters:={"status_category": "Open"}'
```

Add `--fields` with the columns you need, and `--all` to read every page.

## The conversation

`get_one` returns the ticket with its emails in `communications`, oldest first. Each has `name`, `sender`, `recipients`, `cc`, `bcc`, `subject`, `content` and `creation`. The internal notes are `Comment` rows:

```sh
frappectl -s <p> doc list Comment -f reference_doctype="HD Ticket" -f reference_name=<t> -f comment_type=Comment \
  --fields content,owner,creation --order-by "creation asc"
```

## History and numbers for one ticket

- `method call -X GET helpdesk.helpdesk.doctype.hd_ticket.api.get_timeline_changes -f name=<t>` lists each status change, with who made it and when.
- `method call helpdesk.api.ticket_analytics.get_ticket_analytics -f ticket=<t>` gives the ticket's SLA timeline: when it was created, first answered and resolved, against what target, and by how much it missed.

## Creating a ticket

Write the ticket to a file and create it:

```json
{
  "subject": "Refund not received",
  "description": "<p>I was charged twice for my order.</p>",
  "raised_by": "jane@example.com",
  "contact": "Jane Doe",
  "customer": "Acme",
  "priority": "High",
  "agent_group": "Billing"
}
```

```sh
frappectl -s <p> doc create "HD Ticket" --input ticket.json
```

Only `subject` and `raised_by` are needed: `contact` is filled in from a contact with that email, and `status` and `priority` from the defaults. Create the contact first with `create_contact` when there is none. A new ticket can send the contact an acknowledgement email, depending on the site's email settings.

## Merging and splitting

- **Merge** (`merge_ticket -f source=<t> -f target=<t>`): the source's emails, comments and files are copied into the target. The source is closed, with `is_merged` 1 and `merged_with` set, and the customer is emailed on it. A ticket already merged cannot be merged again. There is no unmerge.
- **Split** (`split_ticket -f subject=<s> -f communication_id=<email>`): the email you name, and every email, comment and file after it, move to a new ticket with that subject. The new ticket has `ticket_split_from` set. It returns the new ticket's name. Take the email's `name` from `get_one`'s `communications`.
