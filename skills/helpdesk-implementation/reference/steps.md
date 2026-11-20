# Steps

Each step has a key, a title to rewrite in their words, when it applies, what you do, what they do, and a **Done when** check. A check is a read on the site's data. Never mark a step done on someone's word alone, except where the step says so.

"Setup users" and "agreed" values come from the plan (`plan.md`). "After setup" means after the date the last setup step was marked done. The calls are in `frappe-helpdesk` and its `reference/setup.md`.

Always in the plan: `basics`, `agents`, `assignment`, `ticket-types`, `first-answer`, `first-resolved`, `regular-use`, `weekly-use`. Add the rest when the interview turns them on.

## Set up

### `basics`: Customers see your name

- **Do:** set `HD Settings` `brand_name` and `brand_logo` (a file they give you). Decide with them what to do with the install defaults listed in the traps of `SKILL.md`, and with the welcome ticket.
- **Done when:** `HD Settings` `brand_name` is the agreed name.

### `inbox`: Emails to your support address become tickets

- **When:** customers email them.
- **They do:** add the mailbox in Helpdesk, under Settings, Email Accounts. They type the password or sign in there. Never take it in chat.
- **Do:** check the result. Then ask them to send one test email from an address they own.
- **Done when:** an `Email Account` with `enable_incoming` 1 and `enable_outgoing` 1, whose `append_to` is `HD Ticket` or that has an `imap_folder` row with `append_to` `HD Ticket`. After the test, an `HD Ticket` with `email_account` set to that account.

### `agents`: Everyone who answers customers can sign in

- **Agree:** names, work emails, and who manages.
- **Do:** show the list, then call `frappe.core.api.user_invitation.invite_by_email` with `emails`, `roles` (`["Agent"]`, or `["Agent", "Agent Manager"]` for a manager), `redirect_to_path` `/helpdesk` and `app_name` `helpdesk`.
- **They do:** each person accepts the email and signs in.
- **Done when:** an `HD Agent` with `is_active` 1 for each agreed person, whose `User` has a `last_login`.

### `assignment`: Each new ticket gets an owner

- **Agree:** who takes new tickets, in their words: "everyone in turn", "Priya takes billing".
- **Do:** with one group, enable the base rule named in `HD Settings` `base_support_rotation` and set its `users`. For a split by kind of ticket, create an `Assignment Rule` with `document_type` `HD Ticket`, a `description`, `rule`, `users`, `assignment_days`, and both `assign_condition` (such as `status == 'Open' and ticket_type == 'Billing'`) and `assign_condition_json`. For teams, see `teams`.
- **Done when:** at least one `Assignment Rule` on `HD Ticket` with `disabled` 0 and users, matching what was agreed. After setup, new tickets have `_assign` set.

### `teams`: Tickets reach the right group

- **When:** separate groups handle different kinds of issues.
- **Do:** create each `HD Team` with `team_name` and `users`, and disable or rename the install teams they do not need. Each team makes its own assignment rule. Agree how a ticket gets its team (`agent_group`): an agent sets it, or an assignment rule condition does.
- **Done when:** an `HD Team` with `disabled` 0 and members for each agreed team, and each team's `assignment_rule` is enabled.

### `ticket-types`: Ticket types and priorities match your work

- **Agree:** their kinds of issue and their urgency levels.
- **Do:** create, rename or disable `HD Ticket Type` (name, `priority`, `disabled`) and `HD Ticket Priority` (name, `level`). Keep `Unspecified`: it is the system's fallback. Set `HD Settings` `default_ticket_type` and `default_priority`.
- **Done when:** the enabled `HD Ticket Type` names equal the agreed list plus `Unspecified`, and `default_ticket_type` and `default_priority` are set.

### `statuses`: Ticket statuses say what you mean

- **When:** they need more than Open, Replied, Resolved and Closed, or want customers to see other words.
- **Do:** create or edit `HD Ticket Status` with `label_agent`, `label_customer` and `category` (Open, Paused or Resolved). The category decides how the SLA clock treats it.
- **Done when:** the enabled `HD Ticket Status` labels equal the agreed list, each with the agreed category.

### `sla`: Your response promise is tracked

- **When:** they promise response or resolution times.
- **Agree:** working days and hours, breaks, holidays, and a response and resolution time per priority.
- **Do:** add their holidays to an `HD Service Holiday List`. Then edit the default SLA (or create one with `default_sla` 1) as `reference/setup.md` in `frappe-helpdesk` shows. Times are in seconds of working time.
- **Done when:** an `HD Service Level Agreement` with `enabled` 1 and `default_sla` 1, a `priorities` row for each agreed priority with the agreed times, `support_and_resolution` rows for the agreed days, and a `holiday_list` that holds the agreed holidays.

### `saved-replies`: Your common answers are one click away

- **When:** they write the same answers again and again.
- **Agree:** which answers, and their own wording or past replies.
- **Do:** draft each `HD Saved Reply` (`title`, `message`, `scope`) in their words, using only fields the ticket has. Set `scope` Global or Team only when they agree.
- **Done when:** an `HD Saved Reply` for each agreed title.

### `customers`: Your customers are in

- **When:** they serve companies, or have a customer list.
- **Do:** create `HD Customer` records with `customer_name` and `domain`, and their contacts with `helpdesk.api.contact.create_contact` with `customer` in `doc` and no invite. See "Set up" in `SKILL.md` for the size rule.
- **Done when:** an `HD Customer` for each agreed customer, and the agreed contacts linked in its `contacts` table.

### `knowledge-base`: Your help articles are live

- **When:** they have FAQs or help pages.
- **Do:** draft `HD Article` records (`title`, `category`, `content`) from their own pages. They edit and publish.
- **Done when:** the agreed number of `HD Article` records with `status` Published.

### `portal`: Customers can raise and follow their tickets

- **When:** they want customers to log in.
- **Agree:** who gets access, and whether anyone may raise a ticket (`HD Settings` `allow_anyone_to_create_tickets`).
- **Do:** set the settings. Then invite the agreed contacts: a portal invite emails a customer, so it is a one-way door.
- **Done when:** the settings match, and each agreed contact has a `user`.

### `feedback`: Customers rate closed tickets

- **When:** they want ratings.
- **Do:** set `HD Settings` `enable_email_ticket_feedback` 1 and `send_email_feedback_on_status` to the agreed status. Read the `HD Ticket Feedback Option` labels with them.
- **Done when:** `enable_email_ticket_feedback` is 1 and `send_email_feedback_on_status` is set.

## Start using

Their agents do these. You explain how, then check.

### `first-answer`: Your team answers a real ticket

- **Done when:** an `HD Ticket` created after setup, with `first_responded_on` set, whose first reply (`Communication` with `sent_or_received` Sent) came from someone who is not a setup user.

### `first-resolved`: Your team resolves a real ticket

- **Done when:** an `HD Ticket` created after setup with `status_category` Resolved, last changed by someone who is not a setup user.

### `sla-met`: You keep your promise

- **When:** `sla` is on.
- **Done when:** five or more tickets created after setup with `agreement_status` Fulfilled. Five is a starting guess.

### `saved-reply-used`: Your team uses saved replies

- **When:** `saved-replies` is on.
- **Done when:** the agent says so. There is no reliable record of it; say that.

## Habit and live

### `regular-use`: Every issue goes through Helpdesk

- **Done when:** tickets created in the last 7 days reach at least half the weekly volume they gave. Half is a starting guess: agree the number.

### `weekly-use`: Helpdesk is part of your week

- **Done when:** agents who are not setup users replied to or changed tickets in three different calendar weeks.

### `live`: Helpdesk is working, in your words

- **Done when:** their live condition passes on the data, and agents who are not setup users worked tickets in the last 7 days. Check at 30 and 90 days from the start date.
