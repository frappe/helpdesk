import frappe


@frappe.whitelist()
def clear(ticket: str | int = None, comment: str = None):
    """
    Mark notifications as read. No arguments will clear all notifications for `user`.

    :param ticket: Ticket to clear notifications for
    :param comment: Comment to clear notifications for
    """
    filters = {"user_to": frappe.session.user, "read": False}
    if ticket:
        filters["reference_ticket"] = ticket
    if comment:
        filters["reference_comment"] = comment
    for notification in frappe.get_all(
        "HD Notification", filters=filters, pluck="name"
    ):
        frappe.db.set_value("HD Notification", notification, "read", 1)


def notify_assignment_from_todo(doc, event=None):
    if doc.reference_type != "HD Ticket" or not doc.reference_name:
        return
    if not doc.allocated_to:
        return
    assigned_by = doc.assigned_by or frappe.session.user
    if assigned_by == doc.allocated_to:
        return

    # Check if a similar unread notification already exists to prevent duplicates
    # This can happen if multiple ToDo records are created for the same assignment
    # Using get_all with pluck and limit=1 is optimized for existence checks
    existing_notification = frappe.get_all(
        "HD Notification",
        filters={
            "user_from": assigned_by,
            "user_to": doc.allocated_to,
            "reference_ticket": doc.reference_name,
            "notification_type": "Assignment",
            "read": 0,  # Only check unread notifications
        },
        limit=1,
        pluck="name",
    )
    
    if existing_notification:
        return

    frappe.get_doc(
        frappe._dict(
            doctype="HD Notification",
            user_from=assigned_by,
            user_to=doc.allocated_to,
            reference_ticket=doc.reference_name,
            notification_type="Assignment",
        )
    ).insert(ignore_permissions=True)
