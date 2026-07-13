import frappe
from frappe.permissions import add_permission, update_permission_property

# role -> has write access at permlevel 1
LEVEL_ONE_ROLES = {
    "System Manager": 1,
    "Agent": 1,
    "Agent Manager": 1,
    "HD Customer": 0,
    "HD Customer Manager": 0,
}


def execute():
    protect_existing_hidden_template_fields()
    mirror_permlevel_grants_into_custom_docperms()


def protect_existing_hidden_template_fields():
    """Raise custom fields hidden from customers to permlevel 1."""
    hidden_fields = frappe.get_all(
        "HD Ticket Template Field",
        filters={"hide_from_customer": 1},
        pluck="fieldname",
        distinct=True,
    )
    for fieldname in hidden_fields:
        custom_field = frappe.db.get_value(
            "Custom Field",
            {"dt": "HD Ticket", "fieldname": fieldname, "permlevel": 0},
        )
        if custom_field:
            frappe.db.set_value("Custom Field", custom_field, "permlevel", 1)


def mirror_permlevel_grants_into_custom_docperms():
    """
    When Custom DocPerm rows exist for a doctype, Frappe ignores the
    standard perms from hd_ticket.json entirely. Sites with customised
    HD Ticket permissions (e.g. guest ticket creation enabled) must
    therefore receive the new permlevel-1 rows explicitly, else agents
    would lose write access to the protected fields.
    """
    if not frappe.db.exists("Custom DocPerm", {"parent": "HD Ticket"}):
        return
    for role, can_write in LEVEL_ONE_ROLES.items():
        has_role = frappe.db.exists(
            "Custom DocPerm", {"parent": "HD Ticket", "role": role, "permlevel": 0}
        )
        has_level_one = frappe.db.exists(
            "Custom DocPerm", {"parent": "HD Ticket", "role": role, "permlevel": 1}
        )
        if not has_role or has_level_one:
            continue
        add_permission("HD Ticket", role, permlevel=1)  # grants read
        if can_write:
            update_permission_property("HD Ticket", role, 1, "write", 1, validate=False)
