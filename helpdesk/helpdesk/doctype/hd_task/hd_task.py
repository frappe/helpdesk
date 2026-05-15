# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.utils import capture_event, get_doc_room, publish_event


class HDTask(Document):

    def after_insert(self):
        self._publish_event("helpdesk:ticket-task", "task_added")

    def on_update(self):
        self._publish_event("helpdesk:ticket-task", "task_updated")

    def after_delete(self):
        self._publish_event("helpdesk:ticket-task", "task_deleted")

    def _publish_event(self, event: str, telemetry_event: str):
        data = {
            "ticket_id": self.reference_ticket,
            "task_id": self.name,
        }
        room = get_doc_room("HD Ticket", self.reference_ticket)
        publish_event(event, room=room, data=data)
        capture_event(telemetry_event)


@frappe.whitelist()
def get_tasks(ticket: str):
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)

    return frappe.get_all(
        "HD Task",
        filters={"reference_ticket": ticket},
        fields=[
            "name",
            "subject",
            "status",
            "priority",
            "task_description",
            "expected_start_date",
            "expected_end_date",
            "creation",
            "owner",
            "modified",
        ],
        order_by="creation asc",
    )


@frappe.whitelist()
def create_task(
    ticket: str,
    subject: str,
    status: str = "Open",
    priority: str = "Medium",
    task_description: str = None,
    expected_start_date: str = None,
    expected_end_date: str = None,
):
    frappe.has_permission("HD Ticket", "write", ticket, throw=True)

    if not subject or not subject.strip():
        frappe.throw(_("Subject is required"))

    if not frappe.db.exists("HD Ticket", ticket):
        frappe.throw(_("Ticket not found"))

    doc = frappe.get_doc(
        {
            "doctype": "HD Task",
            "reference_ticket": ticket,
            "subject": subject,
            "status": status,
            "priority": priority,
            "task_description": task_description,
            "expected_start_date": expected_start_date,
            "expected_end_date": expected_end_date,
        }
    )
    doc.insert(ignore_permissions=True)

    return doc


@frappe.whitelist()
def update_task(
    task: str,
    subject: str = None,
    status: str = None,
    priority: str = None,
    task_description: str = None,
    expected_start_date: str = None,
    expected_end_date: str = None,
):
    if not frappe.db.exists("HD Task", task):
        frappe.throw(_("Task not found"))

    ticket = frappe.db.get_value("HD Task", task, "reference_ticket")
    frappe.has_permission("HD Ticket", "write", ticket, throw=True)

    doc = frappe.get_doc("HD Task", task)

    if subject is not None:
        doc.subject = subject
    if status is not None:
        doc.status = status
    if priority is not None:
        doc.priority = priority
    if task_description is not None:
        doc.task_description = task_description
    if expected_start_date is not None:
        doc.expected_start_date = expected_start_date
    if expected_end_date is not None:
        doc.expected_end_date = expected_end_date

    doc.save(ignore_permissions=True)

    return doc


@frappe.whitelist()
def delete_task(task: str):
    if not frappe.db.exists("HD Task", task):
        frappe.throw(_("Task not found"))

    ticket = frappe.db.get_value("HD Task", task, "reference_ticket")
    frappe.has_permission("HD Ticket", "write", ticket, throw=True)

    frappe.delete_doc("HD Task", task, force=True)

    return True
