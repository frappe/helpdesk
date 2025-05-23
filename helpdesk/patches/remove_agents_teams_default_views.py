import frappe


def execute():
    print("Removing default views of agents")
    frappe.db.delete("HD View", {"dt": "HD Agent"})
    print("Removed default views of agents")
    print("--------------------")
    print("Removing default views of teams")
    frappe.db.delete("HD View", {"dt": "HD Team"})
    print("Removed default views of teams")
