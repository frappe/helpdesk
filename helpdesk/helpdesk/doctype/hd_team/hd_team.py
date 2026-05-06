# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.exceptions import DoesNotExistError
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists

from helpdesk.utils import agent_only, capture_event


class HDTeam(Document):
    def after_insert(self):
        self.create_assignment_rule()
        self.sync_users_to_assignment_rule()
        self.capture_team_creation_event()

    def capture_team_creation_event(self):
        should_capture = self.name not in ["Product Experts", "Billing"]
        if should_capture:
            capture_event("team_created")

    def after_rename(self, olddn, newdn, merge=False):
        rule = self.get_assignment_rule()
        rule_doc = frappe.get_doc("Assignment Rule", rule)
        rule_doc.assign_condition = f"status == 'Open' and agent_group == '{newdn}'"
        rule_doc.assign_condition_json = (
            f'[["status", "==", "Open"], "and", ["agent_group", "==", "{newdn}"]]'
        )
        rule_doc.unassign_condition = f"agent_group != '{newdn}'"
        rule_doc.unassign_condition_json = f'[["agent_group", "!=", "{newdn}"]]'
        rule_doc.save(ignore_permissions=True)

    def on_update(self):
        self.sync_users_to_assignment_rule()

    def on_trash(self):
        rule = self.assignment_rule
        if not rule:
            return
        try:
            frappe.delete_doc(
                "Assignment Rule",
                rule,
                ignore_permissions=True,
                force=True,
                ignore_on_trash=True,
            )
            frappe.db.commit()
        except DoesNotExistError:
            frappe.log_error(
                title="Assignment Rule not found",
                message=f"Assignment Rule {rule} not found",
            )

    def create_assignment_rule(self):
        """Creates the assignment rule for this group"""
        rule_doc = frappe.new_doc("Assignment Rule")
        rule_doc.name = append_number_if_name_exists(
            "Assignment Rule", f"{self.name} - Support Rotation"
        )
        rule_doc.document_type = "HD Ticket"
        rule_doc.assign_condition = f"status == 'Open' and agent_group == '{self.name}'"
        rule_doc.assign_condition_json = (
            f'[["status","==","Open"],"and",["agent_group","==","{self.name}"]]'
        )
        rule_doc.unassign_condition = f"agent_group != '{self.name}'"
        rule_doc.unassign_condition_json = f'[["agent_group","!=","{self.name}"]]'
        rule_doc.priority = 1
        rule_doc.disabled = True

        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            rule_doc.append(
                "assignment_days", {"doctype": "Assignment Rule Day", "day": day}
            )

        rule_doc.save(ignore_permissions=True)
        self.assignment_rule = rule_doc.name
        self.save(ignore_permissions=True)

    def get_assignment_rule(self):
        if not self.assignment_rule:
            self.create_assignment_rule()
        return self.assignment_rule

    def sync_users_to_assignment_rule(self):
        """
        Syncs HD Team members into the linked AR's `users` and `weighted_users`.
        Skips if already in sync.
        """
        if not self.assignment_rule:
            return

        members = [u.user for u in self.users if u.user]
        member_set = set(members)

        ar_doc = frappe.get_doc("Assignment Rule", self.assignment_rule)

        ar_user_set = {u.user for u in ar_doc.users if u.user}
        ar_weighted_set = {u.user for u in ar_doc.weighted_users if u.user}

        if member_set == ar_user_set and member_set == ar_weighted_set:
            return

        ar_doc.users = []
        for user in members:
            ar_doc.append("users", {"user": user})

        existing_weights = {
            row.user: row.weight for row in ar_doc.weighted_users if row.user
        }
        ar_doc.weighted_users = []
        for user in members:
            ar_doc.append(
                "weighted_users",
                {"user": user, "weight": existing_weights.get(user, 1)},
            )

        ar_doc.disabled = len(members) == 0
        ar_doc.save(ignore_permissions=True)


@frappe.whitelist()
@agent_only
def get_team_members(team: str):
    """
    Returns the team members for the given team name
    """
    members = frappe.get_all("HD Team Member", filters={"parent": team}, pluck="user")
    return members
