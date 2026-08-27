import frappe
from frappe import _
from frappe.desk.doctype.tag.tag import add_tag, remove_tag

from helpdesk.helpdesk.doctype.hd_ticket_activity.hd_ticket_activity import (
    log_ticket_activity,
)
from helpdesk.utils import agent_only, capture_event

FIRST_TICKET_TAG = "First Ticket"
FIRST_TICKET_TAG_COLOR = "Blue"


@frappe.whitelist()
@agent_only
def update_tags(
    doctype: str,
    name: str,
    added: list[dict] | None = None,
    removed: list[str] | None = None,
) -> str:
    """Apply a batch of tag changes; returns the document's new ``_user_tags``.

    ``added`` is ``[{"name": ..., "color": ...}]``, ``removed`` is a list of tags to be removed e.g. ["Tag1","Tag2"]
    """
    frappe.has_permission(doctype, "write", doc=name, throw=True)

    before = set(parse_tags(frappe.db.get_value(doctype, name, "_user_tags")))
    for tag in added or []:
        apply_tag(doctype, name, tag["name"], tag.get("color") or "Gray")
    for label in removed or []:
        remove_tag(label, doctype, name)

    added_labels = [label for tag in added or [] if (label := tag["name"].strip())]
    new_labels = [label for label in added_labels if label not in before]
    if new_labels and doctype == "HD Ticket":
        capture_event("ticket_tag_applied")
    log_tag_activity(
        doctype,
        name,
        new_labels,
        [label for label in removed or [] if label in before],
    )
    return frappe.db.get_value(doctype, name, "_user_tags") or ""


def apply_tag(doctype: str, name: str, label: str, color: str = "Gray") -> str:
    """Link a tag to a document, creating the helpdesk Tag master if needed.

    ``color`` applies on create, on claim, and to a tag that has no colour
    yet; a tag that already has one keeps it.
    """
    label = label.strip()
    if not label:
        frappe.throw(_("Tag label is required"))
    if "," in label:
        # _user_tags is a comma-separated column, so a comma would split it
        frappe.throw(_("Tag cannot contain commas"))

    existing = frappe.db.get_value("Tag", label, ["app", "color"], as_dict=1)
    if not existing:
        frappe.get_doc(
            {
                "doctype": "Tag",
                "name": label,
                "app": "helpdesk",
                "color": color,
            }
        ).insert(ignore_permissions=True, ignore_if_duplicate=True)
    elif existing.app != "helpdesk" or not existing.color:
        # Desk's tag sidebar mints tags with no app/color; claim them for
        # helpdesk so they list in the picker, and fill a missing colour so
        # they stop rendering gray
        frappe.db.set_value(
            "Tag",
            label,
            {"app": "helpdesk", "color": existing.color or color},
            update_modified=False,
        )

    add_tag(label, doctype, name)
    return label


def log_tag_activity(doctype: str, name: str, added: list[str], removed: list[str]):
    """Log one activity per batch; only tickets have an activity feed."""
    if doctype != "HD Ticket":
        return

    parts = []
    if added:
        parts.append(f"added tag{'s' if len(added) > 1 else ''} {', '.join(added)}")
    if removed:
        parts.append(
            f"removed tag{'s' if len(removed) > 1 else ''} {', '.join(removed)}"
        )
    if parts:
        log_ticket_activity(name, " & ".join(parts))


def parse_tags(user_tags: str | None) -> list[str]:
    return [label.strip() for label in (user_tags or "").split(",") if label.strip()]
