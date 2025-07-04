import frappe
from frappe.utils import split_emails, validate_email_address


@frappe.whitelist(allow_guest=True)
def accept_invitation(key: str | None = None):
    if not key:
        frappe.throw("Invalid or expired key")
    result = frappe.db.get_all("HD Invitation", filters={"key": key}, pluck="name")
    if not result:
        frappe.throw("Invalid or expired key")
    invitation = frappe.get_doc("HD Invitation", result[0])
    invitation.accept()
    invitation.reload()
    user = frappe.get_doc("User", invitation.email)
    needs_password_setup = user and not user.last_password_reset_date
    if invitation.status == "Accepted":
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = (
            "/helpdesk"
            if not needs_password_setup
            else f"{invitation.get_update_password_url()}"
        )


@frappe.whitelist()
def invite_by_email(emails: str, role: str):
    frappe.only_for(["System Manager", "Agent Manager"])
    valid_roles = ["System Manager", "Agent Manager", "Agent"]
    if role not in valid_roles:
        frappe.throw("Cannot invite for this role")
    if not emails:
        return
    email_string = validate_email_address(emails, throw=False)
    email_list = split_emails(email_string)
    if not email_list:
        return
    existing_members = frappe.db.get_all(
        "User", filters={"email": ["in", email_list]}, pluck="email"
    )
    existing_invites = frappe.db.get_all(
        "HD Invitation",
        filters={
            "email": ["in", email_list],
            "role": ["in", valid_roles],
        },
        pluck="email",
    )
    to_invite = list(set(email_list) - set(existing_members) - set(existing_invites))
    for email in to_invite:
        frappe.get_doc(doctype="HD Invitation", email=email, role=role).insert(
            ignore_permissions=True
        )
    return {
        "existing_members": existing_members,
        "existing_invites": existing_invites,
        "to_invite": to_invite,
    }
