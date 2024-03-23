# Copyright (c) 2024, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.background_jobs import enqueue
from frappe.core.doctype.communication.email import make
from frappe.model.document import Document


class HDTicketTimeTracking(Document):
	pass

def check_and_alert_paused_time_entries():
    threshold_duration = get_threshold_duration_from_settings()

    # Fetch paused time entries exceeding the threshold
    paused_time_entries = frappe.get_all(
		"HD Ticket Time Tracking", 
		filters={
			"status": "Paused", 
			"modified": ["<", frappe.utils.add_days(frappe.utils.nowdate(), -threshold_duration)]
		}, 
		fields=["name", "agent", "parent"]
	)

    for entry in paused_time_entries:
        agent_email = frappe.db.get_value("User", entry.agent, "email")
        if agent_email:
            send_alert_email(agent_email, entry.name, entry.parent)

def get_threshold_duration_from_settings():
    # Fetch the threshold setting from HD Settings
    threshold = frappe.db.get_single_value("HD Settings", "paused_duration_threshold")
    return threshold if threshold else 1  # Default to 1 day if not set

def send_alert_email(to_email, time_entry_name, ticket_id):
    subject = f"Action Required: Paused Time Entry {time_entry_name}"
    message = f"Your time entry {time_entry_name} for ticket {ticket_id} has been paused for longer than the allowed duration. Please review and take the necessary action."
    
    # Using Frappe's built-in function to create and send the email
    make(content=message, subject=subject, recipients=to_email, send_email=True, use_template=False)

    print(f"Alert sent to {to_email} for time entry {time_entry_name}")  # For logging purposes
