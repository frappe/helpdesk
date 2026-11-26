import frappe
from frappe.utils import add_to_date, now_datetime


def execute():
    since = add_to_date(now_datetime(), days=-180)

    tickets = frappe.db.get_all(
        "HD Ticket",
        filters=[
            ["creation", ">=", since],
            ["agreement_status", "=", "Failed"],
            ["sla", "is", "set"],
        ],
        fields=[
            "name",
            "sla",
            "response_by",
            "first_responded_on",
            "resolution_by",
            "resolution_date",
        ],
    )

    sla_cache = {}

    for ticket in tickets:
        updates = {}

        sla_name = ticket.sla
        if sla_name not in sla_cache:
            sla_cache[sla_name] = frappe.get_doc("HD Service Level Agreement", sla_name)
        sla = sla_cache[sla_name]

        # first_response_failed_by
        if (
            ticket.first_responded_on
            and ticket.response_by
            and ticket.first_responded_on > ticket.response_by
        ):
            updates["first_response_failed_by"] = sla.calc_elapsed_time(
                ticket.response_by, ticket.first_responded_on
            )

        # resolution_failed_by
        if (
            ticket.resolution_date
            and ticket.resolution_by
            and ticket.resolution_date > ticket.resolution_by
        ):
            updates["resolution_failed_by"] = sla.calc_elapsed_time(
                ticket.resolution_by, ticket.resolution_date
            )

        if updates:
            frappe.db.set_value(
                "HD Ticket", ticket.name, updates, update_modified=False
            )
