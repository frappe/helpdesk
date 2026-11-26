import frappe


def execute():
    """Give customer managers both customer roles; invites accepted earlier could miss one."""
    customers = frappe.get_all(
        "HD Customer Member", {"is_manager": 1}, pluck="parent", distinct=True
    )
    for name in customers:
        customer = frappe.get_doc("HD Customer", name)
        for row in customer.contacts:
            if row.is_manager:
                customer.sync_contact_role(row)
