from frappe import _


def get_data():
	return {
		"fieldname": "service_level_agreement",
		"transactions": [{"label": _("Ticket"), "items": ["Ticket"]}],
	}
