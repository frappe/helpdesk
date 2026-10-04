import frappe

MANAGER_ROLES = ("HD Customer", "HD Customer Manager")


def execute():
    """Give customer managers both customer roles; invites accepted earlier could miss one."""
    for user in get_customer_manager_users():
        if missing := set(MANAGER_ROLES) - set(frappe.get_roles(user)):
            frappe.get_doc("User", user).add_roles(*missing)


def get_customer_manager_users() -> list[str]:
    """Existing users whose contact is a manager on some customer."""
    member = frappe.qb.DocType("HD Customer Member")
    contact = frappe.qb.DocType("Contact")
    user = frappe.qb.DocType("User")
    return (
        frappe.qb.from_(member)
        .join(contact)
        .on(contact.name == member.contact_name)
        .join(user)
        .on(user.name == contact.user)
        .select(user.name)
        .distinct()
        .where(member.is_manager == 1)
        .run(pluck=True)
    )
