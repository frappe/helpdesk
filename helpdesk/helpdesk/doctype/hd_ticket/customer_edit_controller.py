import frappe
from frappe import _
from frappe.model import no_value_fields

from helpdesk.consts import (
    CUSTOMER_ALWAYS_WRITABLE_FIELDS,
    PORTAL_INSERT_EXEMPT_FIELDS,
    SERVER_COMPUTED_FIELDS,
)
from helpdesk.ticket_fields import TicketFields
from helpdesk.utils import is_agent


class CustomerEditController:
    """What a customer may fill on insert and change after it; mixed into HDTicket."""

    def apply_portal_insert_rules(self):
        """The permlevel reset after this hook wipes fields the user cannot write;
        exempt server-set fields and the ones the template lets a customer fill."""
        # a System Manager pulling emails is not the sender of the pulled tickets
        if is_agent() or "System Manager" in frappe.get_roles():
            return
        if frappe.session.user != "Guest":
            self.raised_by = frappe.session.user
        self.via_customer_portal = 1
        self.flags.ignore_permlevel_for_fields = [
            *PORTAL_INSERT_EXEMPT_FIELDS,
            *(row.fieldname for row in self.customer_writable_rows()),
        ]

    def check_update_perms(self):
        # not gated on via_customer_portal: agent-raised tickets are still the customer's
        old_doc = self.get_doc_before_save()
        if not old_doc or is_agent():
            return
        # rating the ticket is the one thing a closing email asks the customer to do
        if self.flags.get("ignore_closed_ticket_guard"):
            return
        is_closed = old_doc.status == "Closed"
        is_rated = bool(old_doc.feedback)
        if is_closed or is_rated:
            text = _("Closed or rated tickets cannot be updated by non-agents")
            frappe.throw(text, frappe.PermissionError)

    def prevent_customer_edits(self):
        """restrict customer from changing ticket values post submission of ticket."""
        if self.is_new() or is_agent():
            return

        # custom flag created to allow insertion in special cases
        if self.flags.get("ignore_customer_edit_guard"):
            return
        editable = self.customer_writable_after_create()
        # the framework's reset runs next and would revert what the template opens
        self.flags.ignore_permlevel_for_fields = list(editable)
        # a customer is never sent what it cannot read, so a whole-document save
        # carries those blank; the framework's reset puts them back
        unreadable = TicketFields().unreadable_fields
        changed = [
            df
            for df in self.meta.fields
            if df.fieldtype not in no_value_fields
            and df.fieldname not in editable
            and not (df.fieldname in unreadable and not self.get(df.fieldname))
            and self.has_value_changed(df.fieldname)
        ]
        if not changed:
            return
        writable_levels = self.get_permlevel_access("write")
        not_permitted = [df for df in changed if df.permlevel not in writable_levels]
        message = (
            _("You do not have permission to change {0}")
            if not_permitted
            else _("You cannot change {0} after the ticket is raised")
        )
        labels = ", ".join(
            self.meta.get_translated_label(df.fieldname)
            for df in not_permitted or changed
        )
        frappe.throw(message.format(labels), frappe.PermissionError)

    def customer_writable_after_create(self) -> set[str]:
        """Close, rate, and what the template opens; replies reopen server-side."""
        writable = set(CUSTOMER_ALWAYS_WRITABLE_FIELDS) | {
            row.fieldname
            for row in self.customer_writable_rows()
            if row.editable_after_creation
        }
        # the portal only closes; Resolved is the agent's call and stops the SLA
        if self.status == "Closed" or self.flags.get("customer_reply_reopen"):
            writable.add("status")
        return writable

    def customer_writable_rows(self) -> list[frappe._dict]:
        """Template rows a customer may fill: shown, readable, not server-set."""
        levels = self.get_permlevel_access("read")
        readable = {df.fieldname for df in self.meta.fields if df.permlevel in levels}
        return [
            row
            for row in TicketFields().template_rows
            if row.visible_to != "Agents"
            and row.fieldname in readable
            and row.fieldname not in SERVER_COMPUTED_FIELDS
        ]
