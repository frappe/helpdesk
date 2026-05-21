# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.integrations.erpnext.utils import create_customer_field


class ERPNextHDSettings(Document):
    # validate to check if ERPNext is installed or not, if enabled is checked then frapep.throw ERPNext is not installed on your site.
    def validate(self):
        if not self.enabled:
            return
        is_erpnext_installed = "erpnext" in frappe.get_installed_apps()
        if not is_erpnext_installed:
            # throw this error message if ERPNext is not installed on the site and enabled is checked
            frappe.throw(
                _(
                    "ERPNext is not installed on your site. Please install ERPNext to enable this setting.",
                )
            )

    def before_save(self):
        if not self.enabled:
            return

        create_customer_field()
