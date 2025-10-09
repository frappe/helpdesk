import frappe
from frappe import _

from helpdesk.utils import is_json_valid


def on_assignment_rule_trash(doc, event):
    if not frappe.get_all(
        "Assignment Rule",
        filters={"document_type": "HD Ticket", "name": ["!=", doc.name]},
    ):
        frappe.throw("There should atleast be 1 assignment rule for ticket")


def on_assignment_rule_validate(doc, event):
    if doc.assign_condition_json and not is_json_valid(doc.assign_condition_json):
        frappe.throw(
            _("The Assign Condition json '{0}' is invalid: {1}").format(
                doc.assign_condition_json,
                "Condition format should be like this e.g [['status','==','open']], it's recommended to use portal view to create conditions.",
            )
        )

    if doc.unassign_condition_json and not is_json_valid(doc.unassign_condition_json):
        frappe.throw(
            _("The Unassign Condition json '{0}' is invalid: {1}").format(
                doc.unassign_condition_json,
                "Condition format should be like this e.g [['status','==','open']], it's recommended to use portal view to create conditions.",
            )
        )
