# Helpdesk

## Language

### Tickets

**Source**:
The channel a ticket came in through: Email, Portal or WhatsApp. A ticket an agent raises from the desk counts as Portal.
_Avoid_: channel, via portal

### WhatsApp

**WhatsApp Ticket**:
A ticket whose **Source** is WhatsApp. Its conversation with the customer happens over WhatsApp, and it has no email thread.
_Avoid_: WhatsApp chat, conversation

**Business Number**:
One of the site's WhatsApp numbers, each a WA Account in the whatsapp app. A WhatsApp Ticket belongs to the Business Number it came in on and always replies from it.
_Avoid_: WhatsApp account, line

**Active WhatsApp Ticket**:
The one WhatsApp Ticket of a contact on a **Business Number** that is not Closed. A contact has at most one per Business Number; every inbound message from that contact to that number lands on it.
_Avoid_: open ticket (Resolved tickets are still active)

**Reopen**:
An inbound message on a Paused or Resolved WhatsApp Ticket moves it back to the reopen status, same as an email reply.

**Closed-Ticket Prompt**:
The reply sent when a contact whose last WhatsApp Ticket is Closed messages again, asking whether to raise a new ticket.

**WhatsApp Sender**:
The Contact a WhatsApp number belongs to, matched on mobile or phone. An unknown number becomes a new Contact named after its WhatsApp profile, with no customer or portal user until an agent links one.

**Held Message**:
An inbound message sent after a **Closed-Ticket Prompt** and before the contact answers it. It belongs to no ticket; choosing "Create new ticket" moves every Held Message onto the new ticket, and the first one becomes its subject and description.

**Reply Window**:
The 24 hours after the contact's last message, when an agent may send any message. Once it closes, only an approved template can be sent, and the agent is told so before typing.

## Relationships

- A **Contact** has many **WhatsApp Tickets** over time but at most one **Active WhatsApp Ticket** per **Business Number**
- Only a Closed ticket triggers the **Closed-Ticket Prompt**; a Paused or Resolved one is **Reopened**
- Only the contact starts a **WhatsApp Ticket**, by messaging in; agents never open one
- Email tickets never count as a contact's **Active WhatsApp Ticket**; the two channels stay separate
- A contact gets one **Closed-Ticket Prompt** until they answer it; "No, thanks" leaves the **Held Messages** unlinked
- A contact with a portal login sees their **WhatsApp Tickets** on the portal read-only; they reply only on WhatsApp
- A message for a merged **WhatsApp Ticket** goes to the ticket it was merged into
- A **WhatsApp Ticket** merges only into another WhatsApp Ticket on the same **Business Number**, and is never split

## Flagged ambiguities

- "One contact, one ticket" meant one *active* ticket, not one ticket forever.
