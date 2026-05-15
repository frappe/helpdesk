import frappe


def sync_erp_customer_to_helpdesk(doc, method):
    if not should_sync():
        return

    if doc.flags.get("ignore_erpnext_sync"):
        return

    hd_customer_exists = frappe.db.exists("HD Customer", {"erp_customer": doc.name})
    if not hd_customer_exists:
        hd_doc = frappe.get_doc(
            {
                "doctype": "HD Customer",
                "customer_name": doc.customer_name,
                "erp_customer": doc.name,
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
            {"erp_customer": doc.name},
            "image",
            doc.image,
        )


def should_sync():
    return "erpnext" in frappe.get_installed_apps() and frappe.db.get_single_value(
        "ERPNext HD Settings", "enabled"
    )


def set_links(erp_customer_name: str, hd_customer_name: str):
    frappe.db.set_value(
        "HD Customer", hd_customer_name, "erp_customer", erp_customer_name
    )
    frappe.db.set_value("Customer", erp_customer_name, "hd_customer", hd_customer_name)
