import frappe


def after_insert(c, method=None):
	# DocType against which the communication is created. We only want those
	# which related to Helpdesk
	if not c.reference_doctype == "HD Ticket":
		return

	# Skip if doc is not mentioned
	if not c.reference_name:
		return

	frappe.publish_realtime(
		"helpdesk:new-communication",
		{
			"ticket_id": c.reference_name,
		},
	)
