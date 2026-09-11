"""Clear the backlog of assignment notifications the upgrade surfaced.

Rule-driven assignments notified nobody before core ``assign_to`` took over,
so every ticket one had ever routed turns up unread. Later ones still arrive
unread.
"""

import frappe


def execute():
    frappe.db.set_value(
        "Notification Log",
        {"app": "helpdesk", "type": "Assignment", "read": 0},
        "read",
        1,
        update_modified=False,
    )
