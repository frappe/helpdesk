import json
import re

import frappe

OLD_FIELD = "via_customer_portal"
# bare and negated builder forms; quoted names like doc.get('...') stay for a manual move
OLD_CHECK = re.compile(
    rf"\b(not\s+)?((?:doc\.)?)(?<!['\"]){OLD_FIELD}\b(?!['\"]|\s*[=!<>])"
)


def execute():
    """Backfill ticket source from the dropped via_customer_portal column."""
    backfill_tickets()
    migrate_saved_views()
    migrate_conditions("HD Service Level Agreement", {}, ["condition"])
    migrate_conditions(
        "Assignment Rule",
        {"document_type": "HD Ticket"},
        ["assign_condition", "unassign_condition", "close_condition"],
    )


def backfill_tickets():
    Ticket = frappe.qb.DocType("HD Ticket")
    # the column outlives its field until trim-tables
    if frappe.db.has_column("HD Ticket", OLD_FIELD):
        frappe.qb.update(Ticket).set(Ticket.source, "Portal").where(
            Ticket[OLD_FIELD] == 1
        ).run()
    # adding the column already defaulted every row to Email; this catches any gap
    frappe.qb.update(Ticket).set(Ticket.source, "Email").where(
        Ticket.source.isnull() | (Ticket.source == "")
    ).run()


def migrate_saved_views():
    """A saved view filtering on the dropped field throws when opened."""
    views = frappe.get_all(
        "HD View",
        filters={"dt": "HD Ticket"},
        or_filters={
            "filters": ["like", f"%{OLD_FIELD}%"],
            "order_by": ["like", f"%{OLD_FIELD}%"],
        },
        fields=["name", "filters", "order_by"],
    )
    for view in views:
        filters = to_source_filters(frappe.parse_json(view.filters or "[]"))
        values = {
            "filters": json.dumps(filters),
            # desc keeps Portal first, as it was for the check
            "order_by": (view.order_by or "").replace(OLD_FIELD, "source"),
        }
        frappe.db.set_value("HD View", view.name, values, update_modified=False)


def migrate_conditions(doctype: str, filters: dict, python_fields: list[str]) -> None:
    """Rewrite python conditions and their builder JSON (`<field>_json`)."""
    meta = frappe.get_meta(doctype)
    fields = [f"{f}_json" for f in python_fields] + python_fields
    fields = [f for f in fields if meta.has_field(f)]
    for row in frappe.get_all(doctype, filters=filters, fields=["name", *fields]):
        values = {
            field: to_source_value(field, row[field])
            for field in fields
            if OLD_FIELD in (row[field] or "")
        }
        if values:
            frappe.db.set_value(doctype, row.name, values, update_modified=False)


def to_source_value(field: str, value: str) -> str:
    if field.endswith("_json"):
        try:
            return json.dumps(to_source_filters(json.loads(value)))
        except ValueError:
            return value
    return OLD_CHECK.sub(to_source_expression, value)


def to_source_expression(match: re.Match) -> str:
    # matches what the builder writes for the rewritten JSON condition
    channel = "Email" if match.group(1) else "Portal"
    return f"{match.group(2)}source == '{channel}'"


def to_source_filters(filters: dict | list) -> dict | list:
    if isinstance(filters, dict):
        return dict(to_source_pair(key, value) for key, value in filters.items())
    return [to_source_condition(condition) for condition in filters]


def to_source_pair(key: str, value: object) -> tuple[str, object]:
    if key != OLD_FIELD:
        return key, value
    if isinstance(value, list) and len(value) > 1:
        return "source", [value[0], to_channel(value[1])]
    return "source", to_channel(value)


def to_source_condition(condition: list) -> list:
    # [field, operator, value] or [doctype, field, operator, value]
    if isinstance(condition, list) and condition and isinstance(condition[0], list):
        return to_source_filters(condition)
    if not isinstance(condition, list) or len(condition) < 3:
        return condition
    index = len(condition) - 3
    if condition[index] != OLD_FIELD:
        return condition
    operator, value = condition[index + 1], condition[index + 2]
    return [*condition[:index], "source", operator, to_channel(value)]


def to_channel(value: object) -> str:
    return "Portal" if str(value).lower() in ("1", "true", "yes") else "Email"
