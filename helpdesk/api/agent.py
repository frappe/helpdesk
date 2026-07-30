import frappe

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def sent_invites(emails: list[str], send_welcome_mail_to_user: bool = True):
    for email in emails:
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.get_doc(
                {"doctype": "User", "email": email, "first_name": email.split("@")[0]}
            ).insert()

            if send_welcome_mail_to_user:
                user.send_welcome_mail_to_user()

        frappe.get_doc(
            {
                "doctype": "HD Agent",
                "ID": email,
                "user": user.name,
                "agent_name": user.full_name,
                "user_image": user.user_image,
            }
        ).insert()
    return
