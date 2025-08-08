from typing import Literal

import frappe
from frappe import _

from helpdesk.helpdesk.doctype.hd_settings.hd_settings import HDSettings


@frappe.whitelist(methods=["GET"])
def get_event_data(email_event: str):
    frappe.only_for(["Agent Manager", "System Manager"])
    if email_event == "share_feedback":
        send_email_feedback_on_status = frappe.db.get_single_value(
            "HD Settings", "send_email_feedback_on_status"
        )
        enable_email_ticket_feedback = bool(
            frappe.db.get_single_value("HD Settings", "enable_email_ticket_feedback")
        )
        share_feedback_email_content = frappe.db.get_single_value(
            "HD Settings", "feedback_email_content"
        )
        default_share_feedback_email_content = frappe.db.get_single_value(
            "HD Settings", "default_feedback_email_content"
        )
        return {
            "send_email_feedback_on_status": send_email_feedback_on_status,
            "enable_email_ticket_feedback": enable_email_ticket_feedback,
            "share_feedback_email_content": default_share_feedback_email_content
            if HDSettings.is_email_content_empty(share_feedback_email_content)
            else share_feedback_email_content,
            "default_share_feedback_email_content": default_share_feedback_email_content,
        }

    if email_event == "acknowledgement":
        send_acknowledgement_email = frappe.db.get_single_value(
            "HD Settings", "send_acknowledgement_email"
        )
        acknowledgement_email_content = frappe.db.get_single_value(
            "HD Settings", "acknowledgement_email_content"
        )
        default_acknowledgement_email_content = frappe.db.get_single_value(
            "HD Settings", "default_acknowledgement_email_content"
        )
        return {
            "send_acknowledgement_email": send_acknowledgement_email,
            "acknowledgement_email_content": default_acknowledgement_email_content
            if HDSettings.is_email_content_empty(acknowledgement_email_content)
            else acknowledgement_email_content,
            "default_acknowledgement_email_content": default_acknowledgement_email_content,
        }

    frappe.throw(_("Invalid email event"))


@frappe.whitelist(methods=["PUT"])
def set_feedback_settings(
    send_email_feedback_on_status: Literal["Closed", "Resolved"],
    enable_email_ticket_feedback: bool,
    share_feedback_email_content: str,
):
    frappe.only_for(["Agent Manager", "System Manager"])
    # rendered_template = frappe.render_template(share_feedback_email_content, {
    #     "url": "www.google.com",
    #     "doc": {
    #         "name": "Elton"
    #     }
    # })
    # todo: add input validation
    frappe.db.set_single_value(
        "HD Settings",
        "send_email_feedback_on_status",
        send_email_feedback_on_status,
    )
    frappe.db.set_single_value(
        "HD Settings",
        "enable_email_ticket_feedback",
        int(enable_email_ticket_feedback),
    )
    frappe.db.set_single_value(
        "HD Settings", "feedback_email_content", share_feedback_email_content
    )
    return {
        "send_email_feedback_on_status": send_email_feedback_on_status,
        "enable_email_ticket_feedback": enable_email_ticket_feedback,
        "share_feedback_email_content": share_feedback_email_content,
        # "rendered_template": rendered_template,
    }


@frappe.whitelist(methods=["PUT"])
def set_acknowledgement_settings(
    send_acknowledgement_email: bool, acknowledgement_email_content: str
):
    frappe.db.set_single_value(
        "HD Settings", "send_acknowledgement_email", int(send_acknowledgement_email)
    )
    frappe.db.set_single_value(
        "HD Settings", "acknowledgement_email_content", acknowledgement_email_content
    )
    return {
        "send_acknowledgement_email": send_acknowledgement_email,
        "acknowledgement_email_content": acknowledgement_email_content,
    }
