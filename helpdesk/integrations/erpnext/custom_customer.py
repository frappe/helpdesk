import frappe
from erpnext.selling.doctype.customer.customer import Customer


class CustomCustomer(Customer):
    def after_rename(self, olddn, newdn, merge=False):
        super().after_rename(olddn, newdn, merge)

        frappe.db.set_value(
            "HD Customer",
            {"erp_customer": olddn},
            "erp_customer",
            newdn,
        )
