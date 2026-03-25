import frappe
from frappe.model.naming import _generate_random_string


def execute():
    # This patch does two things:
    # 1. For all users that dont have a role of HD Agent & HD Agent Manager, and have raised a ticket, assign them the role of HD Customer
    # 2. Find all contacts that are linked to a customer via dynamic link, group them by customer and add them to HD Customer doctype's contacts child table

    # First part: Assigning HD Customer role to users who have raised a ticket but dont have HD Agent or HD Agent Manager role
    HDTicket = frappe.qb.DocType("HD Ticket")
    User = frappe.qb.DocType("User")
    HasRole = frappe.qb.DocType("Has Role")

    agent_users = (
        frappe.qb.from_(HasRole)
        .select(HasRole.parent)
        .where(HasRole.role.isin(["HD Agent", "HD Agent Manager"]))
    )

    customer_users = (
        frappe.qb.from_(HDTicket)
        .join(User)
        .on(HDTicket.raised_by == User.name)
        .select(User.name)
        .where(
            (HDTicket.raised_by != "Guest")
            & (User.name.notin(agent_users))
            & (User.name != "Administrator")
        )
        .distinct()
    ).run(as_dict=True)

    customer_users = [user.name for user in customer_users]

    values = [
        (_generate_random_string(), user, "HD Customer", "roles", "User")
        for user in customer_users
    ]

    frappe.db.bulk_insert(
        "Has Role", ["name", "parent", "role", "parentfield", "parenttype"], values
    )

    # Second part: Moving dynamic link of contact to HD Customer doctype
    Contact = frappe.qb.DocType("Contact")
    DynamicLink = frappe.qb.DocType("Dynamic Link")

    contacts_with_customer = (
        frappe.qb.from_(Contact)
        .join(DynamicLink)
        .on(Contact.name == DynamicLink.parent)
        .select(
            Contact.name.as_("contact_name"),
            DynamicLink.link_name.as_("customer_name"),
        )
        .where(
            (DynamicLink.link_doctype == "HD Customer")
            & (DynamicLink.parenttype == "Contact")
        )
    ).run(as_dict=True, debug=True)

    # group by customer_name:
    contacts_by_customer: dict[str, list[str]] = {}
    for row in contacts_with_customer:
        contacts_by_customer.setdefault(row.customer_name, []).append(
            {"contact_name": row.contact_name}
        )

    for customer_name, contacts in contacts_by_customer.items():
        try:
            customer_doc = frappe.get_doc("HD Customer", customer_name)
            for contact in contacts:
                if contact["contact_name"] not in [
                    d.contact_name for d in customer_doc.contacts
                ]:
                    customer_doc.append(
                        "contacts", {"contact_name": contact["contact_name"]}
                    )

            customer_doc.save()
        except Exception as e:
            print(f"Error processing customer {customer_name}: {e}")
            frappe.log_error(
                f"Error processing customer {customer_name}: {e}",
                "move_contact_dynamic_link_to_hd_customer",
            )
