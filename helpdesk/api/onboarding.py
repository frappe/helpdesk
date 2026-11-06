import frappe
from frappe import _

from helpdesk.consts import (
    ONBOARDING_STEPS,
    SETUP_CHECKLIST_STEPS,
    WELCOME_TICKET_SUBJECT,
)
from helpdesk.utils import capture_event


@frappe.whitelist()
def get_first_ticket(ticket: str | None = None):
    """Get first ticket created except the default ticket"""
    # If a cached ticket ID was passed, verify it still exists
    if ticket and frappe.db.exists("HD Ticket", ticket):
        return ticket

    result = frappe.get_all(
        "HD Ticket",
        filters={
            "subject": ["!=", WELCOME_TICKET_SUBJECT],
            "owner": ["=", frappe.session.user],
        },
        fields=["name"],
        order_by="creation asc",
        limit=1,
    )
    return result[0].name if result else None


@frappe.whitelist()
def get_general_category_id():
    """Get the id of the general category"""
    category = frappe.get_all(
        "HD Article Category",
        filters={"category_name": ["=", "General"]},
        pluck="name",
        order_by="creation asc",
        limit=1,
    )
    return category[0] if category else None


@frappe.whitelist(methods=["GET"])
def get_setup_status() -> dict:
    """What the first-run setup page polls: is a mailbox connected, has it brought in
    a ticket, and is usage data being shared. Includes the mailbox address. System Managers only."""
    frappe.only_for("System Manager")
    email_address = frappe.db.get_value(
        "Email Account", {"enable_incoming": 1}, "email_id"
    )
    return {
        "email_connected": bool(email_address),
        "email_address": email_address,
        # the welcome and agent-made tickets have no email account, only the mailbox does
        "ticket_arrived": bool(
            frappe.get_list(
                "Communication",
                filters={
                    "reference_doctype": "HD Ticket",
                    "sent_or_received": "Received",
                    "email_account": ["is", "set"],
                },
                limit=1,
                pluck="name",
            )
        ),
        "telemetry_enabled": bool(
            frappe.db.get_single_value("System Settings", "enable_telemetry")
        ),
    }


@frappe.whitelist(methods=["POST"])
def complete_setup(skipped: bool = False) -> None:
    """Mark the first-run setup done for the whole site, whether finished or skipped.
    Safe to call again. System Managers only."""
    frappe.only_for("System Manager")
    frappe.db.set_single_value("HD Settings", "setup_complete", 1)
    capture_event("setup_skipped" if skipped else "setup_completed")


@frappe.whitelist(methods=["POST"])
def set_telemetry_enabled(enabled: bool) -> None:
    """Turn usage data sharing on or off for the site. System Managers only."""
    frappe.only_for("System Manager")
    settings = frappe.get_doc("System Settings")
    settings.enable_telemetry = int(enabled)
    settings.save()


@frappe.whitelist(methods=["POST"])
def mark_checklist_steps(steps: list[str]) -> None:
    """Tick sidebar "Getting started" steps for the current admin.
    Rebuilds the stored list in the sidebar's order, so dropped steps cannot block it."""
    frappe.only_for("System Manager")
    unknown = [step for step in steps if step not in SETUP_CHECKLIST_STEPS]
    if unknown:
        frappe.throw(_("Unknown setup step: {0}").format(", ".join(unknown)))

    user = frappe.session.user
    status = frappe.parse_json(
        frappe.db.get_value("User", user, "onboarding_status") or "{}"
    )
    key = "helpdesk_onboarding_status"
    done = {step["name"] for step in status.get(key, []) if step.get("completed")}
    done.update(steps)
    status[key] = [
        {"name": name, "completed": name in done} for name in ONBOARDING_STEPS
    ]
    frappe.db.set_value(
        "User", user, "onboarding_status", frappe.as_json(status), update_modified=False
    )
