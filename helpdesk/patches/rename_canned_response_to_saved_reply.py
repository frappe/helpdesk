import frappe


def execute():
    old = "HD Canned Response"
    new = "HD Saved Reply"

    if frappe.db.exists("DocType", new):
        return

    if not frappe.db.exists("DocType", old):
        return

    frappe.rename_doc("DocType", old, new)
    print("Migrated", old, "to", new)
