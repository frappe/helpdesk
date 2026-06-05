import frappe


def execute():
	"""Add b-tree indexes on HD Ticket for the columns the ticket list filters
	and sorts on most often.

	On large ``tabHD Ticket`` tables the default list queries otherwise fall
	back to full table scans / filesorts:

	- ``ORDER BY modified DESC`` and ``WHERE status = ... ORDER BY modified`` →
	  covered by the ``(status, modified)`` composite.
	- ``WHERE raised_by / owner / contact = ...`` (used by the permission query
	  for portal users and by the agent/customer filters).
	- ``WHERE ticket_type = ...`` (type filter).

	``frappe.db.add_index`` is a no-op when the index already exists, so this
	patch is safe to re-run.
	"""
	if not frappe.db.table_exists("HD Ticket"):
		return

	indexes = [
		(["status", "modified"], "status_modified_index"),
		(["raised_by"], "raised_by_index"),
		(["owner"], "owner_index"),
		(["ticket_type"], "ticket_type_index"),
		(["contact"], "contact_index"),
	]
	for fields, index_name in indexes:
		frappe.db.add_index("HD Ticket", fields, index_name=index_name)
