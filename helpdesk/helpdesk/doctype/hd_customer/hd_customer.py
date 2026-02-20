# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


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
        rows = ["customer_name", "domain", "creation", "image"]

        return {"columns": columns, "rows": rows}

    def validate(self):
        self.validate_members()

    def validate_members(self):
        if len(self.contacts) == 0:
            return
        primary_contacts = [contact for contact in self.contacts if contact.is_primary]
        if len(primary_contacts) == 0:
            frappe.throw(_("At least one primary contact is required"))

        if len(primary_contacts) > 1:
            frappe.throw(_("Only one primary contact is allowed"))

        # check for duplicate contacts
        contact_names = [contact.contact_name for contact in self.contacts]
        if len(contact_names) != len(set(contact_names)):
            frappe.throw(_("Duplicate contacts are not allowed"))

    def before_save(self):
        self.set_primary_member_details()

    def set_primary_member_details(self):
        if not self.contacts:
            return

        primary_contact = [
            contact.contact_name for contact in self.contacts if contact.is_primary
        ]

        primary_contact = primary_contact[0]
        self.primary_member = primary_contact

        [email, mobile_no, phone] = frappe.get_value(
            "Contact",
            primary_contact,
            ["email_id", "mobile_no", "phone"],
        )
        if email:
            self.email_id = email
        if mobile_no or phone:
            self.mobile_no = mobile_no or phone
