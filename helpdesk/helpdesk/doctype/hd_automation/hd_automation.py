# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document
from frappe.utils.data import validate_json_string

from helpdesk.utils import get_context


class HDAutomation(Document):
    def validate(self) -> None:
        validate_json_string(self.rule)

    def apply(self, doc) -> None:
        rule = json.loads(self.rule)
        if not self.apply_presets(doc, rule):
            return

        rule = rule.get("rule") or []
        self.parse_rule(doc, rule)

    def apply_presets(self, doc, rule) -> bool:
        filter_expression: str = rule.get("event", {}).get("presets", "")
        if not filter_expression:
            return True

        context = get_context(doc)
        if not frappe.safe_eval(filter_expression, None, context):
            return False

        return True

    def parse_rule(self, doc, rule) -> None:
        for r in rule:
            self.apply_actions(doc, r)

    def apply_actions(self, doc, action) -> None:
        expression = action.get("condition", "")
        context = get_context(doc)
        if expression and not frappe.safe_eval(expression, None, context):
            return

        actions = action.get("actions") or []
        for a in actions:
            action_type = a.get("type") or ""
            if not action_type:
                continue
            if action_type == "set":
                self.set_field(doc, a)
            if action_type == "notify":
                frappe.msgprint(a.get("message") or "")
            if action_type == "add_comment":
                pass

    def set_field(self, doc, action) -> None:
        field = action.get("field") or ""
        value = action.get("value") or ""
        if not field:
            return
        doc.set(field, value)


hook_map = {
    "before_save": "On ticket creation",
    "on_update": "On ticket update",
}


def apply_automations(doc, hook) -> None:
    doctype: str = doc.doctype
    if doctype == "HD Automation":
        return

    event = hook_map.get(hook, "")
    if not event:
        return

    if not doc.is_new() and event == "On ticket creation":
        return

    automations: list["str"] = frappe.db.get_all(
        "HD Automation",
        {"enabled": 1, "event_type": event, "dt": doctype},
        pluck="name",
    )
    for a in automations:
        automation_doc = frappe.get_doc("HD Automation", a)
        automation_doc.apply(doc)
