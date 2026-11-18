# Use case specifications

Six use cases across the two workflows (two per member, three members). Each flow is automated in `usecases/` under the same
ID, and each test asserts the result shown on screen and then the
postconditions in the stored ticket.

Sources: the Helpdesk documentation describes the customer portal and the
agent desk in general terms; the step-level behaviour below was written by the
team from the baseline (16.1.0) and confirmed on the running system.

## Requirements the use cases are derived from

| ID | Workflow | Requirement |
|---|---|---|
| FR-A1 | A | A signed-in customer can raise a ticket with a subject and a description. |
| FR-A2 | A | A new ticket starts as Open, priority Medium, raised by the signed-in customer. |
| FR-A3 | A | The subject is mandatory and at most 140 characters. |
| FR-A4 | A | A ticket is visible to the customer who raised it and to agents only. |
| FR-B1 | B | An agent can assign a ticket to an agent. |
| FR-B2 | B | An agent can set the priority and the ticket type. |
| FR-B3 | B | An agent can move a ticket between Open, Replied, Resolved and Closed; the resolution date follows BR3. |
| FR-B4 | B | A customer can close their own ticket; a resolved ticket that an agent answered needs a rating first (BR2). |
| FR-B5 | B | A closed or rated ticket cannot be changed by the customer (BR4). |
| FR-B6 | B | A ticket waiting on the customer is closed automatically after N days without a message (BR1; tested at API level). |

---

## UC-01 Raise a ticket

| | |
|---|---|
| Actor | Customer |
| Requirements | FR-A1, FR-A2, FR-A3 |
| Preconditions | The customer is signed in. |
| Postconditions (success) | One new ticket exists with the entered subject, status Open, raised by the customer, no resolution date. |
| Postconditions (failure) | No ticket is created. |

**Main flow (MF)**
1. The customer opens the ticket list and chooses Create.
2. The system shows the New Ticket form with a Subject field.
3. The customer enters a subject; the system shows the description editor.
4. The customer enters a description and chooses Submit.
5. The system creates the ticket and shows its page: subject, Status Open, Priority Medium, and a Close button.

**Alternative flows**
- **AF1** (step 1): the customer opens the form directly by its address and enters a subject of exactly 140 characters. The ticket is created with the full subject.
- **AF2** (step 4): the customer chooses Discard. The system clears the description and disables Submit. The customer writes a new description and submits; the ticket holds only the second text.

**Exception flows**
- **EF1** (step 3): the subject is empty. The system shows "Please enter a subject to continue" and offers no Submit button.
- **EF2** (step 4): a subject but no description. Submit stays disabled.
- **EF3** (step 3): the customer types more than 140 characters. The field keeps the first 140.

## UC-02 Close and rate a ticket

| | |
|---|---|
| Actor | Customer |
| Requirements | FR-B4, FR-B5 |
| Preconditions | The customer is signed in and owns a ticket that is not closed. For MF, AF2, EF1, EF2 the ticket is Resolved and an agent has replied. |
| Postconditions (success) | The ticket is Closed; the rating is stored where one was given; the resolution date set when it was resolved is unchanged. |
| Postconditions (failure) | The ticket keeps its status and has no rating. |

**Main flow (MF)**
1. The customer opens the resolved ticket and chooses Close.
2. The system shows "Rate this ticket".
3. The customer selects 4 of 5; the system lists the reasons for that rating.
4. The customer picks a reason and chooses Submit.
5. The system closes the ticket and shows Status Closed and the chosen feedback; the Close button is gone.

**Alternative flows**
- **AF1** (step 1): the ticket is Open and no agent has replied. The system asks "Close Ticket"; the customer confirms; the system shows "Ticket closed successfully." No rating is required.
- **AF2** (step 4): the customer also writes a comment in "Tell us more". The comment is stored with the rating.

**Exception flows**
- **EF1** (step 3-4): no rating, or a rating without a reason. Submit stays disabled and the dialog shows what is still required ("Select a rating", "Pick an option").
- **EF2** (step 4): the customer dismisses the dialog. The ticket stays Resolved and unrated.
- **EF3** (step 1): the ticket is already Closed. The page offers no Close button and the ticket is unchanged.

## UC-03 Triage and assign a ticket

| | |
|---|---|
| Actor | Agent |
| Requirements | FR-B1, FR-B2, FR-A4 |
| Preconditions | The agent is signed in; an open, unassigned ticket exists. |
| Postconditions (success) | The ticket is assigned to the agent (MF), or holds the new priority (AF1) or type (AF2). |
| Postconditions (failure) | The ticket is unchanged and unassigned. |

**Main flow (MF)**
1. The agent opens the ticket list and selects the ticket.
2. The system shows the ticket with Assignee "Set Assignee...".
3. The agent opens the assignee picker and selects themself.
4. The system shows "Assignees updated successfully." and the agent as assignee.

**Alternative flows**
- **AF1** (step 3): the agent sets Priority to High. The system shows "Ticket updated successfully."
- **AF2** (step 3): the agent sets Ticket Type to Bug. The system shows "Ticket updated successfully."

**Exception flows**
- **EF1** (step 1): a different customer opens the ticket's address. The system shows "Not allowed via controller permission check" and returns them to their own list.
- **EF2** (step 1): a customer opens the agent's ticket screen. The system does not show it and offers no assignee or priority controls.

## UC-04 Resolve and reopen a ticket

| | |
|---|---|
| Actor | Agent |
| Requirements | FR-B3, FR-A4 |
| Preconditions | The agent is signed in; a ticket exists (Open for MF and AF1, Resolved for AF2). |
| Postconditions (success) | The ticket has the new status; a resolution date exists exactly when the status is in the Resolved category. |
| Postconditions (failure) | No ticket is created or changed. |

**Main flow (MF)**
1. The agent opens the ticket and opens the status menu.
2. The agent selects Resolved.
3. The system shows "Ticket updated successfully.", the status Resolved, and the activity "changed Status Open → Resolved".
4. The customer, opening the same ticket, sees Status Resolved.

**Alternative flows**
- **AF1** (step 2): the agent selects Replied. The ticket waits on the customer and has no resolution date.
- **AF2** (step 2): the ticket is Resolved and the agent selects Open. The resolution date is cleared.

**Exception flows**
- **EF1** (step 1): the ticket number does not exist. The system shows "HD Ticket 999999 not found".
- **EF2** (step 1): the visitor is not signed in. The system shows the Sign In page.

## UC-05 Reply to a ticket

| | |
|---|---|
| Actor | Customer |
| Requirements | FR-B3, FR-B5 |
| Preconditions | The customer is signed in and owns a ticket that is not closed. |
| Postconditions (success) | The conversation has one more message; the ticket is Open; a resolution date, if there was one, is cleared. |
| Postconditions (failure) | No message is added and the ticket keeps its status. |

**Main flow (MF)**
1. The customer opens a ticket whose status is shown as "Awaiting Response" (the agent set it to Replied).
2. The customer opens the message box and types a message; the system enables Send.
3. The customer chooses Send.
4. The system adds the message, closes the editor and shows Status Open.

**Alternative flows**
- **AF1** (step 1): the ticket is already Open. The message is added and the ticket stays Open.
- **AF2** (step 1): the ticket is Resolved. The message reopens it: Status Open and the resolution date is cleared (BR3).

**Exception flows**
- **EF1** (step 2): the message is empty. Send stays disabled.
- **EF2** (step 1): the ticket is Closed. The page offers no message box (BR4).

## UC-06 Find a ticket in my list

| | |
|---|---|
| Actor | Customer |
| Requirements | FR-A4, FR-B3 |
| Preconditions | The customer is signed in and has raised at least two tickets. |
| Postconditions | Tickets are unchanged: finding a ticket does not modify it. |

**Main flow (MF)**
1. The customer opens the ticket list.
2. The customer types a subject in the Subject filter.
3. The system lists only the matching ticket, with its status.
4. The customer selects it; the system shows the ticket page.

**Alternative flows**
- **AF1** (step 2): the customer types the ticket number in the ID filter. Only that ticket is listed.
- **AF2** (step 2): an agent has resolved the ticket. The list opens with a "Status is Open" filter that hides it, so the customer chooses "Clear all Filter" and then filters by number; the ticket is listed as Resolved.

**Exception flows**
- **EF1** (step 3): nothing matches. The system shows "No tickets found for the applied filters."
- **EF2** (step 2): the number belongs to another customer's ticket. Nothing is listed (FR-A4).

---

## Flow-to-test map

| Use case | Flows | Test file |
|---|---|---|
| UC-01 | MF, AF1, AF2, EF1, EF2, EF3 | `usecases/uc01_raise_ticket.spec.mjs` |
| UC-02 | MF, AF1, AF2, EF1, EF2, EF3 | `usecases/uc02_close_and_rate.spec.mjs` |
| UC-03 | MF, AF1, AF2, EF1, EF2 | `usecases/uc03_triage_and_assign.spec.mjs` |
| UC-04 | MF, AF1, AF2, EF1, EF2 | `usecases/uc04_resolve_and_reopen.spec.mjs` |
| UC-05 | MF, AF1, AF2, EF1, EF2 | `usecases/uc05_reply_to_ticket.spec.mjs` |
| UC-06 | MF, AF1, AF2, EF1, EF2 | `usecases/uc06_find_ticket.spec.mjs` |

32 flows, 32 automated tests.

## Observations made while automating (not yet triaged)

- Typing a subject on the New Ticket form raises an "Internal Server Error"
  toast: the article-suggestion call (`helpdesk.api.article.search`) returns
  500 on this site, which has no RediSearch module. Ticket creation still works.
- The description is mandatory in the form but optional through the API.
- Opening a ticket that does not exist shows the same "not found" message
  several times at once.
- The customer's ticket list opens with a "Status is Open" filter, so resolved
  and closed tickets are hidden until the filter is cleared. A customer looking
  for a ticket an agent has just resolved will not see it at first.
- The list remembers each user's filters between visits. Pressing Refresh
  right after typing a new filter restored the previously saved one in one
  observed run; this was not isolated further.
- A customer sees the status "Replied" as "Awaiting Response".
