import frappe
from frappe import _
from frappe.installer import install_app


def execute():
    if "studio" not in frappe.get_all_apps():
        frappe.throw(
            _(
                "Helpdesk now needs the Studio app for the customer portal. Run `bench get-app studio`, then migrate again."
            )
        )
    install_app("studio")
