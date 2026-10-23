import frappe
from frappe import _
from frappe.desk.doctype.tag.tag import DocTags

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
        apply_tag(doctype, name, tag["name"], tag.get("color"))
    for label in removed or []:
        DocTags(doctype).remove(name, label)

    added_labels = [label for tag in added or [] if (label := tag["name"].strip())]
    new_labels = [label for label in added_labels if label not in before]
    if new_labels and doctype == "HD Ticket":
        capture_event("ticket_tag_applied")
    return frappe.db.get_value(doctype, name, "_user_tags") or ""


def apply_tag(doctype: str, name: str, label: str, color: str | None = None) -> str:
    """Link a document to a tag that belongs to Helpdesk and Desk."""
    label = label.strip()
    if not label:
        frappe.throw(_("Tag label is required"))
    if "," in label:
        # _user_tags is a comma-separated column, so a comma would split it
        frappe.throw(_("Tag cannot contain commas"))

    DocTags(doctype).add(name, label, app="helpdesk", color=color)
    return label


def parse_tags(user_tags: str | None) -> list[str]:
    return [label.strip() for label in (user_tags or "").split(",") if label.strip()]
