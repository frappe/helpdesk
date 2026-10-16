import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property

HELPDESK_NOTIFICATION_TYPES = ["Reaction", "Ticket Reopened"]

# depends_on keeps the fields out of non-helpdesk Comment forms in Desk;
# the SPA reads them via API, which is unaffected
COMMENT_CUSTOM_FIELDS = {
    "Comment": [
        {
            "fieldname": "is_pinned",
            "label": "Is Pinned",
            "fieldtype": "Check",
            "insert_after": "content",
            "depends_on": 'eval:doc.reference_doctype === "HD Ticket"',
        },
        {
            "fieldname": "reactions",
            "label": "Reactions",
            "fieldtype": "Table",
            "options": "HD Comment Reaction",
            "insert_after": "is_pinned",
            "depends_on": 'eval:doc.reference_doctype === "HD Ticket"',
        },
    ],
}


def setup_comments_and_notifications():
    """Schema for core Comment / Notification Log adoption.

    Idempotent; runs on install and via patch on existing sites.
    """
    create_custom_fields(COMMENT_CUSTOM_FIELDS)
    add_notification_types()
    add_comment_permissions()


def add_notification_types():
    for type_name in HELPDESK_NOTIFICATION_TYPES:
        if frappe.db.exists("Notification Type", type_name):
            continue
        frappe.get_doc(
            {"doctype": "Notification Type", "type_name": type_name, "enabled": 1}
        ).insert(ignore_permissions=True)


def add_comment_permissions():
    """Agents get full CRUD on Comment; customers get none.

    Internal notes must never be readable by portal customers, so no
    customer-facing role is ever added here.
    """
    for role in ["Agent", "Agent Manager"]:
        if not frappe.db.exists("Role", role):
            continue
        add_permission("Comment", role, 0)
        for ptype in ["create", "write", "delete"]:
            update_permission_property("Comment", role, 0, ptype, 1)
