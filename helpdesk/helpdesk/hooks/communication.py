import frappe

from helpdesk.utils import publish_event


def after_insert(c, method=None):
	# DocType against which the communication is created. We only want those
	# which related to Helpdesk
	if not c.reference_doctype == "HD Ticket":
		return

	# Skip if doc is not mentioned
	if not c.reference_name:
		return

	t = frappe.get_last_doc("HD Ticket", {"name": c.reference_name})
	if not t.description and not t.via_customer_portal:
		t.description = c.content
		t.save()

	event = "helpdesk:new-communication"
	data = {"ticket_id": c.reference_name}
	publish_event(event, data)
