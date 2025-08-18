from typing import Literal

import frappe
from frappe import _

from helpdesk.helpdesk.doctype.hd_settings.hd_settings import HDSettings


def only_for_managers():
    frappe.only_for(["Agent Manager", "System Manager"])


@frappe.whitelist(methods=["GET"])
def get_data(notification: str):
    only_for_managers()

    if notification == "share_feedback":
        send_email_feedback_on_status = frappe.db.get_single_value(
            "HD Settings", "send_email_feedback_on_status"
        )
        enable_email_ticket_feedback = bool(
            frappe.db.get_single_value("HD Settings", "enable_email_ticket_feedback")
        )
        share_feedback_email_content = frappe.db.get_single_value(
            "HD Settings", "feedback_email_content"
        )
        default_share_feedback_email_content = HDSettings.get_default_email_content(
            notification
        )
        return {
            "ticket_status": send_email_feedback_on_status,
            "enabled": enable_email_ticket_feedback,
            "content": default_share_feedback_email_content
            if HDSettings.is_email_content_empty(share_feedback_email_content)
            else share_feedback_email_content,
            "default_content": default_share_feedback_email_content,
        }

    if notification == "acknowledgement":
        send_acknowledgement_email = bool(
            frappe.db.get_single_value("HD Settings", "send_acknowledgement_email")
        )
        acknowledgement_email_content = frappe.db.get_single_value(
            "HD Settings", "acknowledgement_email_content"
        )
        default_acknowledgement_email_content = HDSettings.get_default_email_content(
            notification
        )
        return {
            "enabled": send_acknowledgement_email,
            "content": default_acknowledgement_email_content
            if HDSettings.is_email_content_empty(acknowledgement_email_content)
            else acknowledgement_email_content,
            "default_content": default_acknowledgement_email_content,
        }

    if notification == "reply_to_agents":
        enable_reply_email_to_agent = bool(
            frappe.db.get_single_value("HD Settings", "enable_reply_email_to_agent")
        )
        email_content = frappe.db.get_single_value(
            "HD Settings", "reply_email_to_agent_content"
        )
        default_email_content = HDSettings.get_default_email_content(notification)
        return {
            "enabled": enable_reply_email_to_agent,
            "content": default_email_content
            if HDSettings.is_email_content_empty(email_content)
            else email_content,
            "default_content": default_email_content,
        }

    if notification == "reply_via_agent":
        enable_reply_email_via_agent = bool(
            frappe.db.get_single_value("HD Settings", "enable_reply_email_via_agent")
        )
        email_content = frappe.db.get_single_value(
            "HD Settings", "reply_via_agent_email_content"
        )
        default_email_content = HDSettings.get_default_email_content("reply_via_agent")
        return {
            "enabled": enable_reply_email_via_agent,
            "content": default_email_content
            if HDSettings.is_email_content_empty(email_content)
            else email_content,
            "default_content": default_email_content,
        }

    frappe.throw(_("Invalid notification"))


@frappe.whitelist(methods=["PUT"])
def update_share_feedback(
    ticket_status: Literal["Closed", "Resolved"],
    enabled: bool,
    content: str,
):
    only_for_managers()

    # todo: add input validation

    frappe.db.set_single_value(
        "HD Settings",
        "send_email_feedback_on_status",
        ticket_status,
    )
    frappe.db.set_single_value(
        "HD Settings",
        "enable_email_ticket_feedback",
        int(enabled),
    )
    frappe.db.set_single_value("HD Settings", "feedback_email_content", content)
    return {
        "ticket_status": ticket_status,
        "enabled": enabled,
        "content": content,
    }


@frappe.whitelist(methods=["PUT"])
def update_acknowledgement(enabled: bool, content: str):
    only_for_managers()

    # todo: add input validation

    frappe.db.set_single_value(
        "HD Settings", "send_acknowledgement_email", int(enabled)
    )
    frappe.db.set_single_value("HD Settings", "acknowledgement_email_content", content)
    return {
        "enabled": enabled,
        "content": content,
    }


@frappe.whitelist(methods=["PUT"])
def update_reply_to_agents(enabled: bool, content: str):
    only_for_managers()

    # todo: add input validation

    frappe.db.set_single_value(
        "HD Settings", "enable_reply_email_to_agent", int(enabled)
    )
    frappe.db.set_single_value("HD Settings", "reply_email_to_agent_content", content)
    return {
        "enabled": enabled,
        "content": content,
    }


@frappe.whitelist(methods=["PUT"])
def update_reply_via_agent(enabled: bool, content: str):
    only_for_managers()

    # todo: add input validation

    frappe.db.set_single_value(
        "HD Settings", "enable_reply_email_via_agent", int(enabled)
    )
    frappe.db.set_single_value("HD Settings", "reply_via_agent_email_content", content)
    return {
        "enabled": enabled,
        "content": content,
    }
