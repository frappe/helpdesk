# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from helpdesk.integrations.erpnext.utils import (
    cascade_rename,
    in_cascade,
    map_source_to_target_values,
)
from helpdesk.integrations.erpnext.utils import should_sync as should_sync_with_erpnext
from helpdesk.integrations.erpnext.utils import (
    sync_related_fields,
    validate_rename_conflict,
)


class HDCustomer(Document):
    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Name",
                "key": "name",
                "width": "17rem",
                "type": "Data",
            },
            {
                "label": "Domain",
                "key": "domain",
                "width": "24rem",
                "type": "Data",
            },
            {
                "label": "Created On",
                "key": "creation",
                "width": "8rem",
                "type": "Datetime",
            },
        ]
        rows = ["name", "domain", "image", "creation", "owner"]
        return {"columns": columns, "rows": rows}

    def after_insert(self):
        if should_sync_with_erpnext() and not self.flags.get("ignore_erpnext_sync"):
            self.create_customer_in_erpnext()

    def create_customer_in_erpnext(self):
        if self.erpnext_customer:
            return

        erpnext_customer_exists = frappe.db.exists(
            "Customer", {"hd_customer": self.name}
        )
        if erpnext_customer_exists:
            return

        # create a new customer in ERPNext with the same name as the HD Customer and link them together
        erp_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": self.customer_name,
                "hd_customer": self.name,
                **map_source_to_target_values(self),
            }
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        frappe.db.set_value("HD Customer", self.name, "erpnext_customer", erp_doc.name)

    def on_update(self):
        if not should_sync_with_erpnext() or self.flags.get("ignore_erpnext_sync"):
            return

        sync_related_fields(self)

    def before_rename(self, olddn, newdn, merge=False):
        validate_rename_conflict("HD Customer", olddn, newdn, merge)

    def after_rename(self, olddn, newdn, merge=False):
        cascade_rename("HD Customer", olddn, newdn, merge)

    def on_trash(self):
        if in_cascade() or not should_sync_with_erpnext():
            return

        erpnext_customer = frappe.db.get_value(
            "Customer", {"hd_customer": self.name}, "name"
        )
        if erpnext_customer:
            # Clear the back-link first so CustomCustomer.on_trash won't try to
            # delete this HD Customer again (it's already being deleted).
            frappe.db.set_value("Customer", erpnext_customer, "hd_customer", None)
            frappe.delete_doc("Customer", erpnext_customer, ignore_permissions=True)
