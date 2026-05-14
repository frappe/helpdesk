# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class HDCustomer(Document):
    def after_insert(self):
        self.sync_to_erpnext()

    def on_update(self):
        self.sync_update_to_erpnext()

    def sync_to_erpnext(self):
        if "erpnext" not in frappe.get_installed_apps():
            return
        if self.flags.get("ignore_erpnext_sync"):
            return
        if self.erpnext_customer:
            return

        erp_customer_doc = get_mapped_doc(
            "HD Customer",
            self.name,
            {
                "HD Customer": {
                    "doctype": "Customer",
                    "field_map": {
                        "customer_name": "customer_name",
                        "image": "image",
                    },
                }
            },
        )

        erp_customer_doc.customer_type = "Company"

        erp_customer_doc.flags.ignore_erpnext_sync = True
        erp_customer_doc.insert(ignore_permissions=True)

        self.db_set("erpnext_customer", erp_customer_doc.name)
        frappe.db.set_value(
            "Customer",
            erp_customer_doc.name,
            "hd_customer",
            self.name,
            update_modified=False,
        )

    def sync_update_to_erpnext(self):
        if "erpnext" not in frappe.get_installed_apps():
            return
        if self.flags.get("ignore_erpnext_sync"):
            return
        if not self.erpnext_customer:
            return
        if not (
            self.has_value_changed("customer_name") or self.has_value_changed("image")
        ):
            return

        frappe.db.set_value(
            "Customer",
            self.erpnext_customer,
            {
                "customer_name": self.customer_name,
                "image": self.image,
            },
            update_modified=False,
        )

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
        return {"columns": columns}
