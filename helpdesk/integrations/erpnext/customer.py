import frappe
from frappe import _


def sync_erpnext_customer_to_helpdesk(doc, method):
    if not should_sync():
        return

    if doc.flags.get("ignore_erpnext_sync"):
        return

    hd_customer_exists = frappe.db.exists("HD Customer", {"erpnext_customer": doc.name})
    if not hd_customer_exists:
        hd_doc = frappe.get_doc(
            {
                "doctype": "HD Customer",
                "customer_name": doc.customer_name,
                "erpnext_customer": doc.name,
                "image": doc.image,
            }
        )
        hd_doc.flags.ignore_erpnext_sync = True
        hd_doc.insert(ignore_permissions=True)
        set_links(doc.name, hd_doc.name)
        return hd_doc.name

    if doc.has_value_changed("image"):
        frappe.db.set_value(
            "HD Customer",
            {"erpnext_customer": doc.name},
            "image",
            doc.image,
        )


def should_sync():
    return "erpnext" in frappe.get_installed_apps() and frappe.db.get_single_value(
        "ERPNext HD Settings", "enabled"
    )


def set_links(erpnext_customer_name: str, hd_customer_name: str):
    frappe.db.set_value(
        "HD Customer",
        hd_customer_name,
        "erpnext_customer",
        erpnext_customer_name,
        update_modified=False,
    )
    frappe.db.set_value(
        "Customer",
        erpnext_customer_name,
        "hd_customer",
        hd_customer_name,
        update_modified=False,
    )


@frappe.whitelist()
def get_sync_info() -> dict:
    if "erpnext" not in frappe.get_installed_apps():
        return {"enabled": False}

    enabled = bool(frappe.db.get_single_value("ERPNext HD Settings", "enabled"))
    if not enabled:
        return {"enabled": False}

    hd_count = frappe.db.count("HD Customer")
    erp_count = frappe.db.count("Customer")
    return {
        "enabled": True,
        "hd_count": hd_count,
        "erp_count": erp_count,
        "in_sync": hd_count == erp_count,
    }


@frappe.whitelist()
def sync_hd_erpnext_customers() -> None:
    if not should_sync():
        frappe.throw(
            _("ERPNext integration is not enabled"), title=_("Cannot Sync Customers")
        )

    job_id = f"sync_customers_{frappe.utils.get_datetime().timestamp()}"
    frappe.enqueue(
        sync_all_customers,
        queue="long",
        timeout=12000,
        job_id=job_id,
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
        # Match by name: HD Customer name == ERP Customer name
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
        # Match by name: ERP Customer name == HD Customer name
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
                }
            )
            erp_doc.flags.ignore_erpnext_sync = True
            erp_doc.insert(ignore_permissions=True)
            set_links(erp_doc.name, hd.name)

    frappe.publish_realtime(
        "helpdesk:erpnext-sync-end",
        user=frappe.session.user,
    )


def setup_test_data():
    """
    Resets customers on both sides and seeds fresh test data.

    ERP Customers (5): two share the same customer_name to test duplicate handling.
    HD Customers (5): all distinct names, none overlapping with ERP names.
    Integration is left disabled so sync can be triggered manually.
    """
    # Wipe existing
    for name in frappe.get_all("HD Customer", pluck="name"):
        frappe.delete_doc("HD Customer", name, force=True, ignore_permissions=True)

    for name in frappe.get_all("Customer", pluck="name"):
        frappe.delete_doc("Customer", name, force=True, ignore_permissions=True)

    frappe.db.set_single_value("ERPNext HD Settings", "enabled", 0)

    cg = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
    ter = frappe.db.get_value("Territory", {"is_group": 0}, "name")

    erp_seeds = [
        "Alpha Industries",
        "Beta Solutions",
        "Duplicate Corp",
        "Duplicate Corp",  # intentional duplicate customer_name
        "Gamma Enterprises",
    ]
    for customer_name in erp_seeds:
        doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_group": cg,
                "territory": ter,
            }
        )
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        print(f"ERP  {doc.name!r}  (customer_name={doc.customer_name!r})")

    hd_seeds = [
        "Omega Corp",
        "Zeta Labs",
        "Delta Systems",
        "Sigma Works",
        "Lambda Tech",
    ]
    for customer_name in hd_seeds:
        doc = frappe.get_doc({"doctype": "HD Customer", "customer_name": customer_name})
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        print(f"HD   {doc.name!r}")

    print("\nDone. Integration disabled.")
