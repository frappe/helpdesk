"""
HMIS <-> Support Tool integration API.

Implements the contract from the HMIS - Support Tool Integration PRD:
  - create_ticket   : equivalent of POST /api/tickets
  - get_ticket      : equivalent of GET  /api/tickets/{ticket_id}
  - list_tickets    : list all tickets raised by a given reporter (phone/email)

Authentication: standard Frappe API Key + Secret, tied to a dedicated
service user (e.g. hmis-integration@tiberbu.com). Calls must include:
  Authorization: token <api_key>:<api_secret>

Status mapping (internal HD Ticket Status -> external contract):
  Open / In Progress (Open category)        -> "New" / "In Progress"
  Replied (Paused category)                 -> "Replied"
  Resolved / Closed (Resolved category)      -> "Resolved" / "Closed"
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

# Maps our internal HD Ticket Status names to the external contract's
# status vocabulary (New, Replied, In Progress, Resolved, Closed).
_STATUS_MAP = {
    "Open": "New",
    "In Progress": "In Progress",
    "Replied": "Replied",
    "Resolved": "Resolved",
    "Closed": "Closed",
}


SOURCE_BRANDS = {"HMIS": None, "F360": "F360", "P360": "P360", "Admin Central": "Admin Central"}


def _map_status(internal_status: str) -> str:
    return _STATUS_MAP.get(internal_status, internal_status)


def _resolve_facility(facility_name: str):
    """Look up HD Facility by exact name match, case-insensitive."""
    if not facility_name:
        return None
    match = frappe.db.get_value(
        "HD Facility", {"facility_name": facility_name}, "name"
    )
    if match:
        return match
    # Fallback: case-insensitive match
    match = frappe.db.sql(
        "SELECT name FROM `tabHD Facility` WHERE LOWER(facility_name) = LOWER(%s) LIMIT 1",
        (facility_name,),
    )
    return match[0][0] if match else None


def _resolve_ticket_type(category: str):
    """Map/find an HD Ticket Type matching the given category, creating one if needed."""
    if not category:
        return None
    if frappe.db.exists("HD Ticket Type", category):
        return category
    # Create it on the fly so future HMIS categories aren't silently dropped —
    # mirrors how "Report"/"Registration" types were added earlier.
    frappe.get_doc({"doctype": "HD Ticket Type", "name": category}).insert(
        ignore_permissions=True
    )
    return category


def _serialize_ticket(ticket, external_reference_id=None):
    assigned_to = None
    if ticket.get("_assign"):
        import json
        try:
            assignees = json.loads(ticket._assign)
            if assignees:
                agent_name = frappe.db.get_value("HD Agent", {"user": assignees[0]}, "agent_name")
                assigned_to = f"Implementer: {agent_name}" if agent_name else assignees[0]
        except (ValueError, TypeError):
            pass

    last_reply = frappe.db.get_value(
        "HD Ticket Comment",
        {"reference_ticket": ticket.name},
        "content",
        order_by="creation desc",
    )

    return {
        "ticket_id": ticket.name,
        "external_reference_id": external_reference_id or ticket.get("external_reference_id"),
        "status": _map_status(ticket.status),
        "assigned_to": assigned_to,
        "last_update": str(ticket.modified),
        "last_reply": last_reply,
        "created_at": str(ticket.creation),
    }


@frappe.whitelist(methods=["POST"])
def create_ticket(
    source: str,
    reporter: dict,
    description: str,
    external_reference_id: str = None,
    category: str = None,
    priority: str = None,
    attachments: list = None,
):
    """POST /api/tickets equivalent. See module docstring for contract."""

    if source not in SOURCE_BRANDS:
        frappe.throw(_("Unsupported source: {0}").format(source), frappe.ValidationError)

    if not reporter or not reporter.get("email"):
        frappe.throw(_("reporter.email is required"), frappe.ValidationError)

    if not description:
        frappe.throw(_("description is required"), frappe.ValidationError)

    # --- Idempotency: same source + external_reference_id -> return existing ticket ---
    if external_reference_id:
        existing_name = frappe.db.get_value(
            "HD Ticket",
            {"source": source, "external_reference_id": external_reference_id},
            "name",
        )
        if existing_name:
            existing = frappe.get_doc("HD Ticket", existing_name)
            frappe.local.response.http_status_code = 200
            return _serialize_ticket(existing, external_reference_id)

    facility_name = _resolve_facility((reporter or {}).get("facility"))
    if (reporter or {}).get("facility") and not facility_name:
        frappe.throw(
            _("Facility '{0}' was not found in the system.").format(reporter.get("facility")),
            frappe.ValidationError,
        )

    ticket_type = _resolve_ticket_type(category)

    priority_value = priority if priority in ("Low", "Medium", "High", "Urgent") else "Medium"

    subject = (description or "").strip().splitlines()[0][:140] or _("HMIS Issue")
    if category:
        subject = f"{category}: {subject}"

    doc = frappe.get_doc({
        "doctype": "HD Ticket",
        "subject": subject,
        "description": description,
        "raised_by": reporter.get("email"),
        "facility": facility_name,
        "ticket_type": ticket_type,
        "priority": priority_value,
        "source": source,
        "external_reference_id": external_reference_id,
    })
    _brand = SOURCE_BRANDS.get(source)
    if _brand:
        _b = frappe.db.get_value("HD Brand", _brand, ["default_team", "default_sla"], as_dict=True) or {}
        doc.brand = _brand
        if _b.get("default_team"):
            doc.agent_group = _b["default_team"]
        if _b.get("default_sla"):
            doc.sla = _b["default_sla"]
    doc.insert(ignore_permissions=True)
    frappe.db.commit()

    doc.reload()
    frappe.local.response.http_status_code = 201
    return _serialize_ticket(doc, external_reference_id)


@frappe.whitelist(methods=["GET"])
def get_ticket(ticket_id: str):
    """GET /api/tickets/{ticket_id} equivalent."""
    if not frappe.db.exists("HD Ticket", ticket_id):
        frappe.local.response.http_status_code = 404
        frappe.throw(_("Ticket not found"), frappe.DoesNotExistError)

    ticket = frappe.get_doc("HD Ticket", ticket_id)
    return _serialize_ticket(ticket)


@frappe.whitelist(methods=["GET"])
def list_tickets(email: str = None, phone: str = None):
    """List all tickets raised by a given reporter, identified by email or phone."""
    if not email and not phone:
        frappe.throw(_("Provide email or phone to list tickets"), frappe.ValidationError)

    filters = []
    if email:
        filters.append(["raised_by", "=", email])
    if phone:
        filters.append(["custom_phone", "=", phone])

    or_filters = filters if len(filters) > 1 else None
    single_filter = filters[0] if len(filters) == 1 else None

    tickets = frappe.get_all(
        "HD Ticket",
        filters=[single_filter] if single_filter else [],
        or_filters=or_filters if or_filters else [],
        fields=["name", "status", "creation", "modified", "external_reference_id", "_assign"],
        order_by="creation desc",
    )

    return {
        "tickets": [_serialize_ticket(frappe._dict(t)) for t in tickets]
    }
