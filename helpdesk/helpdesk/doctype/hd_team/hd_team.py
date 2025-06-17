# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.core.doctype.version.version import get_diff
from frappe.exceptions import DoesNotExistError
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists


class HDTeam(Document):
    @frappe.whitelist()
    def rename_self(self, new_name: str):
        self.rename(new_name)

    def after_insert(self):
        # nosemgrep
        self.create_assignment_rule()
        assignment_rule_doc = frappe.get_doc("Assignment Rule", self.assignment_rule)

        for user in self.users:
            _user = user.get("user")
            if not _user:
                continue
            assignment_rule_doc.append("users", {"user": _user})

        if assignment_rule_doc.disabled and assignment_rule_doc.users:
            assignment_rule_doc.disabled = False
        assignment_rule_doc.save()

    def after_rename(self, olddn, newdn, merge=False):
        # Update the condition for the linked assignment rule
        rule = self.get_assignment_rule()
        rule_doc = frappe.get_doc("Assignment Rule", rule)
        rule_doc.assign_condition = f"status == 'Open' and agent_group == '{newdn}'"
        rule_doc.save(ignore_permissions=True)

    def on_update(self):
        self.update_support_rotations()

    def on_trash(self):
        # Deletes the assignment rule for this group
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
        rule_doc.priority = 1
        rule_doc.disabled = True  # Disable the rule by default, when agents are added to the group, the rule will be enabled

        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            day_doc = frappe.get_doc({"doctype": "Assignment Rule Day", "day": day})
            rule_doc.append("assignment_days", day_doc)

        rule_doc.save(ignore_permissions=True)
        self.assignment_rule = rule_doc.name
        self.save(ignore_permissions=True)

    def get_assignment_rule(self):
        """
        Returns the assignment rule for this group, if not found creates one
        and returns it
        """
        if not self.assignment_rule:
            self.create_assignment_rule()

        return self.assignment_rule

    def update_support_rotations(self):
        """
        Update the support rotations for the hd_agent
        # If agent removed, remove from the support rule of the team
        # If agent added add to the support rule of the team and also, while adding remove from base Support Rotation
        """
        assg_rule_doc = frappe.get_doc("Assignment Rule", self.assignment_rule)
        if not assg_rule_doc:
            return

        previous_doc = self.get_doc_before_save()
        diff = get_diff(previous_doc, self)
        if not diff:
            return

        if not diff.get("removed") and not diff.get("added"):
            return

        for user in diff.get("removed"):
            self.update_assignment_rule_users(user, assg_rule_doc, action="remove")

        for user in diff.get("added"):
            self.update_assignment_rule_users(user, assg_rule_doc)

    def update_assignment_rule_users(self, user, assignment_rule_doc, action="add"):
        _user = user[1].get("user")
        if not user:
            frappe.throw(_("User Not found"))
            return

        if action == "add":
            assignment_rule_doc.append("users", {"user": _user})
            if assignment_rule_doc.disabled:
                assignment_rule_doc.disabled = False
            assignment_rule_doc.save()

            # remove the user from the base assignment rule
            base_assignment_rule = frappe.get_value(
                "HD Settings", "HD Settings", "base_support_rotation"
            )
            base_assignment_rule = frappe.get_doc(
                "Assignment Rule", base_assignment_rule
            )
            user_id = frappe.get_value(
                "Assignment Rule User",
                {"user": _user, "parent": base_assignment_rule.name},
            )
            if user_id:
                frappe.delete_doc("Assignment Rule User", user_id)
        else:
            user_id = frappe.get_value(
                "Assignment Rule User",
                {"user": _user, "parent": assignment_rule_doc.name},
            )
            if not user_id:
                return
            frappe.delete_doc("Assignment Rule User", user_id)

            # disable the assignment rule if there are no users
            total_users_in_assignment_rule = frappe.db.count(
                "Assignment Rule User", {"parent": assignment_rule_doc.name}
            )
            if total_users_in_assignment_rule == 0:
                assignment_rule_doc.disabled = True
                assignment_rule_doc.save()


@frappe.whitelist()
def get_team_members(team: str):
    """
    Returns the team members for the given team name
    """
    members = frappe.get_all("HD Team Member", filters={"parent": team}, pluck="user")
    return members
