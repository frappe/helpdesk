import frappe


def execute():
    legacy_app_field = frappe.db.has_column("Tag", "app")
    fields = ["name", "app"] if legacy_app_field else ["name"]
    for tag in frappe.get_all("Tag", fields=fields):
        doc = frappe.get_doc("Tag", tag.name)
        legacy_app = tag.get("app")
        apps = {row.app_name for row in doc.get("apps", []) if row.app_name}
        changed = False
        if not apps:
            doc.append("apps", {"app_name": "frappe"})
            changed = True
            if legacy_app == "helpdesk":
                doc.append("apps", {"app_name": "helpdesk"})
                changed = True
            elif legacy_app:
                doc.append("apps", {"app_name": legacy_app})
                changed = True
        elif legacy_app and legacy_app not in apps:
            doc.append("apps", {"app_name": legacy_app})
            changed = True
        if changed:
            doc.save()

    for field in ("Tag-app", "Tag-color"):
        if frappe.db.exists("Custom Field", field):
            frappe.delete_doc("Custom Field", field, ignore_missing=True)
