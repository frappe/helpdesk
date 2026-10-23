"""Which HD Ticket fields helpdesk's own pages show to customers and to agents.

Permission levels are the real boundary. The Default template's Visible to only
narrows what helpdesk pages show: raw framework queries ignore it.
"""

from functools import cached_property

import frappe

from helpdesk.consts import CORE_TICKET_FIELDS, DEFAULT_TICKET_TEMPLATE
from helpdesk.utils import is_agent

AGENT_WORKFLOW_FIELDS = {"_assign", "_liked_by", "_user_tags"}
# only these reach the client; visible_to and editable_after_creation stay on the server
CLIENT_COLUMNS = ("fieldname", "required", "placeholder", "url_method")


class TicketFields:
    """HD Ticket fields the session user may see; write rules live on HDTicket."""

    def __init__(self, template: str = DEFAULT_TICKET_TEMPLATE):
        self.template = template
        self.meta = frappe.get_meta("HD Ticket")

    def strip_hidden_fields(self, ticket: dict) -> dict:
        """Drop the hidden fields off a ticket dict."""
        for fieldname in self.hidden_fields:
            ticket.pop(fieldname, None)
        return ticket

    def get_layout(self) -> list[frappe._dict]:
        """The agent details tab: visible template rows, then missing core fields."""
        # TODO: a flat list for now; grow it into tabs, sections and columns that a
        # layout editor writes back to the template rows, the way CRM Fields Layout does
        template_fieldnames: set[str] = {
            row.fieldname for row in self.visible_template_rows
        }
        core_fields = [
            frappe._dict(fieldname=fieldname)
            for fieldname in CORE_TICKET_FIELDS
            if fieldname not in template_fieldnames
            and fieldname not in self.hidden_fields
        ]
        return [
            self.get_client_field(row) for row in self.visible_template_rows
        ] + core_fields

    def get_form(self) -> list[frappe._dict]:
        """Visible template rows with live meta, for pages that hold no meta."""
        return [
            self.get_form_field(row)
            for row in self.visible_template_rows
            if self.meta.has_field(row.fieldname)
        ]

    def get_form_field(self, row: frappe._dict) -> frappe._dict:
        docfield = self.meta.get_field(row.fieldname)
        return frappe._dict(
            **self.get_client_field(row),
            label=docfield.label,
            fieldtype=docfield.fieldtype,
            options=docfield.options,
            link_filters=docfield.link_filters,
            depends_on=docfield.depends_on,
            mandatory_depends_on=docfield.mandatory_depends_on,
            read_only_depends_on=docfield.read_only_depends_on,
        )

    def get_client_field(self, row: frappe._dict) -> frappe._dict:
        return frappe._dict({column: row[column] for column in CLIENT_COLUMNS})

    @cached_property
    def visible_template_rows(self) -> list[frappe._dict]:
        # customers always raise as themselves, so raised_by is never theirs to edit
        hidden = (
            self.hidden_fields if self.is_agent else self.hidden_fields | {"raised_by"}
        )
        return [row for row in self.template_rows if row.fieldname not in hidden]

    @cached_property
    def hidden_fields(self) -> set[str]:
        """Unreadable fields, plus agent-only and workflow fields for a customer."""
        if self.is_agent:
            return self.unreadable_fields
        agent_only_fields = {
            row.fieldname for row in self.template_rows if row.visible_to == "Agents"
        }
        return self.unreadable_fields | agent_only_fields | AGENT_WORKFLOW_FIELDS

    @cached_property
    def is_agent(self) -> bool:
        return is_agent()

    @cached_property
    def unreadable_fields(self) -> set[str]:
        """Columns the user's permission levels withhold: the framework's own answer."""
        return set(self.meta.get_valid_columns()) - set(
            frappe.model.get_permitted_fields("HD Ticket")
        )

    @cached_property
    def template_rows(self) -> list[frappe._dict]:
        """The template's rows, read once and only when asked for."""
        return frappe.get_all(
            "HD Ticket Template Field",
            filters={
                "parent": self.template,
                "parenttype": "HD Ticket Template",
            },
            fields=[
                "fieldname",
                "visible_to",
                "editable_after_creation",
                "required",
                "placeholder",
                "url_method",
            ],
            order_by="idx",
        )
