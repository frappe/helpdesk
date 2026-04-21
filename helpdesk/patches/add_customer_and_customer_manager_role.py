import frappe


def execute():
    roles = ["HD Customer", "HD Customer Manager"]

    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc(
                {
                    "doctype": "Role",
                    "role_name": role_name,
                    "home_page": "/helpdesk",
                    "desk_access": 0,
                }
            ).insert()
        else:
            doc = frappe.get_doc("Role", role_name)
            doc.home_page = "/helpdesk"
            doc.desk_access = 0
            doc.save()
