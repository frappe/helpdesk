import frappe
from erpnext.selling.doctype.customer.customer import Customer

from helpdesk.integrations.erpnext.utils import (
    cascade_rename,
    in_cascade,
    set_links,
    should_sync,
    validate_rename_conflict,
)


class CustomCustomer(Customer):
    def after_insert(self):
        super().after_insert()

        if not should_sync():
            return

        if self.flags.get("ignore_erpnext_sync"):
            return

        hd_customer_exists = frappe.db.exists(
            "HD Customer", {"erpnext_customer": self.name}
        )
        if not hd_customer_exists:
            hd_doc = frappe.get_doc(
                {
                    "doctype": "HD Customer",
                    "customer_name": self.customer_name,
                    "erpnext_customer": self.name,
                    "image": self.image,
                }
            )
            hd_doc.flags.ignore_erpnext_sync = True
            hd_doc.insert(ignore_permissions=True)
            set_links(self.name, hd_doc.name)

    def on_update(self):
        super().on_update()

        if not should_sync():
            return

        if self.flags.get("ignore_erpnext_sync"):
            return

        if self.has_value_changed("image"):
            frappe.db.set_value(
                "HD Customer",
                {"erpnext_customer": self.name},
                "image",
                self.image,
            )

    def before_rename(self, olddn, newdn, merge=False):
        super().before_rename(olddn, newdn, merge)
        validate_rename_conflict("Customer", olddn, newdn, merge)

    def after_rename(self, olddn, newdn, merge=False):
        super().after_rename(olddn, newdn, merge)
        cascade_rename("Customer", olddn, newdn, merge)

    def on_trash(self):
        super().on_trash()

        if in_cascade() or not should_sync():
            return

        hd_customer = frappe.db.get_value(
            "HD Customer", {"erpnext_customer": self.name}, "name"
        )
        if hd_customer:
            # Clear the back-link first so HDCustomer.on_trash won't try to
            # delete this Customer again (it's already being deleted).
            frappe.db.set_value("HD Customer", hd_customer, "erpnext_customer", None)
            frappe.delete_doc("HD Customer", hd_customer, ignore_permissions=True)
