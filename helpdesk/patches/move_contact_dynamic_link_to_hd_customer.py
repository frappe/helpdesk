import frappe
from frappe import _


def execute():
    """Migrate the old Contact→HD Customer model to the new child-table model.

    1. Grant the new ``HD Customer`` role to every non-agent who has raised a
       ticket (they used to get portal access implicitly).
    2. Move every Contact→HD Customer dynamic link into the customer's
       ``contacts`` child table.
    """
    grant_customer_role_to_ticket_raisers()
    migrate_contact_links_to_members()


def grant_customer_role_to_ticket_raisers() -> None:
    HasRole = frappe.qb.DocType("Has Role")
    ticket_raisers = get_ticket_raisers_without_role(HasRole)
    if not ticket_raisers:
        return

    values = [
        (frappe.generate_hash(length=10), user, "HD Customer", "roles", "User")
        for user in ticket_raisers
    ]
    frappe.db.bulk_insert(
        "Has Role", ["name", "parent", "role", "parentfield", "parenttype"], values
    )


def get_ticket_raisers_without_role(HasRole) -> list[str]:
    """Ticket raisers who are neither agents nor already an HD Customer."""
    HDTicket = frappe.qb.DocType("HD Ticket")
    User = frappe.qb.DocType("User")

    excluded_users = (
        frappe.qb.from_(HasRole)
        .select(HasRole.parent)
        .where(HasRole.role.isin(["Agent", "Agent Manager", "HD Customer"]))
    )

    return (
        frappe.qb.from_(HDTicket)
        .join(User)
        .on(HDTicket.raised_by == User.name)
        .select(User.name)
        .where(
            (HDTicket.raised_by != "Guest")
            & (User.name.notin(excluded_users))
            & (User.name != "Administrator")
        )
        .distinct()
        .run(pluck=True)
    )


def migrate_contact_links_to_members() -> None:
    contacts_by_customer = get_linked_contacts_by_customer()

    failures: list[str] = []
    for customer_name, contact_names in contacts_by_customer.items():
        try:
            add_members(customer_name, contact_names)
        except Exception:
            failures.append(customer_name)
            frappe.log_error(
                title="move_contact_dynamic_link_to_hd_customer",
                message=f"Failed to migrate contacts for customer {customer_name}",
            )

    if failures:
        frappe.throw(
            _(
                "Could not migrate contacts for {0} customer(s): {1}. "
                "Fix the underlying data and re-run the patch."
            ).format(len(failures), ", ".join(failures))
        )


def get_linked_contacts_by_customer() -> dict[str, list[str]]:
    Contact = frappe.qb.DocType("Contact")
    DynamicLink = frappe.qb.DocType("Dynamic Link")

    rows = (
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
    ).run(as_dict=True)

    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(row.customer_name, []).append(row.contact_name)
    return grouped


def add_members(customer_name: str, contact_names: list[str]) -> None:
    customer = frappe.get_doc("HD Customer", customer_name)

    existing = {row.contact_name for row in customer.contacts}
    # An existing primary contact is a member too; seed it so a primary that
    # was never dynamic-linked doesn't fail validate_contacts().
    if customer.primary_contact and customer.primary_contact not in existing:
        customer.append("contacts", {"contact_name": customer.primary_contact})
        existing.add(customer.primary_contact)

    for contact_name in contact_names:
        if contact_name not in existing:
            customer.append("contacts", {"contact_name": contact_name})
            existing.add(contact_name)

    customer.save(ignore_permissions=True)
