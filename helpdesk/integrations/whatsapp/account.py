import frappe
from frappe import _
from frappe.model.document import Document

TICKET_DOCTYPE = "HD Ticket"
TICKET_ACTION = {"append_to": TICKET_DOCTYPE, "trigger_on": "Incoming"}
MAPPING_FIELDS = (
    "message_field",
    "sender_field",
    "sender_name_field",
    "timestamp_field",
)


def validate(doc: Document, method: str | None = None) -> None:
    """An HD Ticket row only marks the account's incoming messages as tickets; Helpdesk fills the ticket itself."""
    for action in doc.get("append_actions", []):
        if action.append_to != TICKET_DOCTYPE:
            continue
        if action.trigger_on != "Incoming" or any(
            action.get(field) for field in MAPPING_FIELDS
        ):
            frappe.throw(
                _(
                    "Row #{0}: an append action to HD Ticket takes Trigger On Incoming and no field mapping, since Helpdesk fills the ticket itself."
                ).format(action.idx),
                title=_("Append action not allowed"),
            )


def creates_tickets(account: str | None) -> bool:
    """Whether the account's incoming messages become tickets: it has an HD Ticket append action."""
    return bool(
        account
        and frappe.db.exists(
            "WA Account Append",
            {
                "parent": account,
                "parenttype": "WA Account",
                "append_to": TICKET_DOCTYPE,
            },
        )
    )


def add_ticket_action(account: str) -> None:
    """Make an account's incoming messages tickets, unless it already does."""
    if creates_tickets(account):
        return
    doc = frappe.get_doc("WA Account", account)
    doc.append("append_actions", TICKET_ACTION)
    doc.save(ignore_permissions=True)
