# Helpdesk

Agents answer customer tickets and publish a knowledge base that customers and guests read on the portal.

## Tickets

**Source**:
The channel a ticket came in through: Email, Portal or WhatsApp. A ticket an agent raises from the desk counts as Portal.
_Avoid_: channel, via portal

## Knowledge base

**Article**:
A published help page. It belongs to at most one Category or Subcategory and carries its own Access.

**Category**:
A top-level group of Articles, shown on the knowledge base home. It can also hold Subcategories.
_Avoid_: Folder, section, group

**Subcategory**:
A Category nested one level under another Category, used to split a large Category into themes. It holds Articles, never further Subcategories. Its Articles return to the parent Category when it is deleted.
_Avoid_: Child category, sub-section, nested category

**Pinned category**:
A top-level Category featured on the knowledge base home in a chosen order. Subcategories cannot be pinned.

**Pinned article**:
A Published Article listed under the Featured tab on the knowledge base home, in a chosen order. While any are pinned, Featured replaces the Latest tab. Unpublishing or archiving it unpins it.
_Avoid_: Promoted article, featured article (that is only the portal's tab)

**Article weight**:
A whole number on an Article. Inside its Category, a heavier Article lists first; equal weights keep the usual order (newest, or most viewed). Pinning never changes it. It has no effect on search or the home page's Popular and Latest lists.
_Avoid_: Priority, rank, position

**General**:
The reserved Category that receives the Articles of a deleted Category. It cannot be renamed or deleted, but it can hold Subcategories like any Category.

**Archived article**:
An Article taken out of the knowledge base without deleting it, so the tickets that cite it keep their link. It belongs to no Category, and readers never see it. Restoring it puts it back in a Category as a draft.

**Access**:
Who can read an Article: Public (anyone), Customers (signed-in customers), or Private (agents only).
_Avoid_: Visibility, audience

**Category access**:
The Access shared by every Article in a Category and its Subcategories; Mixed when they differ. It is derived from the Articles, never stored. A reader sees a Category when they can read any Article in it or its Subcategories.

## SLA

**Working hours**: the hours of a workday, set per weekday on an SLA policy (HD Service Day: start and end time). Only working hours count towards an SLA: due dates (response by, resolution by), elapsed times (first response, resolution, hold, failed by), ticket analytics and the outside-hours banner all skip holidays, non-workdays and the time outside these hours.

**Break**: an optional pause inside a workday, such as lunch, set as a break start and end on that workday's row. A row has at most one break, which must sit strictly inside its working hours. The break is not working time: the SLA clock stops for it everywhere working hours apply, and a ticket raised during it is raised outside working hours. Open tickets pick up a new or changed break the next time they are updated.

## WhatsApp

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
