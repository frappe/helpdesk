# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document
from frappe.utils.data import validate_json_string

from helpdesk.utils import get_context

HOOK_MAP = {
    "before_save": "On ticket creation",
    "on_update": "On ticket update",
}


class HDAutomation(Document):
    def validate(self) -> None:
        validate_json_string(self.rule)

    def apply(self, doc) -> None:
        rule = json.loads(self.rule)
        if not self.apply_presets(doc, rule):
            return
        print("\n\n", "RAN", self.name, "\n\n")
        rule = rule.get("rule") or []
        self.handle_rule(doc, rule)

    def apply_presets(self, doc, rule) -> bool:
        filter_expression: str = rule.get("event", {}).get("presets", "")
        if not filter_expression:
            return True

        context = get_context(doc)
        if not frappe.safe_eval(filter_expression, None, context):
            return False

        return True

    def handle_rule(self, doc, rule) -> None:
        context = get_context(doc)
        matched = False

        for r in rule:
            rule_type = r.get("type", "")
            actions = r.get("actions") or []

            if rule_type == "if":
                expression = r.get("condition", "")
                if expression and frappe.safe_eval(expression, None, context):
                    self.run_actions(doc, actions)
                    matched = True

            elif rule_type == "else" and not matched:
                self.run_actions(doc, actions)

    def run_actions(self, doc, actions) -> None:
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


def apply_automations(doc, hook) -> None:
    doctype: str = doc.doctype
    if doctype == "HD Automation":
        return

    event = HOOK_MAP.get(hook, "")
    if not event:
        return

    if event == "On ticket creation" and not doc.is_new():
        return

    automations: list["str"] = frappe.db.get_all(
        "HD Automation",
        {"enabled": 1, "event_type": event, "dt": doctype},
        pluck="name",
    )
    for a in automations:
        automation_doc = frappe.get_doc("HD Automation", a)
        automation_doc.apply(doc)
