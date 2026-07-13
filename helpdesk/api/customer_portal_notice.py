import frappe
from frappe.realtime import get_website_room

from helpdesk.utils import agent_manager_only

NOTICE_FLAG = "show_customer_portal_permission_notice"


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def dismiss_notice() -> None:
    """Permanently dismiss the customer portal permission change notice."""
    disable_notice()


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def restore_ticket_access() -> None:
    """Restore pre-migration ticket visibility for customer contacts.

    Promotes every customer contact to a customer manager in a background
    job, so each contact can again see all tickets of their customer.
    Dismisses the notice once the job is queued.
    """
    frappe.enqueue(
        promote_all_contacts_to_managers,
        queue="long",
        job_id="promote_all_contacts_to_managers",
        deduplicate=True,
    )


def disable_notice() -> None:
    """Turn the flag off and notify connected clients, publishing the same
    realtime event HD Settings emits from its on_update."""
    frappe.db.set_single_value("HD Settings", NOTICE_FLAG, 0)
    frappe.publish_realtime(
        "helpdesk:settings-updated", room=get_website_room(), after_commit=True
    )


def promote_all_contacts_to_managers() -> None:
    """Mark every customer contact as manager and grant the manager roles."""
    users = get_users_of_non_manager_contacts()
    mark_all_members_as_managers()
    grant_manager_roles(users)
    for user in users:
        frappe.clear_cache(user=user)


def get_users_of_non_manager_contacts() -> list[str]:
    """Users linked to contacts that are not managers yet. Contacts without
    a linked user are skipped, there is no user to grant the role to."""
    contact_names = frappe.get_all(
        "HD Customer Member",
        filters={"is_manager": 0, "parenttype": "HD Customer"},
        parent_doctype="HD Customer",
        pluck="contact_name",
        distinct=True,
    )
    if not contact_names:
        return []

    return frappe.get_all(
        "Contact",
        filters={"name": ("in", contact_names), "user": ("is", "set")},
        pluck="user",
        distinct=True,
    )


def mark_all_members_as_managers() -> None:
    Member = frappe.qb.DocType("HD Customer Member")
    (
        frappe.qb.update(Member)
        .set(Member.is_manager, 1)
        .where((Member.is_manager == 0) & (Member.parenttype == "HD Customer"))
    ).run()


def grant_manager_roles(users: list[str]) -> None:
    """Bulk-insert the customer roles for users that are missing them."""
    roles = ("HD Customer Manager", "HD Customer")
    if not users:
        return

    existing = frappe.get_all(
        "Has Role",
        filters={
            "parenttype": "User",
            "parent": ("in", users),
            "role": ("in", roles),
        },
        fields=["parent", "role"],
    )
    existing_pairs = {(row.parent, row.role) for row in existing}
    values = [
        (frappe.generate_hash(length=10), user, role, "roles", "User")
        for user in users
        for role in roles
        if (user, role) not in existing_pairs
    ]
    if values:
        frappe.db.bulk_insert(
            "Has Role", ["name", "parent", "role", "parentfield", "parenttype"], values
        )
