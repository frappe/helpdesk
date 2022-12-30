# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FDCustomer(Document):
	pass


def get_contact_count(doc, event):
	if len(doc.links) == 0:
		return

	contact_count = frappe.db.count(
		"Dynamic Link",
		{
			"link_doctype": "FD Customer",
			"link_name": doc.links[0].link_name,
			"parenttype": "Contact",
		},
	)
	customer = frappe.get_doc("FD Customer", doc.links[0].link_name)
	customer.contact_count = contact_count

	customer.save()


def get_ticket_count(doc, event):
	if not doc.customer:
		return

	ticket_count = frappe.db.count("Ticket", {"customer": doc.customer})
	customer = frappe.get_doc("FD Customer", doc.customer)
	customer.ticket_count = ticket_count

	customer.save()
