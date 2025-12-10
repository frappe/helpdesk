import frappe


@frappe.whitelist()
def get_app_version():
    return frappe.get_attr("helpdesk" + ".__version__")
