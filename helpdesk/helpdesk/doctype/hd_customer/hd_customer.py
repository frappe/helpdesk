# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.contacts.doctype.contact.contact import invite_user
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
        self.validate_contacts()

    def validate_contacts(self):
        if len(self.contacts) == 0:
            return

        if len(self.contacts) == 1:
            # make the first contact primary if there is only one contact
            self.contacts[0].is_primary = True

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
        self.handle_roles()

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

    def handle_roles(self):
        # if any contact has is_manager set to true, then set the role of that contact to Customer Manager, and remove the role from other contacts
        if frappe.flags.ignore_customer_role:
            return
        if not self.has_value_changed("contacts"):
            return
        for contact in self.contacts:
            user = self.get_user(contact.contact_name)
            if not user:
                continue
            user_doc = frappe.get_doc("User", user)
            if contact.is_manager:
                # add HD Customer Manager role to the contact
                user_doc.append_roles("HD Customer Manager", "HD Customer")
            else:
                # add HD Customer role and remove HD Customer Manager role from the contact)
                user_doc.append_roles("HD Customer")
                user_doc.remove_roles("HD Customer Manager")
            user_doc.save()

    def get_user(self, contact_name, throw=True):
        user = frappe.get_value("Contact", contact_name, "user")
        if user:
            return user

        # fallback to email if user is not set for the contact
        email = frappe.get_value("Contact", contact_name, "email_id")
        if email:
            if user := frappe.db.exists("User", email):
                frappe.db.set_value("Contact", contact_name, "user", user)
            return user
        elif throw:
            frappe.throw(_("No user linked to contact {0}").format(contact_name))
        else:
            return None

    @frappe.whitelist()
    @agent_only
    def get_contacts(self):

        result = []
        for contact in self.contacts:
            info = frappe.get_value(
                "Contact",
                contact.contact_name,
                ["email_id", "mobile_no", "phone", "image", "user"],
            )
            if not info:
                continue

            email_id, mobile_no, phone, image, user = info

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
                    "last_active": (
                        frappe.get_value("User", user, "last_active") if user else None
                    ),
                    "ticket_count": (
                        len(pending_tickets_count) if pending_tickets_count else 0
                    ),
                }
            )
            # result = sort by is_primary first then is_manager
            result.sort(
                key=lambda x: (not x["is_primary"], not x["is_manager"]),
            )
        return result

    @frappe.whitelist()
    def update_contacts(self, contacts: str, role: str):
        roles = frappe.get_roles()
        if "System Manager" not in roles or "Agent Manager" not in roles:
            frappe.throw(_("You do not have permission to update contacts"))
        try:
            contacts = frappe.parse_json(contacts)
            is_manager = role == "HD Customer Manager"
            for contact in contacts:
                self.create_user_if_not_exist(contact)
                self.append(
                    "contacts", {"contact_name": contact, "is_manager": is_manager}
                )
            self.save()
        except Exception:
            frappe.throw(_("Invalid users data"))

    def create_user_if_not_exist(self, contact):
        user_linked = self.get_user(contact, throw=False)
        if user_linked:
            return
        invite_user(contact)

    @frappe.whitelist()
    @agent_only
    def get_pending_invites(self):
        pending_invites = frappe.db.get_all(
            "User Invitation",
            filters={
                "app_name": "helpdesk",
                "status": "Pending",
                "customer": self.name,
            },
            fields=[
                "name",
                "email",
                "invited_by",
                "creation",
            ],
        )
        res = []
        for pending_invitation in pending_invites:
            roles = frappe.db.get_all(
                "User Role",
                fields=["role"],
                filters={"parent": pending_invitation.name},
            )
            res.append(
                {
                    "name": pending_invitation.name,
                    "email": pending_invitation.email,
                    "invited_by": pending_invitation.invited_by,
                    "invited_on": pending_invitation.creation,
                    "roles": [r.role for r in roles],
                }
            )
        return res
