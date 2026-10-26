---
name: frappe-helpdesk-customer
description: Act as a customer of a Frappe Helpdesk site, through frappectl. Use to raise a support ticket, check a ticket's status and when it is due, read and reply to the conversation, close and rate a ticket, see the customer's organization and its members, or read the knowledge base, when the frappectl profile is a contact on a site running the Helpdesk app, not an agent.
---

# Frappe Helpdesk for customers

A customer is a contact (`Contact`) with a user on the site. They raise tickets (`HD Ticket`) and talk to the support team through them. The emails on a ticket, theirs and the agents', are `Communication` rows. A contact can belong to one or more organizations (`HD Customer`), as a Member or a Manager.

For an agent's profile, use the `frappe-helpdesk-agent` skill instead.

## 1. Connect

Ask the human for a frappectl profile, and pass it as `-s <p>`. Check it with `frappectl -s <p> method call helpdesk.api.customer.get_portal_account`: it returns the user and their organizations, with their `role` in each. If `helpdesk.api.auth.get_user` says `is_agent` is true, this is the wrong skill.

- A contact sees the tickets where they are the `contact`, the `raised_by` or the owner. An organization's Managers also see all of its tickets.
- Agents' internal notes are never visible, and some ticket fields are hidden. `doc list` leaves out a hidden field without saying so.
- Ticket names are numbers. Pass them with `-f` (always a string), not `-F`, which sends `4` as an integer and the method refuses it.
- Some methods accept only GET. Call those with `method call -X GET`. This file marks them.
- `doc update` reads stdin when it is not a terminal, and hangs in an agent's shell. Pass `< /dev/null` with `--set`.
- A call refused with "Access not allowed for this URL" comes from a site that blocks API paths for customers on an older Helpdesk. Tell the human; the site's admin has to update it.

## 2. Find tickets

```sh
T=helpdesk.helpdesk.doctype.hd_ticket.api
frappectl -s <p> doc list "HD Ticket" -f status_category=Open --fields name,subject,status,modified --order-by "modified desc"
frappectl -s <p> doc list "HD Ticket" -f customer=<organization> --fields name,subject,status,raised_by   # a Manager's view
frappectl -s <p> method call $T.get_one -f name=<ticket>                       # the ticket and every email on it
frappectl -s <p> method call -X GET $T.get_timeline_changes -f name=<ticket>   # each status change, by whom and when
```

`get_one` has `response_by` and `resolution_by`, when the team is due to answer and to resolve, and `first_responded_on`. Its `communications` are oldest first, with `sender`, `content` and `creation`.

A status falls in one of three categories, kept in `status_category`: Open, Paused or Resolved. Paused usually means the team is waiting for the customer. The app shows a status by its `label_customer` when it has one: `doc list "HD Ticket Status" --fields name,label_customer,category`.

## 3. Common tasks

| Task | Call |
|---|---|
| Raise a ticket | `method call $T.new -F 'doc:={"subject": "...", "description": "<p>...</p>"}'`. It returns the new ticket. |
| See what else a new ticket can carry | `method call helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one -f name=Default`. Its `fields` (such as `priority` and `ticket_type`) can go in `doc`. Add `customer` when the contact is in more than one organization. |
| Reply | `method call create_communication_via_contact --doctype "HD Ticket" --name <t> -F message="<html>"`. The ticket moves back to an Open status. |
| Close a ticket | `doc update "HD Ticket" <t> --set status=Closed < /dev/null` |
| Close and rate it | Add `--set feedback=<option> --set feedback_extra="<comment>"`. List the options with `doc list "HD Ticket Feedback Option" -f disabled=0 --fields name,rating`; `rating` runs from 0.2 (one star) to 1 (five). |
| See an organization | `method call helpdesk.api.customer.get_organization -f customer=<organization>`: its members and their roles |
| Manage an organization (Managers) | `invite_members -f customer=<o> -F 'emails:=["..."]' -F is_manager:=false`, `update_member_role -f customer=<o> -f contact=<c> -F is_manager:=true` and `remove_member -f customer=<o> -f contact=<c>`, all in `helpdesk.api.customer`. The site's HD Settings must allow it. |
| Search the knowledge base | `method call -X GET helpdesk.api.knowledge_base.search_articles -f query=<words>` |
| Browse it | `-X GET` `get_categories`, then `get_articles -f category=<category>`, then `get_article -f name=<article>`, all in `helpdesk.api.knowledge_base` |

## 4. Traps

- **Replies and ratings go to the team.** Show the human the message, or the rating, and ask before you send it.
- **A customer can only close a ticket.** Any other change of status, and changes to its priority, team or other fields after it is raised, are refused with "You cannot change ... after the ticket is raised".
- **A closed or rated ticket is final.** It takes no reply and no change. Raise a new ticket, and mention the old number in it.
- **A rating cannot be changed**, and cannot be given while raising a ticket.
- **Closing may need a rating.** When the site requires feedback, closing a resolved ticket that an agent answered without one fails with "Ticket must be resolved with a feedback".
- **Tickets are raised as the profile's user.** You cannot raise one on behalf of someone else.
- **The knowledge base search returns nothing** on sites without its search index. Browse the categories instead.
