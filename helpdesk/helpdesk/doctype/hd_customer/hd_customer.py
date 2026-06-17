# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.core.api.user_invitation import invite_by_email
from frappe.model.document import Document
from frappe.utils import validate_email_address

from helpdesk.integrations.erpnext.utils import cascade_rename, in_cascade
from helpdesk.integrations.erpnext.utils import should_sync as should_sync_with_erpnext
from helpdesk.integrations.erpnext.utils import validate_rename_conflict
from helpdesk.utils import agent_only, get_customers, is_agent

CUSTOMER_ROLES = ("HD Customer", "HD Customer Manager")


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
                "label": "Customer Type",
                "key": "customer_type",
                "width": "10rem",
                "type": "Select",
            },
            {
                "label": "Email ID",
                "key": "email_id",
                "width": "17rem",
                "type": "Data",
            },
            {
                "label": "Mobile No",
                "key": "mobile_no",
                "width": "12rem",
                "type": "Data",
            },
            {
                "label": "Created On",
                "key": "creation",
                "width": "8rem",
                "type": "Datetime",
            },
        ]
        rows = [
            "customer_name",
            "customer_type",
            "email_id",
            "mobile_no",
            "creation",
            "image",
        ]

        return {"columns": columns, "rows": rows}

    def validate(self):
        self.validate_contacts()

    def validate_contacts(self):
        if not self.contacts:
            return

        contact_names = [contact.contact_name for contact in self.contacts]
        if len(contact_names) != len(set(contact_names)):
            frappe.throw(_("Duplicate contacts are not allowed"))

        if self.primary_contact and self.primary_contact not in contact_names:
            frappe.throw(_("Primary contact must be one of the listed contacts"))

    def before_save(self):
        self.ensure_primary_contact_is_manager()
        self.handle_roles()

    def ensure_primary_contact_is_manager(self):
        # the primary is optional, but whoever is set as primary is a manager
        if not self.contacts or not self.primary_contact:
            return
        for contact in self.contacts:
            if contact.contact_name == self.primary_contact:
                contact.is_manager = True

    def handle_roles(self):
        # if any contact has is_manager set to true, then set the role of that contact to Customer Manager, and remove the role from other contacts
        if not self.has_value_changed("contacts"):
            return
        for contact in self.contacts:
            user = self.get_user(contact.contact_name, throw_error=False)
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

    def get_user(self, contact_name, throw_error=True):
        user = frappe.db.get_value("Contact", contact_name, "user")
        if user:
            return user

        # fallback to email if user is not set for the contact
        email = frappe.get_value("Contact", contact_name, "email_id")
        if email:
            if user := frappe.db.exists("User", email):
                frappe.db.set_value("Contact", contact_name, "user", user)
            return user
        elif throw_error:
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
                    "is_primary": int(contact.contact_name == self.primary_contact),
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
            # sort by is_primary first then is_manager
            result.sort(
                key=lambda x: (not x["is_primary"], not x["is_manager"]),
            )
        return result

    @frappe.whitelist()
    def add_contacts(self, contacts: str | list, role: str = "HD Customer") -> dict:
        """Add contacts that already have a linked user; invite the rest by email.

        Each entry can be a Contact name or an email address. Returns the
        contact names added directly and the result of the sent invitations.
        """
        self.validate_contact_update_permission(role)
        entries = frappe.parse_json(contacts) if isinstance(contacts, str) else contacts
        if not entries:
            frappe.throw(_("No contacts to add"))

        added, to_invite = [], []
        for entry in entries:
            contact_name, email = self.resolve_contact_entry(entry)
            if contact_name and self.get_user(contact_name, throw_error=False):
                if self.append_contact(contact_name, role):
                    added.append(contact_name)
            else:
                to_invite.append({"email": email, "contact": contact_name})

        if added:
            self.save()
        return {"added": added, "invite_result": self.invite_contacts(to_invite, role)}

    def validate_contact_update_permission(self, role: str) -> None:
        if role not in CUSTOMER_ROLES:
            frappe.throw(_("Invalid role {0}").format(role))
        roles = frappe.get_roles()
        if "System Manager" not in roles and "Agent Manager" not in roles:
            frappe.throw(
                _("You do not have permission to update contacts"),
                frappe.PermissionError,
            )

    def resolve_contact_entry(self, entry: str) -> tuple[str | None, str]:
        """Resolve an entry to a (contact name, email) pair."""
        if frappe.db.exists("Contact", entry):
            email = frappe.db.get_value("Contact", entry, "email_id")
            if not email:
                frappe.throw(_("Contact {0} has no email address").format(entry))
            return entry, email
        validate_email_address(entry, throw=True)
        return frappe.db.get_value("Contact", {"email_id": entry}, "name"), entry

    def append_contact(self, contact_name: str, role: str) -> bool:
        if any(row.contact_name == contact_name for row in self.contacts):
            return False
        self.append(
            "contacts",
            {
                "contact_name": contact_name,
                "is_manager": role == "HD Customer Manager",
            },
        )
        return True

    def invite_contacts(self, to_invite: list[dict], role: str) -> dict:
        result = {
            "invited_emails": [],
            "pending_invite_emails": [],
            "accepted_invite_emails": [],
            "disabled_user_emails": [],
        }
        for item in to_invite:
            params = {"customer": self.name}
            if item["contact"]:
                params["contact"] = item["contact"]
            response = invite_by_email(
                item["email"],
                roles=[role],
                redirect_to_path="/helpdesk",
                app_name="helpdesk",
                **params,
            )
            for key, emails in response.items():
                result.setdefault(key, []).extend(emails)
        return result

    @frappe.whitelist()
    def get_pending_invites(self):
        if "Agent Manager" not in frappe.get_roles():
            frappe.throw(_("You do not have permission to access this resource."))
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
            }
        )
        erp_doc.flags.ignore_erpnext_sync = True
        erp_doc.insert(ignore_permissions=True)
        frappe.db.set_value("HD Customer", self.name, "erpnext_customer", erp_doc.name)

    def on_update(self):
        if not should_sync_with_erpnext():
            return

        if self.flags.get("ignore_erpnext_sync"):
            return

        if self.has_value_changed("image"):
            # check if exists
            erpnext_customer = frappe.db.get_value(
                "Customer", {"hd_customer": self.name}, "name"
            )
            if not erpnext_customer:
                return
            frappe.db.set_value(
                "Customer",
                {"hd_customer": self.name},
                "image",
                self.image,
            )

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


# Custom perms for list query. Only the `WHERE` part
# Used so that contact raising the ticket can see the customers they are part of
def permission_query(user):
    if is_agent(user):
        return ""

    customers = get_customers(user, get_roles=True)
    query = ""
    for i, c in enumerate(customers):
        prefix = " OR " if i > 0 else ""
        query += f"{prefix}`tabHD Customer`.name = '{c.get('name')}'"
    return query
