import frappe
from frappe import _
from frappe.model.document import Document
from frappe.permissions import get_doctype_roles
from frappe.query_builder.functions import Coalesce
from pypika.terms import Criterion

from helpdesk.integrations.whatsapp.setup import AGENT_ROLES
from helpdesk.utils import is_admin, is_agent

TICKET = "HD Ticket"
APP_API = "whatsapp.whatsapp.api.messages"
APP_REACT_ENDPOINT = f"{APP_API}.react_to_message"
# checks the ticket's read permission itself before reading through the app
PORTAL_READ_ENDPOINT = "helpdesk.integrations.whatsapp.api.get_messages"


def validate_access() -> None:
    """The whatsapp app's access guard for calls about tickets: agents pass, others may only read a ticket's thread."""
    if not is_ticket_call() or is_agent():
        return
    if frappe.session.user != "Guest" and is_ticket_read():
        return
    frappe.throw(_("Not permitted"), frappe.PermissionError)


def has_permission(
    doc: Document, ptype: str | None = None, user: str | None = None
) -> bool:
    """A ticket's messages follow the ticket; other messages need a role besides Helpdesk's agent roles."""
    if doc.reference_doctype == TICKET and doc.reference_docname:
        return frappe.has_permission(TICKET, "read", doc.reference_docname, user=user)
    return has_other_access(user)


def permission_query(
    user: str | None = None, doctype: str | None = None
) -> Criterion | None:
    """List view twin of has_permission: ticket rows only where the ticket is readable."""
    user = user or frappe.session.user
    if is_admin(user):
        return None
    message = frappe.qb.DocType("WA Message")
    conditions = []
    if frappe.has_permission(TICKET, "read", user=user):
        tickets = frappe.get_list(TICKET, fields=["name"], user=user, run=False)
        conditions.append(
            (message.reference_doctype == TICKET)
            & message.reference_docname.isin(tickets)
        )
    if has_other_access(user):
        conditions.append(Coalesce(message.reference_doctype, "") != TICKET)
    # an empty criterion would lift the restriction, so no access matches no rows
    return Criterion.any(conditions) if conditions else message.name.isnull()


def has_other_access(user: str | None = None) -> bool:
    """True when a role other than Helpdesk's agent roles lets the user read WA Messages, as another app's would."""
    roles = set(get_doctype_roles("WA Message")) - set(AGENT_ROLES)
    return bool(roles & set(frappe.get_roles(user)))


def is_ticket_call() -> bool:
    """True when the request reads, sends or reacts on a ticket's conversation."""
    form = frappe.form_dict
    if form.cmd == PORTAL_READ_ENDPOINT or form.get("reference_doctype") == TICKET:
        return True
    if form.cmd == APP_REACT_ENDPOINT:
        return (
            frappe.db.get_value("WA Message", form.get("message"), "reference_doctype")
            == TICKET
        )
    return any(reference[:1] == [TICKET] for reference in get_references())


def is_ticket_read() -> bool:
    """Customers read only through Helpdesk's endpoint, which leaves out send errors and internals."""
    return frappe.form_dict.cmd == PORTAL_READ_ENDPOINT


def get_references() -> list[list]:
    """The `[doctype, docname]` pairs a read asks for; malformed input is left to the app to refuse."""
    try:
        references = frappe.parse_json(frappe.form_dict.get("references") or "[]")
    except ValueError:
        return []
    if not isinstance(references, list):
        return []
    return [reference for reference in references if isinstance(reference, list)]
