import frappe
from frappe import _

# ERPNext Customer doc_events hooks (registered in hooks.py)


def after_insert(doc, method):
    """Called when an ERPNext Customer is created. Creates or links a matching HD Customer."""
    if doc.flags.get("ignore_erpnext_sync"):
        return
    if "erpnext" not in frappe.get_installed_apps():
        return
    if doc.get("hd_customer"):
        return

    create_or_link_hd_customer(doc)


def on_update(doc, method):
    """Called when an ERPNext Customer is saved. Propagates customer_name and image to the linked HD Customer."""
    if doc.flags.get("ignore_erpnext_sync"):
        return
    if "erpnext" not in frappe.get_installed_apps():
        return

    hd_customer_name = doc.get("hd_customer")
    if not hd_customer_name:
        return

    if not (doc.has_value_changed("customer_name") or doc.has_value_changed("image")):
        return

    frappe.db.set_value(
        "HD Customer",
        hd_customer_name,
        {
            "customer_name": doc.customer_name,
            "image": doc.image,
        },
        update_modified=False,
    )


# Sync helpers
def create_or_link_hd_customer(doc) -> str | None:
    """
    Sync a single ERPNext Customer doc to HD Customer.
    Resolution order:
      1. HD Customer named after erp.customer_name exists AND has no erpnext_customer set → link it
      2. HD Customer named after erp.name exists AND has no erpnext_customer set → link it
      3. Neither available → create HD Customer with customer_name = erp.name (always unique)
    Returns the HD Customer name that was linked or created, or None on failure.
    """
    # Step 1 — match by customer_name, only if that HD Customer is not already linked elsewhere
    if frappe.db.exists("HD Customer", doc.customer_name) and not frappe.db.get_value(
        "HD Customer", doc.customer_name, "erpnext_customer"
    ):
        set_links(doc.name, doc.customer_name)
        return doc.customer_name

    # Step 2 — match by ERPNext unique name, only if unlinked
    if frappe.db.exists("HD Customer", doc.name) and not frappe.db.get_value(
        "HD Customer", doc.name, "erpnext_customer"
    ):
        set_links(doc.name, doc.name)
        return doc.name

    # Step 3 — create with erp.name as customer_name (guaranteed unique)
    hd_doc = frappe.model.mapper.get_mapped_doc(
        "Customer",
        doc.name,
        {
            "Customer": {
                "doctype": "HD Customer",
                "field_map": {
                    "name": "customer_name",
                    "image": "image",
                },
            }
        },
    )

    hd_doc.flags.ignore_erpnext_sync = True
    hd_doc.insert(ignore_permissions=True)

    set_links(doc.name, hd_doc.name)
    return hd_doc.name


def set_links(erp_customer_name: str, hd_customer_name: str):
    frappe.db.set_value(
        "HD Customer", hd_customer_name, "erpnext_customer", erp_customer_name
    )
    frappe.db.set_value("Customer", erp_customer_name, "hd_customer", hd_customer_name)


# API methods
@frappe.whitelist()
def is_unsynced() -> bool:
    """Return True when HD Customer and ERPNext Customer counts differ (sync needed)."""
    if "erpnext" not in frappe.get_installed_apps():
        return False

    hd_count = frappe.db.count("HD Customer")
    erp_count = frappe.db.count("Customer")
    return hd_count != erp_count


# Called from ERPNext Customer list bulk action
@frappe.whitelist()
def bulk_sync_erpnext_customers_to_hd(customer_names: list[str]) -> dict:
    """Sync a list of ERPNext Customers to HD. Called from ERPNext Customer list bulk action."""
    created = 0
    skipped = 0

    for customer_name in customer_names:
        result = sync_erpnext_customer_to_hd(customer_name)
        if result["status"] == "created":
            created += 1
        else:
            skipped += 1

    return {"created": created, "skipped": skipped}


# Called from ERPNext Customer form button
@frappe.whitelist()
def sync_erpnext_customer_to_hd(customer_name: str) -> dict:
    """Sync a single ERPNext Customer to HD Customer. Called from ERPNext Customer form button."""
    if "erpnext" not in frappe.get_installed_apps():
        return {"status": "skipped", "reason": "ERPNext not installed"}

    erp_customer = frappe.get_doc("Customer", customer_name)

    if erp_customer.get("hd_customer"):
        return {"status": "skipped", "reason": "Already synced"}

    hd_name = create_or_link_hd_customer(erp_customer)
    return {"status": "created", "hd_customer": hd_name}


# Called from HD Customer list 'Sync with ERPNext' button, and from patch and after_install for initial reconciliation on install
@frappe.whitelist()
def sync_all_customers_with_erpnext() -> dict:
    """
    Full bi-directional reconciliation. Used by:
    - HD Customer list 'Sync with ERPNext' button
    - Patch (initial reconciliation on install)
    Emits real-time socket events: helpdesk:erpnext-sync-start / helpdesk:erpnext-sync-end
    """
    roles = frappe.get_roles(frappe.session.user)
    if not (
        "Administrator" in roles
        or "System Manager" in roles
        or "Agent Manager" in roles
    ):
        frappe.throw(
            msg=_("You are not permitted to access this resource."),
            title=_("Not Allowed"),
            exc=frappe.PermissionError,
        )

    if "erpnext" not in frappe.get_installed_apps():
        return {"status": "skipped", "reason": "ERPNext not installed"}

    frappe.publish_realtime(
        "helpdesk:erpnext-sync-start",
        user=frappe.session.user,
    )

    try:
        created_in_erpnext = sync_hd_to_erpnext()
        created_in_hd = sync_erpnext_to_hd()
    finally:
        frappe.publish_realtime(
            "helpdesk:erpnext-sync-end",
            user=frappe.session.user,
        )

    return {
        "created_in_erpnext": created_in_erpnext,
        "created_in_hd": created_in_hd,
    }


def sync_hd_to_erpnext() -> int:
    """Create ERPNext Customers for HD Customers that are not yet synced."""
    hd_customers_to_sync = frappe.get_all(
        "HD Customer",
        filters={"erpnext_customer": ("is", "not set")},
        fields=["name"],
    )

    created = 0
    for customer in hd_customers_to_sync:
        try:
            hd_doc = frappe.get_doc("HD Customer", customer.name)
            hd_doc.sync_to_erpnext()
            created += 1
        except Exception:
            frappe.log_error(
                title="ERPNext Customer Sync Failed",
                message=frappe.get_traceback(),
            )

    return created


def sync_erpnext_to_hd() -> int:
    """Create or link HD Customers for ERPNext Customers that are not yet synced."""
    unsynced_erp_customers = frappe.get_all(
        "Customer",
        filters={"hd_customer": ("is", "not set")},
        fields=["name"],
    )

    created = 0
    for customer in unsynced_erp_customers:
        try:
            erp_doc = frappe.get_doc("Customer", customer.name)
            create_or_link_hd_customer(erp_doc)
            created += 1
        except Exception:
            frappe.log_error(
                title="HD Customer Sync Failed",
                message=frappe.get_traceback(),
            )

    return created


# This covers only the case when Helpdesk is installed after ERPNext. If ERPNext is installed after helpdesk, the field will be created via after_install in erpnext
# calledn via patch and after_install of ERPNext
def setup_erpnext_customer_sync():
    """
    Create the hd_customer custom field on ERPNext Customer and enqueue initial reconciliation.
    Called from after_install (when Helpdesk is installed after ERPNext) and daily scheduler.
    """
    if "erpnext" not in frappe.get_installed_apps():
        return

    create_helpdesk_fields_in_customer()

    # TODO: whether should be done via initial sync or via button in Helpdesk.
    frappe.enqueue(
        "helpdesk.helpdesk.integrations.erpnext.customer.sync_all_customers_with_erpnext",
        queue="long",
        timeout=60000,
    )


def create_helpdesk_fields_in_customer():
    """Create the hd_customer custom field on ERPNext Customer. Called from after_install of ERPNext."""
    if "helpdesk" not in frappe.get_installed_apps():
        return

    if not frappe.db.exists(
        "Custom Field", {"dt": "Customer", "fieldname": "hd_customer"}
    ):
        from frappe.custom.doctype.custom_field.custom_field import create_custom_field

        create_custom_field(
            "Customer",
            {
                "fieldname": "hd_customer",
                "label": "HD Customer",
                "fieldtype": "Data",
                "read_only": 1,
            },
        )
