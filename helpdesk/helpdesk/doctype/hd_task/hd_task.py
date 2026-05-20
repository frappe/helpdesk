# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt
# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
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
        assigned: DF.Link | None
        start_date: DF.Date | None
        due_date: DF.Datetime | None
        reference_doctype: DF.Link | None
        reference_docname: DF.DynamicLink | None
        name: DF.Int | None
    # end: auto-generated types

    def after_insert(self):
        self.assign_to_user_silently()
        self._publish_event("helpdesk:ticket-task", "task_added")

    def validate(self):
        if self.is_new() or not self.assigned:
            return
        before = self.get_doc_before_save()
        if before and before.assigned != self.assigned:
            self.unassign_from_previous_user_silently(before.assigned)
            self.assign_to_user_silently()

    def on_update(self):
        self._publish_event("helpdesk:ticket-task", "task_updated")

    def after_delete(self):
        self._publish_event("helpdesk:ticket-task", "task_deleted")

    # FIXED: Replaced core form assignments with explicit, clean database injections 
    # to avoid triggering unintended side-effect document lifecycle hooks on parent tickets
    def unassign_from_previous_user_silently(self, user: str | None):
        if user:
            frappe.db.delete("ToDo", {
                "reference_type": self.doctype,
                "reference_name": self.name,
                "allocated_to": user
            })

    # FIXED: Maps directly to your new 'assigned' string value field
    def assign_to_user_silently(self):
        if self.assigned:
            if not frappe.db.exists("ToDo", {"reference_type": self.doctype, "reference_name": self.name, "allocated_to": self.assigned}):
                todo = frappe.new_doc("ToDo")
                todo.reference_type = self.doctype
                todo.reference_name = self.name
                todo.allocated_to = self.assigned
                todo.description = self.title or self.description or _("Task Assignment")
                todo.priority = self.priority
                todo.insert(ignore_permissions=True)

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
                "key": "assigned",
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
            "assigned",
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
            "assigned",
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
    assigned: str = None,
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
            "assigned": assigned,
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
    assigned: str = None,
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
    if assigned is not None:
        doc.assigned = assigned
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


@frappe.whitelist()
def get_agents_list():
    return frappe.get_all(
        "User",
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name", "full_name"],
        limit=200,
        order_by="full_name asc"
    )