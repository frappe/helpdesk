import frappe
from frappe import _
from frappe.utils import now_datetime

from helpdesk.integrations.whatsapp.outgoing import (
    get_last_incoming,
    get_reply_window_closes_at,
    send_system_message,
)
from helpdesk.integrations.whatsapp.setup import WHATSAPP_SOURCE, is_whatsapp_installed


class WhatsAppMerge:
    """Merge rules for WhatsApp Tickets: same channel, Business Number and customer, messages moved."""

    def __init__(self, source: str, target: str) -> None:
        self.source = source
        self.target = target
        self.channels = {
            name: frappe.db.get_value("HD Ticket", name, "source") == WHATSAPP_SOURCE
            for name in (source, target)
        }

    @property
    def is_whatsapp(self) -> bool:
        """True when either ticket is a WhatsApp Ticket."""
        return any(self.channels.values())

    def validate(self) -> None:
        """Refuse merges across channels, Business Numbers or customers."""
        if not self.is_whatsapp:
            return
        if not all(self.channels.values()):
            frappe.throw(
                _("A WhatsApp ticket can only be merged with another WhatsApp ticket")
            )
        if is_whatsapp_installed():
            self.validate_conversation()

    def validate_conversation(self) -> None:
        # replies follow the last sender, so a merge across customers would misdeliver
        source, target = get_last_incoming(self.source), get_last_incoming(self.target)
        if (
            not source
            or not target
            or source.whatsapp_account != target.whatsapp_account
        ):
            frappe.throw(
                _(
                    "WhatsApp tickets can only be merged when they share a business number"
                )
            )
        if source.to != target.to:
            frappe.throw(
                _(
                    "WhatsApp tickets can only be merged when they belong to the same customer"
                )
            )

    def merge(self) -> None:
        """Move the source's messages onto the target and tell the customer on WhatsApp."""
        if not is_whatsapp_installed():
            return
        move_messages(self.source, self.target)
        closes_at = get_reply_window_closes_at(get_last_incoming(self.target))
        if closes_at and closes_at > now_datetime():
            # after commit, so a rolled back merge never reaches the customer
            frappe.enqueue(
                "helpdesk.integrations.whatsapp.merge.send_merge_notice",
                source=self.source,
                target=self.target,
                enqueue_after_commit=True,
            )


def send_merge_notice(source: str, target: str) -> None:
    """Tell the customer on WhatsApp that their ticket was merged; a system notice, so SLA is left alone."""
    customer = get_last_incoming(target)
    send_system_message(
        customer.to,
        customer.whatsapp_account,
        reference_doctype="HD Ticket",
        reference_docname=target,
        message=_(
            "Your ticket #{0} has been merged with ticket #{1}. We will continue here."
        ).format(source, target),
    )


def move_messages(source: str, target: str) -> None:
    # moved, not copied: inserting an Outgoing copy would send it to Meta again
    Message = frappe.qb.DocType("WA Message")
    frappe.qb.update(Message).set(Message.reference_docname, target).where(
        (Message.reference_doctype == "HD Ticket")
        & (Message.reference_docname == source)
    ).run()
