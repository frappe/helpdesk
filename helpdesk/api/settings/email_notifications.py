from typing import Any, Literal

import frappe
from frappe import _
from frappe.utils.jinja import validate_template

from helpdesk.helpdesk.doctype.hd_settings.helpers import (
    get_default_email_content,
    is_email_content_empty,
)


def only_for_managers():
    frappe.only_for(["Agent Manager", "System Manager"])


def get_email_content(content: str, default_content: str) -> str:
    if is_email_content_empty(content):
        return default_content
    return content


def get_share_feedback_data():
    send_email_feedback_on_status = frappe.db.get_single_value(
        "HD Settings", "send_email_feedback_on_status"
    )
    enable_email_ticket_feedback = bool(
        frappe.db.get_single_value("HD Settings", "enable_email_ticket_feedback")
    )
    feedback_email_content = frappe.db.get_single_value(
        "HD Settings", "feedback_email_content"
    )
    default_feedback_email_content = get_default_email_content("share_feedback")
    if send_email_feedback_on_status == "":
        send_email_feedback_on_status = "Closed"
    return {
        "ticket_status": {
            "label": send_email_feedback_on_status,
            "value": send_email_feedback_on_status,
        },
        "enabled": enable_email_ticket_feedback,
        "content": get_email_content(
            feedback_email_content, default_feedback_email_content
        ),
        "default_content": default_feedback_email_content,
    }


def get_acknowledgement_data():
    send_acknowledgement_email = bool(
        frappe.db.get_single_value("HD Settings", "send_acknowledgement_email")
    )
    acknowledgement_email_content = frappe.db.get_single_value(
        "HD Settings", "acknowledgement_email_content"
    )
    default_acknowledgement_email_content = get_default_email_content("acknowledgement")
    return {
        "enabled": send_acknowledgement_email,
        "content": get_email_content(
            acknowledgement_email_content, default_acknowledgement_email_content
        ),
        "default_content": default_acknowledgement_email_content,
    }


def get_reply_to_agents_data():
    enable_reply_email_to_agent = bool(
        frappe.db.get_single_value("HD Settings", "enable_reply_email_to_agent")
    )
    email_content = frappe.db.get_single_value(
        "HD Settings", "reply_email_to_agent_content"
    )
    default_email_content = get_default_email_content("reply_to_agents")
    return {
        "enabled": enable_reply_email_to_agent,
        "content": get_email_content(email_content, default_email_content),
        "default_content": default_email_content,
    }


def get_reply_via_agent_data():
    enable_reply_email_via_agent = bool(
        frappe.db.get_single_value("HD Settings", "enable_reply_email_via_agent")
    )
    email_content = frappe.db.get_single_value(
        "HD Settings", "reply_via_agent_email_content"
    )
    default_email_content = get_default_email_content("reply_via_agent")
    return {
        "enabled": enable_reply_email_via_agent,
        "content": get_email_content(email_content, default_email_content),
        "default_content": default_email_content,
    }


@frappe.whitelist(methods=["GET"])
def get_data(notification: str):
    only_for_managers()

    if notification == "share_feedback":
        return get_share_feedback_data()

    if notification == "acknowledgement":
        return get_acknowledgement_data()

    if notification == "reply_to_agents":
        return get_reply_to_agents_data()

    if notification == "reply_via_agent":
        return get_reply_via_agent_data()

    frappe.throw(_("Invalid notification"))


def set_common_settings(
    enabled_field_name: str, enabled: bool, content_field_name: str, content: str
):
    validate_template(content)
    frappe.db.set_single_value(
        "HD Settings",
        enabled_field_name,
        int(enabled),
    )
    frappe.db.set_single_value("HD Settings", content_field_name, content)
    return {
        "enabled": enabled,
        "content": content,
    }


def merge(*mps: dict[str, Any]):
    res: dict[str, Any] = {}
    for mp in mps:
        for key, value in mp.items():
            res[key] = value
    return res


@frappe.whitelist(methods=["PUT"])
def update_share_feedback(
    ticket_status: dict[Literal["label", "value"], str],
    enabled: bool,
    content: str,
):
    only_for_managers()
    common_settings = set_common_settings(
        "enable_email_ticket_feedback",
        enabled,
        "feedback_email_content",
        content,
    )
    frappe.db.set_single_value(
        "HD Settings",
        "send_email_feedback_on_status",
        ticket_status["value"],
    )
    return merge(common_settings, {"ticket_status": ticket_status})


@frappe.whitelist(methods=["PUT"])
def update_acknowledgement(enabled: bool, content: str):
    only_for_managers()
    return set_common_settings(
        "send_acknowledgement_email",
        enabled,
        "acknowledgement_email_content",
        content,
    )


@frappe.whitelist(methods=["PUT"])
def update_reply_to_agents(enabled: bool, content: str):
    only_for_managers()
    return set_common_settings(
        "enable_reply_email_to_agent",
        enabled,
        "reply_email_to_agent_content",
        content,
    )


@frappe.whitelist(methods=["PUT"])
def update_reply_via_agent(enabled: bool, content: str):
    only_for_managers()
    return set_common_settings(
        "enable_reply_email_via_agent",
        enabled,
        "reply_via_agent_email_content",
        content,
    )
