import frappe
from frappe import _
from frappe.installer import install_app


def execute():
    # install_app's "already installed" return leaves flags.in_install set
    if "studio" in frappe.get_installed_apps():
        return
    if "studio" not in frappe.get_all_apps():
        frappe.throw(
            _(
                "Helpdesk now needs the Studio app for the customer portal. Run `bench get-app studio`, then migrate again."
            )
        )
    install_app("studio")
