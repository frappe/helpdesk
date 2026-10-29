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

**Pinned article**:
A Published Article listed under the Featured tab on the knowledge base home, in a chosen order. While any are pinned, Featured replaces the Latest tab. Unpublishing or archiving it unpins it.
_Avoid_: Promoted article, featured article (that is only the portal's tab)

**Article weight**:
A whole number on an Article. Inside its Category, a heavier Article lists first; equal weights keep the usual order (newest, or most viewed). Pinning sets it from the pin order: the first of N Pinned articles weighs N, the last 1, and unpinning resets it to 0. It has no effect on search or the home page's Popular and Latest lists.
_Avoid_: Priority, rank, position

**General**:
The reserved Category that receives the Articles of a deleted Category. It cannot be renamed or deleted, but it can hold Subcategories like any Category.

**Archived article**:
An Article taken out of the knowledge base but kept because a ticket cites it. It belongs to no Category.

**Access**:
Who can read an Article: Public (anyone), Customers (signed-in customers), or Private (agents only).
_Avoid_: Visibility, audience

**Category access**:
The Access shared by every Article in a Category and its Subcategories; Mixed when they differ. It is derived from the Articles, never stored. A reader sees a Category when they can read any Article in it or its Subcategories.
