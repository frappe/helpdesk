from frappe import _


def get_data():
	return {
		"fieldname": "sla",
		"transactions": [{"label": _("Ticket"), "items": ["Ticket"]}],
	}
