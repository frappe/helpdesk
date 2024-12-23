import frappe
from frappe import _

from helpdesk.utils import is_agent


@frappe.whitelist()
def get_users():
    if not is_agent():
        frappe.throw(_("Access denied"), exc=frappe.PermissionError)

    if frappe.session.user == "Guest":
        frappe.throw(frappe._("Authentication failed"), exc=frappe.AuthenticationError)

    users = frappe.qb.get_query(
        "User",
        fields=["name", "email", "enabled", "user_image", "full_name", "user_type"],
        order_by="full_name asc",
        distinct=True,
    ).run(as_dict=1)

    for user in users:
        if frappe.session.user == user.name:
            user.session_user = True

    return users
