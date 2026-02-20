# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.utils import agent_only


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
        self.set_primary_contact_details()
        self.set_manager_if_not_exists()

    def set_primary_contact_details(self):
        if not self.contacts:
            return

        primary_contact = [
            contact.contact_name for contact in self.contacts if contact.is_primary
        ]

        self.primary_contact = primary_contact[0]

        [email, mobile_no, phone] = frappe.get_value(
            "Contact",
            primary_contact,
            ["email_id", "mobile_no", "phone"],
        )

        self.email_id = email
        self.mobile_no = mobile_no or phone

    def set_manager_if_not_exists(self):
        if not self.contacts:
            return
        manager_contact = [
            contact.contact_name for contact in self.contacts if contact.is_manager
        ]
        if manager_contact:
            return
        primary_contact = [
            contact.contact_name for contact in self.contacts if contact.is_primary
        ][0]
        for contact in self.contacts:
            contact.is_manager = contact.contact_name == primary_contact


@frappe.whitelist()
@agent_only
def get_contacts_for_customer(customer: str):
    # from customer doctype get contact list
    # and for each contact get the email_id and mobile_no, name, image from the contact doctype, get last modified as well
    # along with that get us tickets count ticket with status_category as Open or Paused
    customer_doc = frappe.get_doc("HD Customer", customer)
    contacts = customer_doc.contacts

    result = []
    for contact in contacts:
        info = frappe.get_value(
            "Contact",
            contact.contact_name,
            ["email_id", "mobile_no", "phone", "image", "modified"],
        )
        if not info:
            continue

        email_id, mobile_no, phone, image, modified = info
        pending_tickets_count = frappe.db.get_list(
            "HD Ticket",
            filters={
                "status_category": ["in", ["Open", "Paused"]],
            },
            or_filters=[
                ["raised_by", "=", contact.contact_name],
                ["contact", "=", contact.contact_name],
            ],
            pluck="name",
        )

        result.append(
            {
                "contact_name": contact.contact_name,
                "is_primary": contact.is_primary,
                "is_manager": contact.is_manager,
                "email_id": email_id,
                "mobile_no": mobile_no or phone,
                "image": image,
                "modified": modified,
                "ticket_count": (
                    len(pending_tickets_count) if pending_tickets_count else 0
                ),
            }
        )
    return result
