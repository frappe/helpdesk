# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class HDVisit(Document):
	pass


@frappe.whitelist()
def track_visit(dt: str, dn: str):
	"""
	Log a visit to a document

	:param dt: `DocType`
	:param dn: `DocName`
	"""
	parent = frappe.get_doc(dt, dn)
	if not parent.has_permission():
		err = _("You do not have permission to access {0} {1}").format(dt, dn)
		frappe.throw(err, frappe.PermissionError)
	parent.add_seen()
	values = {
		"reference_doctype": dt,
		"reference_name": dn,
		"user": frappe.session.user,
	}
	exists = frappe.db.get_value("HD Visit", values)
	if exists:
		visit = frappe.get_doc("HD Visit", exists)
	else:
		visit = frappe.new_doc("HD Visit")
		visit.update(values)
	visit.last_visit = now_datetime()
	visit.save()
