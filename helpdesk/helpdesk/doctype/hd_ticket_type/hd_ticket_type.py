import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketType(Document):
    def on_update(self):
        frappe.cache().delete_value("hd_ticket_type_keywords")

    def on_trash(self):
        self.prevent_system_delete()
        frappe.cache().delete_value("hd_ticket_type_keywords")

    def prevent_system_delete(self):
        if self.is_system:
            frappe.throw(_("System types can not be deleted"))
