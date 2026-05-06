import frappe

from helpdesk.setup.default_views import default_views


def execute():
    if frappe.db.exists("HD View", "STD-VIEW-SLA-DUE") and not frappe.db.exists(
        "HD View", "STD-VIEW-SLA-ALERTS"
    ):
        frappe.rename_doc(
            "HD View", "STD-VIEW-SLA-DUE", "STD-VIEW-SLA-ALERTS", force=True
        )

    for view in default_views:
        view_name = view["name"]

        if not frappe.db.exists("HD View", view_name):
            continue

        doc = frappe.get_doc("HD View", view_name)
        doc.update(
            {
                "columns": view["columns"],
                "filters": view["filters"],
                "icon": view["icon"],
                "label": view["label"],
                "order_by": view["order_by"],
                "rows": view["rows"],
                "dt": view["dt"],
                "route_name": view["route_name"],
                "type": view["type"],
            }
        )
        doc.save(ignore_permissions=True)
