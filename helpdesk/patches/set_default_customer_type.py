import frappe

from helpdesk.integrations.erpnext.utils import should_sync


def execute():
    """Backfill customer_type for existing customers created before the field existed."""
    if should_sync():
        sync_customer_type_from_erpnext()
    else:
        set_default_customer_type()


def sync_customer_type_from_erpnext():
    """Copy customer_type from each linked ERPNext Customer onto its HD Customer."""
    linked_customers = frappe.get_all(
        "HD Customer",
        filters={
            "customer_type": ["is", "not set"],
            "erpnext_customer": ["is", "set"],
        },
        fields=["name", "erpnext_customer"],
    )
    if not linked_customers:
        return

    erpnext_names = list({customer.erpnext_customer for customer in linked_customers})
    customer_types = dict(
        frappe.get_all(
            "Customer",
            filters={"name": ["in", erpnext_names]},
            fields=["name", "customer_type"],
            as_list=True,
        )
    )

    hd_names_by_type: dict[str, list[str]] = {}
    for customer in linked_customers:
        customer_type = customer_types.get(customer.erpnext_customer)
        if customer_type:
            hd_names_by_type.setdefault(customer_type, []).append(customer.name)

    for customer_type, hd_names in hd_names_by_type.items():
        frappe.db.set_value(
            "HD Customer",
            {"name": ["in", hd_names]},
            "customer_type",
            customer_type,
            update_modified=False,
        )


def set_default_customer_type():
    """Default any remaining customers without a customer_type to "Company"."""
    frappe.db.set_value(
        "HD Customer",
        {"customer_type": ["is", "not set"]},
        "customer_type",
        "Company",
        update_modified=False,
    )
