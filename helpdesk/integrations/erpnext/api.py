import frappe
from frappe import _

from helpdesk.integrations.erpnext.doc_share import sync_shared_docs
from helpdesk.integrations.erpnext.user_permission import sync_user_permissions
from helpdesk.integrations.erpnext.utils import set_links, should_sync


@frappe.whitelist()
def get_sync_info() -> dict:
    """Drive the ERPNext integration settings UI. `in_sync` gates the 'Sync now'
    action. Whether ERPNext is installed is read on the frontend from the boot
    `apps` list, not from here."""
    if "erpnext" not in frappe.get_installed_apps():
        return {"enabled": False, "in_sync": False}

    if not frappe.has_permission("Customer", "read") or not frappe.has_permission(
        "HD Customer", "read"
    ):
        return {"enabled": False, "in_sync": False}

    if not frappe.has_permission("HD Customer", "read") or not frappe.has_permission(
        "Customer", "read"
    ):
        return {"enabled": False}

    enabled = bool(frappe.db.get_single_value("ERPNext HD Settings", "enabled"))
    if not enabled:
        return {"enabled": False}

    return {"enabled": enabled, "in_sync": in_sync()}


def in_sync() -> bool:
    """True when every HD Customer is linked to an ERP Customer and vice versa.
    Sync is a no-op in this state; the UI uses this to gate the 'Sync Customers'
    button.
    """
    if frappe.db.count("HD Customer", {"erpnext_customer": ["is", "not set"]}):
        return False
    if frappe.db.count("Customer", {"hd_customer": ["is", "not set"]}):
        return False
    return True


@frappe.whitelist()
def sync_hd_erpnext_customers() -> None:
    frappe.has_permission("Customer", "write", throw=True)
    frappe.has_permission("HD Customer", "write", throw=True)
    if not should_sync():
        frappe.throw(
            _("ERPNext integration is not enabled"), title=_("Cannot Sync Customers")
        )

    frappe.enqueue(
        sync_all_customers,
        queue="long",
        timeout=12000,
        job_id="sync_hd_erpnext_customers",
        deduplicate=True,
    )


def sync_all_customers():
    """
    Union-merge HD Customers and ERPNext Customers.

    - Unlinked ERP customers are created or linked in HD Customer.
    - Unlinked HD customers are created or linked in ERP Customer.

    Matching is done by name. If a record with the same name exists on the
    other side but is unlinked, the two are linked instead of creating a duplicate.
    """
    frappe.publish_realtime(
        "helpdesk:erpnext-sync-start",
        user=frappe.session.user,
    )

    # ERP → HD
    unlinked_erp = frappe.get_all(
        "Customer",
        filters={"hd_customer": ["is", "not set"]},
        fields=["name", "customer_name", "image"],
    )
    for erp in unlinked_erp:
        existing_hd = frappe.db.get_value(
            "HD Customer",
            {"name": erp.name, "erpnext_customer": ["is", "not set"]},
            "name",
        )
        if existing_hd:
            set_links(erp.name, existing_hd)
        elif not frappe.db.exists("HD Customer", erp.name):
            hd_doc = frappe.get_doc(
                {
                    "doctype": "HD Customer",
                    "customer_name": erp.name,
                    "erpnext_customer": erp.name,
                    "image": erp.image,
                }
            )
            hd_doc.flags.ignore_erpnext_sync = True
            hd_doc.insert(ignore_permissions=True)
            set_links(erp.name, hd_doc.name)

    # HD → ERP
    unlinked_hd = frappe.get_all(
        "HD Customer",
        filters={"erpnext_customer": ["is", "not set"]},
        fields=["name", "customer_name", "image"],
    )
    for hd in unlinked_hd:
        existing_erp = frappe.db.get_value(
            "Customer",
            {"name": hd.name, "hd_customer": ["is", "not set"]},
            "name",
        )
        if existing_erp:
            set_links(existing_erp, hd.name)
        elif not frappe.db.exists("Customer", hd.name):
            erp_doc = frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": hd.customer_name,
                    "hd_customer": hd.name,
                    "image": hd.image,
                }
            )
            erp_doc.flags.ignore_erpnext_sync = True
            erp_doc.insert(ignore_permissions=True)
            set_links(erp_doc.name, hd.name)

    sync_user_permissions()
    sync_shared_docs()

    # after_commit so the frontend's get_sync_info reload sees the committed
    # links (in_sync = True) instead of pre-commit state. The job runs as the
    # triggering user (frappe.enqueue → set_user), so this reaches their room.
    frappe.publish_realtime(
        "helpdesk:erpnext-sync-end",
        user=frappe.session.user,
        after_commit=True,
    )
