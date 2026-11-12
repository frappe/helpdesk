import frappe
from frappe import _
from frappe.realtime import get_website_room

from helpdesk.integrations.frappe_cloud import dismiss_trial, forget_trial, get_trial
from helpdesk.utils import agent_manager_only, is_agent_manager

BANNERS = {
    "customer_portal_permission": "show_customer_portal_permission_notice",
    "ticket_field_permission": "show_ticket_field_permission_notice",
    "ticket_source": "show_ticket_source_notice",
}
# doctype -> (code fields, filters) that can still mention the dropped field
CODE_DOCTYPES = {
    "HD Form Script": (["script"], {}),
    "Client Script": (["script"], {}),
    "Server Script": (["script"], {}),
    "HD Service Level Agreement": (["condition"], {}),
    "Assignment Rule": (
        ["assign_condition", "unassign_condition", "close_condition"],
        {"document_type": "HD Ticket"},
    ),
    "Notification": (["condition"], {"document_type": "HD Ticket"}),
    "Webhook": (["condition"], {"webhook_doctype": "HD Ticket"}),
    "Custom Field": (
        ["depends_on", "mandatory_depends_on", "read_only_depends_on"],
        {"dt": "HD Ticket"},
    ),
    "Property Setter": (["value"], {"doc_type": "HD Ticket"}),
    "Report": (["query"], {"ref_doctype": "HD Ticket"}),
}
# field naming the doctype a script runs on, which may have its own via_customer_portal
SCRIPT_TARGETS = {"Client Script": "dt", "Server Script": "reference_doctype"}
OLD_FIELD = "via_customer_portal"
# escaped, as `_` is a LIKE wildcard
OLD_FIELD_LIKE = r"%via\_customer\_portal%"


@frappe.whitelist()
def get_banners() -> list[dict]:
    """Sidebar notices as `{"name": ...}`; one that needs data carries it under its own key.
    "customer_portal_permission", "ticket_field_permission", "ticket_source" (with `scripts`)
    or "trial" (with `trial`). Always empty for anyone but agent managers and admins."""
    if not is_agent_manager():
        return []

    banners = [
        {"name": banner}
        for banner, flag in BANNERS.items()
        if frappe.db.get_single_value("HD Settings", flag)
    ]
    for banner in banners:
        if banner["name"] == "ticket_source":
            banner["scripts"] = get_scripts_using_old_source_field()
    trial = get_trial()
    if trial:
        banners.append({"name": "trial", "trial": trial})
    return banners


def get_scripts_using_old_source_field() -> list[dict]:
    """Scripts and conditions the current user can read that still mention
    the dropped `via_customer_portal` field."""
    return [
        {"doctype": doctype, "name": name}
        for doctype, (fields, filters) in CODE_DOCTYPES.items()
        if frappe.db.table_exists(doctype) and frappe.has_permission(doctype, "read")
        for name in find_old_field_uses(doctype, fields, filters)
    ]


def find_old_field_uses(doctype: str, fields: list[str], filters: dict) -> list[str]:
    """Names of `doctype` rows whose `fields` mention the old field, skipping
    scripts on doctypes like ERPNext's Issue where that field still exists."""
    target = SCRIPT_TARGETS.get(doctype)
    rows = frappe.get_all(
        doctype,
        filters=filters,
        or_filters={field: ["like", OLD_FIELD_LIKE] for field in fields},
        fields=["name", target] if target else ["name"],
        order_by="name",
    )
    skip = doctypes_with_old_field() if target else set()
    return [row.name for row in rows if not target or row[target] not in skip]


def doctypes_with_old_field() -> set[str]:
    return set(
        frappe.get_all("DocField", filters={"fieldname": OLD_FIELD}, pluck="parent")
        + frappe.get_all("Custom Field", filters={"fieldname": OLD_FIELD}, pluck="dt")
    )


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def dismiss_banner(banner: str) -> None:
    """Hide a sidebar notice. Agent managers only.
    "trial" hides the trial card for this user for a day; any other banner
    turns that notice off for everyone."""
    if banner == "trial":
        dismiss_trial()
        # Only this user's other tabs need to hide the card
        frappe.publish_realtime(
            "helpdesk:settings-updated", user=frappe.session.user, after_commit=True
        )
        return
    if banner not in BANNERS:
        frappe.throw(_("Unknown banner {0}").format(banner))

    frappe.db.set_single_value("HD Settings", BANNERS[banner], 0)
    frappe.publish_realtime(
        "helpdesk:settings-updated", room=get_website_room(), after_commit=True
    )


@frappe.whitelist(methods=["POST"])
@agent_manager_only
def refresh_trial() -> None:
    """Drop the cached trial, so the next `get_banners` reads it from Frappe Cloud."""
    forget_trial()
