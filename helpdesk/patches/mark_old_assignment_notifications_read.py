"""Clear the one-time backlog of unread assignment notifications.

Helpdesk used to notify only when an agent assigned a ticket by hand.
Assignments made by an Assignment Rule notified nobody. Core ``assign_to``
now owns assignments and notifies on every one, so the first load after the
upgrade shows an unread row for every ticket the rule had ever routed.

Those are history, not news. This marks them read once. Assignments made
after the patch runs still arrive unread.
"""

import frappe


def execute():
    # One statement: the filter is narrow and Notification Log is not a table
    # anyone accumulates millions of rows in.
    frappe.db.set_value(
        "Notification Log",
        {"app": "helpdesk", "type": "Assignment", "read": 0},
        "read",
        1,
        update_modified=False,
    )
