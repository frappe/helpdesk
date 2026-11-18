---
name: helpdesk-implementation
description: Set up Frappe Helpdesk for a business and see it through to daily use. Ask how support works today, agree a setup plan in their words, set up the support inbox, agents, assignment, teams, ticket types, an SLA, saved replies, customers, the knowledge base and the portal, then check every step on the site's data. Use when someone wants to set up, implement or start using Helpdesk, asks what to do next in their Helpdesk setup, or asks whether their team is really using it, when the site runs the Helpdesk app.
---

# Setting up Frappe Helpdesk

This skill takes a business from a fresh Helpdesk site to a team that answers every customer issue in it. It does not repeat how to work tickets, SLAs or saved replies: read the `frappe-helpdesk` skill that ships with Helpdesk (`skills/frappe-helpdesk/`, in the site's assistant `helpdesk/frappe-helpdesk`), and its `reference/setup.md`, before you write. That skill shows frappectl commands. Use its doctypes, methods and traps; the calls are the same from any client.

Every step here is a document read or write, or a whitelisted method, so it works the same from the site's assistant, MCP or frappectl. You act as the connected user. Setting up needs the Agent Manager role. An Agent can manage teams and saved replies, but not settings, SLAs or other agents.

The work has four parts, in this order: **agree the plan**, **set up**, **start using**, **check**. Setting up is your job. Using is theirs: their agents answer the tickets, and you check that they did.

## Before you start

1. Call `helpdesk.api.auth.get_user`. Without `is_manager`, stop and say who can do the setup.
2. Look for a plan. List `Note` with `{"title": ["like", "Helpdesk setup plan%"]}`. If one exists, read it and go to "Check where it stands". Do not start a second plan.
3. Read what is already there: `HD Settings`, `HD Agent` (`user`, `is_active`), `HD Team`, `HD Ticket Type`, `HD Ticket Priority`, `HD Ticket Status`, `HD Service Level Agreement`, `Assignment Rule` with `{"document_type": "HD Ticket"}`, `Email Account`, and the count of `HD Ticket`. A site with real tickets is not a fresh site: a change to a status, priority or SLA then changes how live tickets are timed.

## 1. Agree the plan

Ask the questions in `reference/interview.md`. Ask one or two at a time. When the person gives you call notes, take every answer you can from them and ask only for what is missing.

Start with the fit question. When what they lose track of is prospects or orders, not customer issues, say so: Helpdesk will not fix that, and CRM or ERPNext should come first.

Then build the plan from `reference/steps.md`. Every step there says when it applies. Keep the steps that apply, drop the rest, and for each one write:

- the title in their words: "Emails to support@ become tickets", not "Configure Email Account"
- one line on why, tied to what they said
- who does it: you, them, or their team
- what "done" means on the site's data, from the step's **Done when**

Ask what "Helpdesk is working" looks like for them in a month, and turn the answer into a check you can run on their data, such as "every customer email is a ticket with an agent within an hour". If you cannot check it from data, rewrite it with them until you can. This is their live condition.

What they ask for that this skill does not set up goes in the plan under "Asked for, not in this setup", in their words. See "Scope".

**Stop here.** Post the plan, end your turn and wait for their reply. Agree it with them, not with yourself. On a yes, save it as a Note (`reference/plan.md`) so the next session starts where this one ended.

## 2. Set up, one step at a time

Work the setup steps of the plan in order. For each one:

1. Read the records the step touches.
2. Show the change list: for each record, the doctype, the name, each field with its old and new value. Write "new" for a record you will create.
3. Wait for a yes. Ask even when the chat approves writes on its own: the person must see each change to their helpdesk before it is made.
4. Write, ten records or fewer at a time.
5. Run the step's **Done when** check. Say whether it passed, and what the data showed.
6. On a pass, mark the step done in the plan (show that edit too), and name the next step.

Warn before a change that is hard to undo. These are listed in "One-way doors".

To bring in their customers and contacts: under about 50 rows, create them in batches of ten after one test row. Above that, prepare the file with them and have them import it with Data Import. Then check the counts against their file.

## 3. Start using

From here the steps belong to their agents: the first real ticket answered, the first one resolved, a saved reply used. **Never reply to, comment on, resolve or create their tickets for them**, and never write their help articles' final text without their words. A reply you send goes to a real customer, and a ticket you closed proves nothing about whether they use Helpdesk. Explain how to do it in the app, then check that it happened.

A record counts for a use step when it was made after setup by someone who is not a setup user. The plan lists the setup users: an implementer or partner who set up the site for them. When the business set itself up, the list is empty and every record after setup counts.

## 4. Check where it stands

When they ask "where are we", "what's next" or "is it working", run the **Done when** check of every step in the plan. Reads only. For response times and SLA numbers, use the report methods in `frappe-helpdesk`'s `reference/reports.md`: they count working hours the way the SLA does. Then answer in three lines: what is done, what is next, the one thing to do now. Under that, a short table: step, done or not, what the data shows.

They are **live** when their live condition holds and their own agents worked tickets in the last 7 days. Check it again 30 and 90 days after the plan's start date. Live at day 90 is the goal; setup is not.

Offer, at the end of every session, to add three lines to the plan's log: what was done, what failed, what is next.

## Scope

This skill sets up standard Helpdesk: the support inbox, agents and roles, assignment rules, teams, ticket types, priorities and statuses, one SLA with its holiday list, saved replies, customers and contacts, knowledge base articles, the customer portal, feedback, branding.

It does not set up custom fields, field dependencies, ticket templates beyond the default, form scripts, telephony, WhatsApp, Slack or other channels, the ERPNext link, or automations beyond assignment rules and saved reply actions. Note each ask in the plan and say it is not part of this setup.

## One-way doors

Ask before each of these, and say what will happen:

1. **Anything that emails a customer.** A reply, a portal invite, a merge and a feedback request all send email. During setup, send none to a real customer. Test with an address the person owns.
2. **Changing an SLA, a priority or a status while tickets are open.** Every ticket save picks its SLA again and works out its dates again. Say how many open tickets it touches.
3. **Removing a status, priority, type or team that tickets use.** Disable it (`disabled` 1, or `enabled` 0 on a status) instead.
4. **Inviting people.** Each invite sends an email. Show the list first.
5. **Imports.** Test with one row first.
6. **Deleting the last assignment rule on tickets.** Helpdesk refuses it; disable a rule instead.

Everything else can be changed back, so do it after the change list and a yes.

## When a call fails

An error that names its cause has a fix in the traps below or in `frappe-helpdesk`. For an error with no cause:

1. Run the call once more. Change only what could matter.
2. Make it smaller until you find the smallest call that still fails.
3. Stop and give the person the exact call and the exact error.

Never work around a permission error. Say which role the step needs.

## Traps

- **A new site is not empty.** Install creates statuses Open, Replied (a Paused one), Resolved and Closed; priorities Urgent, High, Medium and Low; ticket types Unspecified, Question, Bug and Incident; teams Billing and Product Experts; a default SLA "Standard" on a holiday list "Default" with no holidays in it; a "General" knowledge base category with an "Introduction" article; and a welcome ticket. Rename, disable or keep each one with the person. Do not stack theirs beside them.
- **Nobody is assigned until a rule says so.** The base `Assignment Rule` "Support Rotation" (`HD Settings` `base_support_rotation`) is disabled at install. A team's own rule, "<team> - Support Rotation", assigns only tickets whose `agent_group` is that team.
- **An agent exists only after they accept.** Inviting with the Agent role makes the `HD Agent` when the person accepts. A pending invite is not an agent.
- **Team members are replaced whole.** Read the team, then send its full `users` list with the change. A team with no members has its rule disabled.
- **An SLA needs a holiday list, and a row for each priority it covers.** A ticket whose priority has no row gets no SLA. Times are seconds of working time.
- **Set both forms of a condition.** On an SLA or an assignment rule, set the Python `condition` (or `assign_condition`) and the `*_json` form, so the app can show and edit it.
- **Never take a password in chat.** The person connects the support mailbox in Helpdesk, under Settings, Email Accounts. You check the result.
- **Read in pages.** Ask for 100 rows or fewer at a time. For counts, count; do not list.

## Reference

- `reference/interview.md`: the questions, in order, and what each answer decides.
- `reference/steps.md`: every step, when it applies, what you do, what they do, and its Done when check.
- `reference/plan.md`: how to write the plan as a Note on the site.
