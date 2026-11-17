import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.permissions import add_permission

WHATSAPP_APP = "whatsapp"
WHATSAPP_SOURCE = "WhatsApp"
AGENT_ROLES = ("Agent", "Agent Manager")
# sends go through the app's endpoints, which insert as Administrator once the ticket checks pass
READ_DOCTYPES = ("WA Message", "WA Template")


def setup_whatsapp(app_name: str | None = None) -> None:
    """Set Helpdesk up for WhatsApp once the whatsapp app is installed, on install and migrate."""
    if not is_whatsapp_installed():
        return
    add_whatsapp_source()
    grant_agent_roles()
    index_whatsapp_messages()


def add_whatsapp_source() -> None:
    """Offer WhatsApp as a ticket source, keeping any options an admin added."""
    field = frappe.get_meta("HD Ticket").get_field("source")
    # a site not yet migrated to ticket sources has no field to extend
    if not field:
        return
    options = (field.options or "").split("\n")
    # standard options a later release adds must not stay hidden behind this setter
    missing = [
        option
        for option in [*get_standard_sources(), WHATSAPP_SOURCE]
        if option not in options
    ]
    if missing:
        set_source_options(options + missing)


def grant_agent_roles() -> None:
    """Let agents read ticket conversations and templates; every WA doctype is System Manager only."""
    for doctype in READ_DOCTYPES:
        for role in AGENT_ROLES:
            if not frappe.db.exists(
                "Custom DocPerm", {"parent": doctype, "role": role}
            ):
                add_permission(doctype, role, 0, "read")


def index_whatsapp_messages() -> None:
    """Index the lookups intake and every ticket page make: message ids and a ticket's thread."""
    frappe.db.add_index("WA Message", ["message_id"], "message_id_index")
    frappe.db.add_index(
        "WA Message",
        ["reference_doctype", "reference_docname(140)"],
        "reference_index",
    )


def before_app_uninstall(app_name: str) -> None:
    """Refuse to uninstall the whatsapp app while tickets still hold its messages."""
    if app_name != WHATSAPP_APP:
        return
    count = frappe.db.count("HD Ticket", {"source": WHATSAPP_SOURCE})
    if count:
        frappe.throw(
            _(
                "Delete the WhatsApp tickets first ({0} left). Uninstalling WhatsApp deletes their messages."
            ).format(count)
        )
    remove_whatsapp_source()


def remove_whatsapp_source() -> None:
    """Stop offering WhatsApp as a ticket source, keeping any other options."""
    field = frappe.get_meta("HD Ticket").get_field("source")
    options = (field.options or "").split("\n") if field else []
    if WHATSAPP_SOURCE not in options:
        return
    options.remove(WHATSAPP_SOURCE)
    if options != get_standard_sources():
        return set_source_options(options)
    # a leftover setter would hide sources a later release adds
    frappe.db.delete(
        "Property Setter",
        {"doc_type": "HD Ticket", "field_name": "source", "property": "options"},
    )
    frappe.clear_cache(doctype="HD Ticket")


def set_source_options(options: list[str]) -> None:
    make_property_setter(
        "HD Ticket",
        "source",
        "options",
        "\n".join(options),
        "Text",
        validate_fields_for_doctype=False,
    )


def get_standard_sources() -> list[str]:
    """The source options hd_ticket.json ships, before any Property Setter."""
    return frappe.db.get_value(
        "DocField", {"parent": "HD Ticket", "fieldname": "source"}, "options"
    ).split("\n")


def is_whatsapp_installed() -> bool:
    """True when the whatsapp app is installed on this site."""
    return WHATSAPP_APP in frappe.get_installed_apps()
