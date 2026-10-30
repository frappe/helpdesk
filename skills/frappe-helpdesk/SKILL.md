---
name: frappe-helpdesk
description: Manage a Frappe Helpdesk site from outside the app, through frappectl. Use to find tickets and read their conversations, explain a ticket's SLA, reply, comment, assign, tag, change status or priority, merge or split tickets, look up or create contacts and customers, answer questions about ticket volume, response and resolution times, SLA breaches and feedback, set up agents, teams, SLAs, saved replies and email accounts, or, for a customer's profile, raise, reply to, close and rate their own tickets, when the site runs the Helpdesk app.
---

# Frappe Helpdesk

A Helpdesk site is a set of documents. A ticket (`HD Ticket`) is raised by a contact (`Contact`; `raised_by` is their email), who may belong to a customer (`HD Customer`). The emails on a ticket are `Communication` rows, and the agents' internal notes are `Comment` rows with `comment_type` Comment. Both point back with `reference_doctype` "HD Ticket" and `reference_name`.

A ticket belongs to a team (`agent_group`, an `HD Team`) and is assigned to agents (`HD Agent`), stored as a JSON list in `_assign`. Its `status` (an `HD Ticket Status`) falls in one of three categories, kept in `status_category`: Open, Paused or Resolved. An SLA (`HD Service Level Agreement`) sets when the first response and the resolution are due.

Read and change these documents with `frappectl`. Use the app's own methods where this file names one, because they send the email, thread the reply and keep assignment correct. Use plain document calls for the rest.

## 1. Connect

Ask the human for a frappectl profile, and pass it as `-s <p>`. Check it with `frappectl -s <p> method call helpdesk.api.auth.get_user`: it returns `is_agent`, `is_manager` and `user_teams`.

- **Agent** works tickets: reads, replies, comments, assigns, tags, merges and splits. Agents also manage teams and saved replies, and read contacts and customers.
- **Agent Manager** also manages contacts, customers, SLAs, assignment rules, email accounts and other agents, and sees every agent's numbers.
- **A customer** (`is_agent` false) is a contact working their own tickets. Read `reference/customer.md` and use only the calls there; the rest of this file is for agents.
- Administrator counts as an agent. A deactivated agent (`HD Agent` `is_active` 0) is not one, whatever its roles.

A call refused with "does not have doctype access" needs a role the profile lacks. Tell the human; do not look for a way around it.

- Ticket names are strings: `0320` by default, though a site can change the naming rule. Pass them with `-f`, which always sends a string. `-F` can send a name that looks like a number as an integer, and the method refuses it.
- Some methods accept only GET. Call those with `method call -X GET`. This file marks them.
- `doc create` and `doc update` read stdin when it is not a terminal, and hang in an agent's shell. Pass `--input <file>`, or `< /dev/null` with `--set`.
- Send dict and list arguments as JSON: `-F 'filters:={"agent":"<user>"}'`.
- Sites add their own fields to `HD Ticket`. The ticket template, `HD Ticket Template` "Default", says which ones the app uses, in the order it shows them, and which are required: `method call helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one -f name=Default`. `frappectl -s <p> doctype show "HD Ticket"` lists every field. Check one of them before you guess a field name.

## 2. Find tickets and their data

```sh
frappectl -s <p> doc list "HD Ticket" -f status_category=Open -f agent_group=<team> \
  --fields name,subject,status,priority,_assign,customer,response_by,agreement_status
frappectl -s <p> method call helpdesk.api.search.search -F query=<words>     # subjects, descriptions, emails and comments
frappectl -s <p> doc get "HD Ticket" <ticket>                                 # the ticket's fields
frappectl -s <p> method call frappe.desk.form.activity.get_activity_timeline -f doctype="HD Ticket" -f name=<ticket>   # its emails, notes and changes
frappectl -s <p> method call helpdesk.helpdesk.doctype.hd_ticket.api.get_recent_similar_tickets -f ticket=<ticket>
frappectl -s <p> method call -X GET helpdesk.api.contact.get_contact_info -f name=<contact>
```

The timeline lists everything that happened on the ticket, oldest first. Each activity has a `type`, an `author`, a `timestamp` and its `data`:

- `email`: an email, with its `name`, `sender`, `subject` and `content`.
- `comment`: an internal note, with its `content`.
- `version`: a field change, with `fieldname`, `from` and `to`.
- `log`: the ticket was created, assigned or given an attachment.

To keep only the conversation and the status changes, add `-F 'visible_types:=["email", "comment", {"version": ["status"]}]'`. It holds the latest 20 emails. When `has_more_emails` is true, `method call frappe.desk.form.activity.get_more_email_activities -f doctype="HD Ticket" -f name=<ticket> -F start=20` gives the 20 before them.

Read emails and notes through the timeline: `doc list Communication` returns nothing for an agent.

Common filters (mine, unassigned, overdue, a customer's, a date range): `reference/tickets.md`.

For numbers across many tickets (counts, average response and resolution time, SLA breaches, ratings), use the methods in `reference/reports.md`. They count working hours the way the SLA does, which a `doc list` loop cannot.

## 3. SLA: when is it due, why is it late

`method call helpdesk.helpdesk.doctype.hd_ticket.api.get_one -f name=<ticket>` returns `overdue_by`, with `response` and `resolution` in working seconds past due. It is empty while the ticket is paused. `get_one` also marks the ticket as seen by the caller. The ticket itself has `sla`, `agreement_status` (First Response Due, Resolution Due, Paused, Failed or Fulfilled), `response_by`, `resolution_by`, `first_responded_on`, `on_hold_since`, `total_hold_time`, `first_response_failed_by` and `resolution_failed_by`.

To explain a date, read the SLA named in `sla` with `doc get "HD Service Level Agreement" <sla>` (Agent Manager only): its priorities, working hours and holiday list. Without that role, `get_ticket_analytics` (`reference/tickets.md`) still gives each target and how far it was missed. `reference/sla.md` explains how the SLA is picked and the dates are worked out.

## 4. Common tasks

| Task | Call |
|---|---|
| Pick what to work on next | `doc list "HD Ticket" -f status_category=Open -f '_assign like %<user>%' --fields name,subject,priority,response_by,resolution_by,first_responded_on`. Each ticket is next due by its `response_by`, or by its `resolution_by` once `first_responded_on` is set. Sort on that and put the earliest first. With none of their own, offer their team's unassigned tickets (`reference/tickets.md`). |
| Reply to the customer | `method call reply_via_agent --doctype "HD Ticket" --name <t> -F message="<html>" -f to=<raised_by>`. Only the addresses in `to` are emailed: without it the reply is logged on the ticket and nobody gets it. Add `cc`, `bcc` or `attachments` (File names) when needed. A reply changes the status only when HD Settings `auto_update_status` is on. Read the ticket after sending, tell the human its status, and offer to change it: a Paused status such as Replied stops the SLA clock while you wait for the customer. |
| Add an internal note | `method call new_comment --doctype "HD Ticket" --name <t> -F content="<html>"` |
| Assign an agent | `method call assign_agent --doctype "HD Ticket" --name <t> -f agent=<user>`. It adds to the current assignees and notifies the agent. |
| Change status, priority, team or type | `doc update "HD Ticket" <t> --set status=<status> < /dev/null`. List the statuses with `doc list "HD Ticket Status" --fields name,category`. |
| Reply with a saved reply | `method call helpdesk.api.saved_replies.get_rendered_saved_reply -f ticket_id=<t> -f saved_reply_id=<name>`, send its `message` with `reply_via_agent`, then pass its `actions` to `apply_saved_reply_actions -f ticket_id=<t> -F 'actions:=<actions>'` |
| Tag a ticket | `method call helpdesk.api.tags.update_tags -f doctype="HD Ticket" -f name=<t> -F 'added:=[{"name": "<tag>"}]'`. A new tag is created. To remove one, send `-F 'removed:=["<tag>"]'` instead. |
| Create a ticket for a contact | `doc create "HD Ticket" --input <file>` with `subject`, `description` (HTML), `raised_by` (their email), `contact` and, when they have one, `customer`. See `reference/tickets.md`. |
| Merge two tickets | `method call helpdesk.helpdesk.doctype.hd_ticket.api.merge_ticket -f source=<t> -f target=<t>`. It returns `{}`; `doc get` the source to see `merged_with`. |
| Split a ticket | `method call helpdesk.helpdesk.doctype.hd_ticket.api.split_ticket -f subject=<s> -f communication_id=<email>`. The email and every email and comment after it move to a new ticket. |
| Find a contact | `method call -X GET helpdesk.api.contact.search_contacts -f txt=<text>` |
| Create a contact | `method call helpdesk.api.contact.create_contact -F 'doc:={"first_name": "...", "last_name": "...", "email": "..."}'`. Put `"customer": "<c>"` in `doc` to add them to that customer. Nobody is emailed unless you add `-F invite:=true`, which invites them to the portal instead. |
| Create a customer | `method call helpdesk.api.customer.create_customer -F 'customer:={"customer_name": "...", "domain": "..."}'`. Add `-F 'primary_contact:={"email": "...", "first_name": "..."}'` to create and invite its first contact. |
| Add contacts to a customer | `method call add_contacts --doctype "HD Customer" --name <c> -F 'contacts:=["<contact or email>"]'`. A contact with a user is added. One without a user is emailed an invite instead, and comes back under `invite_result`, not `added`. With `-F invite:=false`, every contact is added and nobody is emailed; a missing contact can be created with its customer in one step ("Create a contact"). |
| Set up the helpdesk | `reference/setup.md` |

For anything this file doesn't cover, find the method: `frappectl -s <p> method search -q "<one or two words>"` (every word must match), then `method show <path>` for its arguments, who may call it and what it returns. Read that before you call it, and still mind the traps below. When nothing matches, the task is usually a field change: use `doctype show` and the `doc` commands. Search is for agents; a customer's profile is refused it, and a site on an older Frappe doesn't have it.

## 5. Traps

- **A reply emails the customer** when HD Settings `enable_reply_email_via_agent` is on. Show the human the reply and ask before you send it.
- **Never insert a `Communication` to reply.** The ticket still updates, but no email goes out and the reply is not threaded. An agent replies with `reply_via_agent`; a customer replies with `create_communication_via_contact` (`reference/customer.md`).
- **A merge cannot be undone.** It copies the source's emails, comments and files into the target, closes the source with `merged_with` set, and posts a reply on the source saying so, which is not emailed. `doc get` both first: when their `raised_by` or `customer` differ, tell the human, because the target's contact will see the source's emails. Ask first.
- **Deletes can take tickets with them.** `delete_contact` and `delete_customer` with `delete_tickets` delete every linked ticket. Ask first, and name what will go.
- **Every save picks the SLA again and recalculates its dates.** Changing the priority, or a field an SLA condition reads, can switch the ticket to another SLA.
- **A contact sees a ticket** only when they are its `contact`, its `raised_by` or its owner. A customer's managers also see every ticket of that `customer`. Set these right on a ticket you create.
- **A ticket you create** records your user, not the contact, as the sender of its first email.
- **Team restrictions hide tickets.** With HD Settings `restrict_tickets_by_agent_group` on, an agent sees only their teams' tickets. A ticket that "does not exist" may be in another team.
- **Saved reply templates** see the ticket's fields and the signed-in user's `User` fields. Where both have a field (`name`, `owner`, `creation`), the user's wins: `{{ name }}` is the agent's user, not the ticket. Use `{{ subject }}` and other ticket-only fields.

## Reference

- `reference/tickets.md`: ticket fields, filters, the conversation, history, feedback, creating, merging and splitting.
- `reference/sla.md`: which SLA applies and how its due dates, pauses and breaches are worked out.
- `reference/reports.md`: ticket volume, response and resolution times, SLA breaches and ratings, for an agent, a team, a customer or a contact.
- `reference/customer.md`: everything a customer's profile can do, and the rules the portal enforces.
- `reference/setup.md`: agents, teams and assignment, SLAs and holiday lists, ticket types and priorities, saved replies and email accounts.
