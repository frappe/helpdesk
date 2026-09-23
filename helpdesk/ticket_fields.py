"""Which HD Ticket fields helpdesk's own pages show to customers and to agents.

Permission levels are the real boundary. The Default template's Visible to only
narrows them, and only here: raw framework queries ignore it.
"""

from functools import cached_property

import frappe
from frappe.model import get_permitted_fields

from helpdesk.consts import (
    CORE_TICKET_FIELDS,
    DEFAULT_TICKET_TEMPLATE,
    SERVER_COMPUTED_FIELDS,
)
from helpdesk.utils import is_agent

AGENT_WORKFLOW_FIELDS = {"_assign", "_liked_by", "_user_tags"}


class TicketFields:
    """HD Ticket fields as the session user may see them.

    Permission levels are the base: they decide what the API returns and who
    may write. The Default template's Visible to is a layer on top that only
    narrows what helpdesk pages show; it never widens. Build one per request
    and ask it; nothing else derives the rule.
    """

    def __init__(self):
        self.meta = frappe.get_meta("HD Ticket")

    @cached_property
    def rows(self) -> list[frappe._dict]:
        """The Default template's rows, read once and only when asked for."""
        return frappe.get_all(
            "HD Ticket Template Field",
            filters={
                "parent": DEFAULT_TICKET_TEMPLATE,
                "parenttype": "HD Ticket Template",
            },
            fields=["fieldname", "visible_to", "required", "placeholder", "url_method"],
            order_by="idx",
        )

    @cached_property
    def for_agent(self) -> bool:
        return is_agent()

    @cached_property
    def unreadable(self) -> set[str]:
        """Columns the user's permission levels withhold: the framework's own answer."""
        return set(self.meta.get_valid_columns()) - set(
            get_permitted_fields("HD Ticket")
        )

    @cached_property
    def hidden(self) -> set[str]:
        """Unreadable at the user's levels, or reserved for the other audience."""
        other = "Customers" if self.for_agent else "Agents"
        hidden = self.unreadable | {
            r.fieldname for r in self.rows if r.visible_to == other
        }
        return hidden if self.for_agent else hidden | AGENT_WORKFLOW_FIELDS

    def strip(self, ticket: dict) -> dict:
        """Drop the hidden fields off a ticket dict."""
        for fieldname in self.hidden:
            ticket.pop(fieldname, None)
        return ticket

    @property
    def details(self) -> list[frappe._dict]:
        """The agent details tab: visible template rows as stored, then the core
        fields it does not list. The tab holds the doctype meta itself."""
        rows = [self.row(r) for r in self.rows if r.fieldname not in self.hidden]
        listed = {r.fieldname for r in rows}
        return rows + [
            frappe._dict(fieldname=fieldname)
            for fieldname in CORE_TICKET_FIELDS
            if fieldname not in listed and fieldname not in self.hidden
        ]

    @property
    def form(self) -> list[frappe._dict]:
        """Visible template rows joined with live meta, in template order.
        The new-ticket form and the customer sidebar, which hold no meta."""
        return [
            self.form_field(row)
            for row in self.rows
            if row.fieldname not in self.hidden and self.meta.has_field(row.fieldname)
        ]

    @property
    def customer_template_fields(self) -> list[str]:
        """Template rows not reserved for agents, whoever asks."""
        return [r.fieldname for r in self.rows if r.visible_to != "Agents"]

    @property
    def customer_fillable(self) -> list[str]:
        """Of those, what a customer may submit while raising a ticket:
        not server-computed, and at a level they may read."""
        levels = self.meta.get_permlevel_access("read")
        return [
            fieldname
            for fieldname in self.customer_template_fields
            if fieldname not in SERVER_COMPUTED_FIELDS
            and self.permlevel(fieldname) in levels
        ]

    def permlevel(self, fieldname: str) -> int | None:
        field = self.meta.get_field(fieldname)
        return field.permlevel if field else None

    def row(self, row) -> frappe._dict:
        """The template's own columns, never visible_to."""
        return frappe._dict(
            fieldname=row.fieldname,
            required=row.required,
            placeholder=row.placeholder,
            url_method=row.url_method,
        )

    def form_field(self, row) -> frappe._dict:
        """A template row plus live doctype meta, for pages that hold no meta."""
        field = self.meta.get_field(row.fieldname)
        return frappe._dict(
            **self.row(row),
            label=field.label,
            fieldtype=field.fieldtype,
            options=field.options,
            link_filters=field.link_filters,
            depends_on=field.depends_on,
            mandatory_depends_on=field.mandatory_depends_on,
            read_only_depends_on=field.read_only_depends_on,
        )
