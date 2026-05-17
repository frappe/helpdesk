# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.desk.form.assign_to import remove as unassign
from frappe.model.document import Document

from helpdesk.utils import capture_event, get_doc_room, publish_event


class HDTask(Document):
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        title: DF.Data
        description: DF.TextEditor | None
        status: DF.Literal["Backlog", "Todo", "In Progress", "Done", "Canceled"]
        priority: DF.Literal["Low", "Medium", "High"]
        assigned_to: DF.Link | None
        start_date: DF.Date | None
        due_date: DF.Datetime | None
        reference_doctype: DF.Link | None
        reference_docname: DF.DynamicLink | None
        name: DF.Int | None
    # end: auto-generated types

    def after_insert(self):
        self.assign_to_user()
        self._publish_event("helpdesk:ticket-task", "task_added")

    def validate(self):
        if self.is_new() or not self.assigned_to:
            return
        before = self.get_doc_before_save()
        if before and before.assigned_to != self.assigned_to:
            self.unassign_from_previous_user(before.assigned_to)
            self.assign_to_user()

    def on_update(self):
        self._publish_event("helpdesk:ticket-task", "task_updated")

    def after_delete(self):
        self._publish_event("helpdesk:ticket-task", "task_deleted")

    def unassign_from_previous_user(self, user: str | None):
        if user:
            unassign(self.doctype, self.name, user)

    def assign_to_user(self):
        if self.assigned_to:
            assign(
                {
                    "assign_to": [self.assigned_to],
                    "doctype": self.doctype,
                    "name": self.name,
                    "description": self.title or self.description,
                    "AssignedTo": self.assigned_to,
                }
            )

    def _publish_event(self, event: str, telemetry_event: str):
        ticket_id = self.reference_docname
        data = {"ticket_id": ticket_id, "task_id": self.name}
        room = get_doc_room("HD Ticket", ticket_id)
        publish_event(event, room=room, data=data)
        capture_event(telemetry_event)

    @staticmethod
    def default_list_data():
        columns = [
            {"label": "Title", "type": "Data", "key": "title", "width": "16rem"},
            {"label": "Status", "type": "Select", "key": "status", "width": "8rem"},
            {"label": "Priority", "type": "Select", "key": "priority", "width": "8rem"},
            {
                "label": "Due Date",
                "type": "Datetime",
                "key": "due_date",
                "width": "8rem",
            },
            {
                "label": "Assigned To",
                "type": "Link",
                "key": "assigned_to",
                "width": "10rem",
            },
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "8rem",
            },
        ]
        rows = [
            "name",
            "title",
            "description",
            "assigned_to",
            "due_date",
            "start_date",
            "status",
            "priority",
            "reference_doctype",
            "reference_docname",
            "modified",
        ]
        return {"columns": columns, "rows": rows}

    @staticmethod
    def default_kanban_settings():
        return {
            "column_field": "status",
            "title_field": "title",
            "kanban_fields": '["description", "priority", "creation"]',
        }


@frappe.whitelist()
def get_tasks(ticket: str):
    if not ticket or not str(ticket).strip():
        frappe.throw(_("Ticket is required"))
    ticket = str(ticket).strip()
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)

    return frappe.get_all(
        "HD Task",
        filters={
            "reference_doctype": "HD Ticket",
            "reference_docname": ticket,
        },
        fields=[
            "name",
            "title",
            "description",
            "assigned_to",
            "status",
            "priority",
            "start_date",
            "due_date",
            "creation",
            "owner",
            "modified",
        ],
        order_by="creation asc",
    )


@frappe.whitelist()
def create_task(
    ticket: str,
    title: str,
    status: str = "Todo",
    priority: str = "Medium",
    description: str = None,
    assigned_to: str = None,
    start_date: str = None,
    due_date: str = None,
):

    if not ticket or not str(ticket).strip():
        frappe.throw(_("Ticket is required"))

    ticket = str(ticket).strip()

    if not title or not title.strip():
        frappe.throw(_("Title is required"))

    frappe.has_permission("HD Ticket", "write", ticket, throw=True)

    if not frappe.db.get_value("HD Ticket", {"name": ticket}, "name"):
        frappe.throw(_("Ticket {0} not found").format(ticket))

    doc = frappe.get_doc(
        {
            "doctype": "HD Task",
            "reference_doctype": "HD Ticket",
            "reference_docname": ticket,
            "title": title,
            "description": description,
            "status": status,
            "priority": priority,
            "assigned_to": assigned_to,
            "start_date": start_date,
            "due_date": due_date,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


@frappe.whitelist()
def update_task(
    task: str,
    title: str = None,
    status: str = None,
    priority: str = None,
    description: str = None,
    assigned_to: str = None,
    start_date: str = None,
    due_date: str = None,
):
    if not frappe.db.exists("HD Task", task):
        frappe.throw(_("Task not found"))

    ticket = frappe.db.get_value("HD Task", task, "reference_docname")
    frappe.has_permission("HD Ticket", "write", str(ticket), throw=True)

    doc = frappe.get_doc("HD Task", task)

    if title is not None:
        doc.title = title
    if status is not None:
        doc.status = status
    if priority is not None:
        doc.priority = priority
    if description is not None:
        doc.description = description
    if assigned_to is not None:
        doc.assigned_to = assigned_to
    if start_date is not None:
        doc.start_date = start_date
    if due_date is not None:
        doc.due_date = due_date

    doc.save(ignore_permissions=True)
    return doc


@frappe.whitelist()
def delete_task(task: str):
    if not frappe.db.exists("HD Task", task):
        frappe.throw(_("Task not found"))

    ticket = frappe.db.get_value("HD Task", task, "reference_docname")
    frappe.has_permission("HD Ticket", "write", str(ticket), throw=True)

    frappe.delete_doc("HD Task", task, force=True)
    return True
