# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.exceptions import DoesNotExistError
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists

from helpdesk.utils import agent_only, capture_event

ASSIGNMENT_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class HDTeam(Document):
    def after_insert(self):
        self.create_assignment_rule()
        self.capture_team_creation_event()

    def on_update(self):
        ar = frappe.get_doc("Assignment Rule", self.assignment_rule)
        self.sync_users(ar)
        ar.disabled = bool(self.disabled)
        ar.save(ignore_permissions=True)

    def on_trash(self):
        if not self.assignment_rule:
            return
        try:
            frappe.delete_doc(
                "Assignment Rule",
                self.assignment_rule,
                ignore_permissions=True,
                force=True,
                ignore_on_trash=True,
            )
            frappe.db.commit()
        except DoesNotExistError:
            frappe.log_error(
                title="Assignment Rule not found",
                message=f"Assignment Rule {self.assignment_rule} not found",
            )

    def after_rename(self, olddn, newdn, merge=False):
        if not self.assignment_rule:
            self.create_assignment_rule()
        ar = frappe.get_doc("Assignment Rule", self.assignment_rule)
        ar.assign_condition, ar.assign_condition_json = self.assign_condition(newdn)
        ar.unassign_condition, ar.unassign_condition_json = self.unassign_condition(
            newdn
        )
        ar.save(ignore_permissions=True)

    def create_assignment_rule(self):
        ar = frappe.new_doc("Assignment Rule")
        ar.name = append_number_if_name_exists(
            "Assignment Rule", f"{self.name} - Support Rotation"
        )
        ar.document_type = "HD Ticket"
        ar.assign_condition, ar.assign_condition_json = self.assign_condition(self.name)
        ar.unassign_condition, ar.unassign_condition_json = self.unassign_condition(
            self.name
        )
        ar.priority = 1
        ar.disabled = bool(self.disabled)

        for day in ASSIGNMENT_DAYS:
            ar.append("assignment_days", {"doctype": "Assignment Rule Day", "day": day})

        self.sync_users(ar)
        ar.save(ignore_permissions=True)
        self.assignment_rule = ar.name
        self.save(ignore_permissions=True)

    def sync_users(self, ar):
        members = [u.user for u in self.users if u.user]

        if ar.get("rule") == "Weighted Distribution":
            existing_weights = {
                row.user: row.weight for row in ar.weighted_users if row.user
            }
            ar.weighted_users = []
            for user in members:
                ar.append(
                    "weighted_users",
                    {"user": user, "weight": existing_weights.get(user, 1)},
                )
        else:
            ar.users = []
            for user in members:
                ar.append("users", {"user": user})

    def capture_team_creation_event(self):
        if self.name not in ["Product Experts", "Billing"]:
            capture_event("team_created")

    def assign_condition(self, team_name: str) -> tuple[str, str]:
        condition = f"status == 'Open' and agent_group == '{team_name}'"
        condition_json = (
            f'[["status","==","Open"],"and",["agent_group","==","{team_name}"]]'
        )
        return condition, condition_json

    def unassign_condition(self, team_name: str) -> tuple[str, str]:
        condition = f"agent_group != '{team_name}'"
        condition_json = f'[["agent_group","!=","{team_name}"]]'
        return condition, condition_json


@frappe.whitelist()
@agent_only
def get_team_members(team: str):
    return frappe.get_all("HD Team Member", filters={"parent": team}, pluck="user")
