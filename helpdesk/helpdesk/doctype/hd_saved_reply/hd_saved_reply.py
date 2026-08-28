# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.utils import capture_event, get_agents_team

# The single registry of action types, driving validation and apply.
# kind "field" writes ticket_field on the ticket; "assignment" actions are
# mutually exclusive; "tag" values are free text (Tag master is created on
# apply if missing); "comment" is free HTML. target is the value's doctype
# with its "still usable" filters; no_value actions carry no value at all.
ACTIONS: dict[str, dict] = {
    "Set Status": {
        "kind": "field",
        "ticket_field": "status",
        "target": ("HD Ticket Status", {"enabled": 1}),
    },
    "Set Priority": {
        "kind": "field",
        "ticket_field": "priority",
        "target": ("HD Ticket Priority", {"disabled": 0}),
    },
    "Set Team": {
        "kind": "field",
        "ticket_field": "agent_group",
        "target": ("HD Team", {"disabled": 0}),
    },
    "Set Ticket Type": {
        "kind": "field",
        "ticket_field": "ticket_type",
        "target": ("HD Ticket Type", {"disabled": 0}),
    },
    "Assign Agent": {
        "kind": "assignment",
        "target": ("HD Agent", {"is_active": 1}),
    },
    "Assign to Me": {"kind": "assignment", "no_value": True},
    "Add Tag": {"kind": "tag"},
    "Remove Tag": {"kind": "tag"},
    "Add Comment": {"kind": "comment"},
}


class HDSavedReply(Document):
    def validate(self):
        self.validate_actions()

    def validate_actions(self):
        actions = parse_actions(self.actions)
        previous = self.get_doc_before_save()
        unchanged = (
            {(a["action_type"], a["value"]) for a in parse_actions(previous.actions)}
            if previous
            else set()
        )
        seen: set = set()
        assignment_count = 0
        for action in actions:
            action_type = action.get("action_type")
            value = action.get("value") or ""
            # A crafted list/dict here is unhashable and would crash the keys below
            if not isinstance(action_type, str) or not isinstance(value, str):
                frappe.throw(_("Invalid action: {0}").format(action_type))
            key = action_key(action_type, value)
            if key in seen:
                frappe.throw(_("Duplicate action: {0}").format(_(action_type or "")))
            seen.add(key)
            if ACTIONS.get(action_type, {}).get("kind") == "assignment":
                assignment_count += 1
            # A target deleted/disabled later must not block unrelated edits,
            # so untouched actions are not re-validated
            if (action_type, value) not in unchanged:
                validate_action(action_type, value)
        if assignment_count > 1:
            frappe.throw(_("Only one of Assign Agent or Assign to Me is allowed"))
        validate_tag_conflict(actions)
        # Stored as a normalized JSON string; extra keys from clients are dropped
        self.actions = json.dumps(
            [
                {"action_type": a.get("action_type"), "value": a.get("value") or ""}
                for a in actions
            ]
        )

    def after_insert(self):
        capture_event("saved_reply_created")

    def on_update(self) -> None:
        # Counted once, when a reply first gets actions, so edits don't inflate it
        previous = self.get_doc_before_save()
        had_actions = bool(parse_actions(previous.actions)) if previous else False
        if not had_actions and parse_actions(self.actions):
            capture_event("saved_reply_actions_added")


def parse_actions(raw: list | str | None) -> list[dict]:
    """Actions arrive as a JSON string (DB, HTTP) or a list (Python callers)."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError:
        parsed = None
    if not isinstance(parsed, list) or not all(isinstance(a, dict) for a in parsed):
        frappe.throw(_("actions must be a list of objects"))
    return parsed


def validate_tag_conflict(actions: list[dict]) -> None:
    """A tag added and removed by the same reply would silently cancel out."""
    added = {a.get("value") for a in actions if a.get("action_type") == "Add Tag"}
    removed = {a.get("value") for a in actions if a.get("action_type") == "Remove Tag"}
    conflict = sorted(tag for tag in added & removed if tag)
    if conflict:
        frappe.throw(
            _("Tag {0} cannot be both added and removed").format(", ".join(conflict))
        )


def action_key(action_type: str, value: str):
    """Uniqueness key: one entry per set-type action, tag actions repeat per value."""
    return (
        (action_type, value)
        if ACTIONS.get(action_type, {}).get("kind") == "tag"
        else action_type
    )


def is_action_valid(action_type: str | None, value: str | None) -> bool:
    """Whether an action can currently be applied to a ticket.

    Strict type checks: values can arrive from a whitelisted endpoint, where a
    crafted list/dict could slip through frappe.db.exists as a query filter.
    """
    if not isinstance(action_type, str):
        return False
    spec = ACTIONS.get(action_type)
    if not spec:
        return False
    if spec.get("no_value"):
        return True
    if not isinstance(value, str) or not value.strip():
        return False
    if spec["kind"] == "comment":
        return True
    if spec["kind"] == "tag":
        # _user_tags is a comma-separated column, so a comma would split it
        return "," not in value
    doctype, usable_filters = spec["target"]
    return bool(frappe.db.exists(doctype, {"name": value, **usable_filters}))


def validate_action(action_type: str, value: str) -> None:
    if not is_action_valid(action_type, value):
        frappe.throw(
            _("Invalid action {0}: {1} does not exist or is disabled").format(
                _(action_type or ""), value
            )
        )


def has_permission(doc, user=None):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    is_user_admin = "System Manager" in user_roles or "Agent Manager" in user_roles

    if doc.owner == user or is_user_admin:
        return True

    is_team_restriction_applied = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    is_global_scope_disabled = frappe.db.get_single_value(
        "HD Settings", "disable_saved_replies_global_scope"
    )

    scope = doc.scope

    if scope == "Global":
        if not is_global_scope_disabled:
            return True

    elif scope == "Team":
        if not is_team_restriction_applied:
            return True
        else:
            user_team = get_agents_team(user)
            user_team_names = [team["team_name"] for team in user_team]
            if not user_team_names:
                return False

            exists = frappe.db.exists(
                "HD Saved Reply Team",
                {"parent": doc.name, "team": ["in", user_team_names]},
            )
            return bool(exists)

    return False


def permission_query(user):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    is_user_admin = "System Manager" in user_roles or "Agent Manager" in user_roles

    if is_user_admin:
        personal_cond = f"(`tabHD Saved Reply`.scope = 'Personal' AND `tabHD Saved Reply`.owner = {frappe.db.escape(user)})"
        return f"`tabHD Saved Reply`.scope != 'Personal' OR {personal_cond}"

    is_team_restriction_applied = frappe.db.get_single_value(
        "HD Settings", "restrict_tickets_by_agent_group"
    )
    is_global_scope_disabled = frappe.db.get_single_value(
        "HD Settings", "disable_saved_replies_global_scope"
    )

    conditions = []
    if not is_global_scope_disabled:
        conditions.append("`tabHD Saved Reply`.scope = 'Global'")

    personal_cond = f"(`tabHD Saved Reply`.scope = 'Personal' AND `tabHD Saved Reply`.owner = {frappe.db.escape(user)})"

    conditions.append(personal_cond)

    team_cond = "`tabHD Saved Reply`.scope = 'Team'"

    if is_team_restriction_applied:
        user_team = get_agents_team(user)
        user_team_names = [team["team_name"] for team in user_team]
        if user_team_names:
            team_names_escaped = ", ".join(
                f"{frappe.db.escape(team)}" for team in user_team_names
            )
            team_cond = f"(`tabHD Saved Reply`.scope = 'Team' AND `tabHD Saved Reply`.name IN (SELECT parent FROM `tabHD Saved Reply Team` WHERE team IN ({team_names_escaped})))"
        else:
            team_cond = None

    if team_cond:
        conditions.append(team_cond)

    query = " OR ".join(f"({cond})" for cond in conditions)
    return query
