# Working as a customer

A customer is a contact with a user on the site. They raise tickets and talk to the support team through them. A contact can belong to one or more organizations (`HD Customer`), as a Member or a Manager. The frappectl notes in `SKILL.md` apply here too.

## 1. What a customer sees

`frappectl -s <p> method call helpdesk.api.customer.get_portal_account` returns the user and their organizations, with their `role` in each.

- A contact sees the tickets where they are the `contact`, the `raised_by` or the owner. An organization's Managers also see all of its tickets.
- Agents' internal notes are never visible, and some ticket fields are hidden. `get_list` leaves out a hidden field without saying so.
- Use the `frappe.client` methods below to read and change tickets, not frappectl's `doc` commands. Sites that block API paths for customers refuse `doc`, and allow the methods the portal itself calls.
- A call refused with "Access not allowed for this URL" comes from a site that blocks API paths for customers on an older Helpdesk. Tell the human; the site's admin has to update it.

## 2. Find tickets

```sh
frappectl -s <p> method call frappe.client.get_list -f doctype="HD Ticket" -F 'fields:=["name","subject","status","modified"]' \
  -F 'filters:={"status_category": "Open"}' -f order_by="modified desc"
frappectl -s <p> method call frappe.client.get_list -f doctype="HD Ticket" -F 'fields:=["name","subject","status","raised_by"]' \
  -F 'filters:={"customer": "<organization>"}'                                  # a Manager's view
frappectl -s <p> method call frappe.client.get_list -f doctype="HD Ticket" -F 'fields:=["name","subject","status"]' \
  -F 'filters:={"subject": ["like", "%<words>%"]}'                              # search by subject
frappectl -s <p> method call frappe.client.get -f doctype="HD Ticket" -f name=<ticket>      # the ticket's fields
frappectl -s <p> method call frappe.desk.form.activity.get_activity_timeline -f doctype="HD Ticket" -f name=<ticket>   # its emails and status changes
```

The ticket has `response_by` and `resolution_by`, when the team is due to answer and to resolve, and `first_responded_on`. The timeline lists the emails from both sides (`email`, with `sender` and `content`) and the changes to fields the customer can see (`version`), oldest first. It holds the latest 20 emails; `SKILL.md` says how to get older ones.

A status falls in one of three categories, kept in `status_category`: Open, Paused or Resolved. Paused usually means the team is waiting for the customer. The app shows a status by its `label_customer` when it has one: `method call frappe.client.get_list -f doctype="HD Ticket Status" -F 'fields:=["name","label_customer","category"]'`.

## 3. Common tasks

| Task | Call |
|---|---|
| Raise a ticket | First get the template's fields (next row). Write the subject and description from what the human said. Write both out in your message to the human, ask "Raise this?" and wait for a yes, even when the human already asked you to raise it. Then `method call helpdesk.helpdesk.doctype.hd_ticket.api.new -F 'doc:={"subject": "...", "description": "<p>...</p>"}'`. It returns the new ticket. |
| Fields a new ticket asks for | `method call helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one -f name=Default`. Its `fields` are the portal's new-ticket form, in order, each with `label`, `fieldtype`, `options`, `placeholder` (the hint the portal shows) and `required`. Ask the human for each one with `required` 1, or whose `mandatory_depends_on` (such as `eval:doc.ticket_type=="Bug"`) is true for the values so far, and put them in `doc`. Skip any whose `depends_on` is false. The portal checks these; the server does not. A field mandatory on the doctype itself is refused by the server with "Value missing for HD Ticket: <field>": ask for it and try again. Add `customer` when the contact is in more than one organization. |
| Reply | `method call create_communication_via_contact --doctype "HD Ticket" --name <t> -F message="<html>"`. The ticket moves back to an Open status. |
| Close a ticket | First check `method call helpdesk.api.config.get_config`. If `is_feedback_mandatory` is 1 and an agent has replied on the ticket, use "Close and rate it" instead. Otherwise `method call frappe.client.set_value -f doctype="HD Ticket" -f name=<t> -f fieldname=status -f value=Closed` |
| Close and rate it | Ask the human for 1 to 5 stars. List the options for that rating with `method call frappe.client.get_list -f doctype="HD Ticket Feedback Option" -F 'fields:=["name","label"]' -F 'filters:={"rating": <stars / 5>, "disabled": 0}'` (3 stars is `0.6`, 4 is `0.8`), and have them pick one. Then `method call frappe.client.set_value -f doctype="HD Ticket" -f name=<t> -F 'fieldname:={"status": "Closed", "feedback": "<option name>", "feedback_extra": "<comment, optional>"}'`. The option is required; it sets the rating. |
| See an organization | `method call helpdesk.api.customer.get_organization -f customer=<organization>`: its members and their roles |
| Manage an organization (Managers) | `invite_members -f customer=<o> -F 'emails:=["..."]' -F is_manager:=false`, `update_member_role -f customer=<o> -f contact=<c> -F is_manager:=true` and `remove_member -f customer=<o> -f contact=<c>`, all in `helpdesk.api.customer`. The site's HD Settings must allow it. |
| Team-wide numbers (average response time, SLA %) | Not for customers: the report methods refuse them. Offer what their own tickets show instead: `first_response_time` (in seconds), `response_by` and `first_responded_on` from "Find tickets". |
| Search the knowledge base | `method call -X GET helpdesk.api.knowledge_base.search_articles -f query=<words>` |
| Browse it | `-X GET` `get_categories`, then `get_articles -f category=<category>`, then `get_article -f name=<article>`, all in `helpdesk.api.knowledge_base` |

## 4. Traps

- **Replies and ratings go to the team.** Show the human the message, or the rating, and ask before you send it.
- **A customer can only close a ticket.** Any other change of status is refused. So are changes to other fields after the ticket is raised ("You cannot change ... after the ticket is raised"), unless the site's ticket template lets customers edit that field after creation.
- **A closed or rated ticket is final.** It takes no reply and no change. Raise a new ticket, and mention the old number in it.
- **A rating cannot be changed**, and cannot be given while raising a ticket.
- **Closing may need a rating.** When `method call helpdesk.api.config.get_config` returns `is_feedback_mandatory` 1 and an agent has replied on the ticket, closing without a rating fails with "Ticket must be resolved with a feedback". Ask for the rating first and use "Close and rate it". If no agent has replied, the ticket closes without one.
- **Tickets are raised as the profile's user.** You cannot raise one on behalf of someone else.
- **The knowledge base search returns nothing** on sites without its search index. Browse the categories instead.
