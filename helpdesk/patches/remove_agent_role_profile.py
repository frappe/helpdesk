import frappe

def execute():
    if frappe.db.exists("Role Profile", "Agent"):
        for user in frappe.get_all("User", {"role_profile_name": "Agent"}):
            user_doc = frappe.get_doc("User", user)
            user_doc.role_profile_name = ""
            user_doc.save()
        frappe.delete_doc("Role Profile", "Agent")