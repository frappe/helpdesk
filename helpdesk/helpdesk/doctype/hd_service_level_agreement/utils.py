import frappe
from frappe.model.document import Document

from helpdesk.utils import get_context

DOCTYPE = "HD Service Level Agreement"


def get_sla(ticket: Document) -> Document:
	"""
	Get Service Level Agreement for `ticket`

	:param doc: Ticket to use
	:return: Applicable SLA
	"""
	filters = {
		"enabled": True,
		"default_sla": False,
	}

	priority = ticket.get("priority")
	if priority:
		filters["priority"] = priority

	sla_list = frappe.get_all(
		DOCTYPE,
		filters=filters,
		fields=["name", "condition"],
	)

	res = None
	for sla in sla_list:
		c = sla.get("condition")
		if not c or (c and frappe.safe_eval(c, None, get_context(ticket))):
			res = sla
			break

	return res or get_default()


def get_default() -> Document:
	"""
	Get default Service Level Agreement

	:return: Default SLA
	"""
	return frappe.get_last_doc(
		DOCTYPE,
		filters={
			"enabled": True,
			"default_sla": True,
		},
	)
