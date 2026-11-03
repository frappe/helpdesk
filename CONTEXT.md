# Helpdesk

Agents answer customer tickets and publish a knowledge base that customers and guests read on the portal.

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

**General**:
The reserved Category that receives the Articles of a deleted Category. It cannot be renamed or deleted, but it can hold Subcategories like any Category.

**Archived article**:
An Article taken out of the knowledge base but kept because a ticket cites it. It belongs to no Category.

**Access**:
Who can read an Article: Public (anyone), Customers (signed-in customers), or Private (agents only).
_Avoid_: Visibility, audience

**Category access**:
The Access shared by every Article in a Category and its Subcategories; Mixed when they differ. It is derived from the Articles, never stored. A reader sees a Category when they can read any Article in it or its Subcategories.

## SLA

**Working hours**: the hours of a workday, set per weekday on an SLA policy (HD Service Day: start and end time). Only working hours count towards an SLA: due dates (response by, resolution by), elapsed times (first response, resolution, hold, failed by), ticket analytics and the outside-hours banner all skip holidays, non-workdays and the time outside these hours.

**Break**: an optional pause inside a workday, such as lunch, set as a break start and end on that workday's row. A row has at most one break, which must sit strictly inside its working hours. The break is not working time: the SLA clock stops for it everywhere working hours apply, and a ticket raised during it is raised outside working hours. Open tickets pick up a new or changed break the next time they are updated.
