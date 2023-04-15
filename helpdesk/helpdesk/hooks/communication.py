import frappe
from frappe.realtime import get_website_room


def after_insert(c, method=None):
	# DocType against which the communication is created. We only want those
	# which related to Helpdesk
	if not c.reference_doctype == "HD Ticket":
		return

	# Skip if doc is not mentioned
	if not c.reference_name:
		return

	event = "helpdesk:new-communication"
	data = {"ticket_id": c.reference_name}
	room = get_website_room()

	frappe.publish_realtime(event, message=data, room=room, after_commit=True)
