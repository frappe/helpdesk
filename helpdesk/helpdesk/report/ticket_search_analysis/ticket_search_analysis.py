# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from helpdesk.api.article import search


def execute(filters: dict | None = None):
    """Return columns and data for the report.

    This is the main entry point for the report. It accepts the filters as a
    dictionary and should return columns and data. It is called by the framework
    every time the report is refreshed or a filter is updated.
    """
    columns = get_columns()
    data = get_data()

    return columns, data


def get_columns() -> list[dict]:
    """Return columns for the report.

    One field definition per column, just like a DocType field definition.
    """
    return [
        {
            "label": _("Subject"),
            "fieldname": "subject",
            "fieldtype": "Data",
        },
        {
            "label": _("Top Result"),
            "fieldname": "top_res",
            "fieldtype": "Text",
        },
        {
            "label": _("Search Score"),
            "fieldname": "score",
            "fieldtype": "Float",
        },
    ]


def get_top_res(search_term: str) -> float:
    """Return the search score for the top result for the search term."""
    res = search(search_term)
    headings = ""
    score = 0
    for item in res:
        headings += item["headings"] or item["subject"]
        headings += "\n"
        score += item["score"]
    return headings, score


def get_data() -> list[list]:
    """Return data for the report.

    The report data is a list of rows, with each row being a list of cell values.
    """
    tickets = frappe.get_all(
        "HD Ticket", {"agent_group": ["like", "%FC%"]}, ["name", "subject"], limit=100
    )
    for ticket in tickets:
        ticket["top_res"], ticket["score"] = get_top_res(ticket["subject"])
    return [
        [ticket["subject"], ticket["top_res"], ticket["score"]] for ticket in tickets
    ]
