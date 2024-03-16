from typing import Literal

import frappe
from frappe import _
from pypika import JoinType

from helpdesk.utils import check_permissions

DOCTYPE_TEMPLATE = "HD Ticket Template"
DOCTYPE_TEMPLATE_FIELD = "HD Ticket Template Field"
DOCTYPE_TICKET = "HD Ticket"


@frappe.whitelist()
def get_one(name: str):
	check_permissions(DOCTYPE_TEMPLATE, None)
	found, about = frappe.get_value(DOCTYPE_TEMPLATE, name, ["name", "about"]) or [None, None]
	if not found:
		return {
			"about": None,
			"fields": []
		}

	fields = []
	fields.extend(get_fields(name, "DocField"))
	fields.extend(get_fields(name, "Custom Field"))
	return {
		"about": about,
		"fields": fields,
	}


def get_fields(template: str, fetch: Literal["Custom Field", "DocField"]):
	QBField = frappe.qb.DocType(DOCTYPE_TEMPLATE_FIELD)
	QBFetch = frappe.qb.DocType(fetch)
	fields = (
		frappe.qb.from_(QBField)
		.select(QBField.star)
		.where(QBField.parent == template)
		.where(QBField.parentfield == "fields")
		.where(QBField.parenttype == DOCTYPE_TEMPLATE)
	)
	where_parent = QBFetch.parent == DOCTYPE_TICKET
	if fetch == "Custom Field":
		where_parent = QBFetch.dt == DOCTYPE_TICKET
	return (
		frappe.qb.from_(fields)
		.select(
			QBFetch.description,
			QBFetch.fieldtype,
			QBFetch.label,
			QBFetch.options,
			fields.fieldname,
			fields.hide_from_customer,
			fields.required,
			fields.url_method,
		)
		.join(QBFetch, JoinType.inner)
		.on(QBFetch.fieldname == fields.fieldname)
		.where(where_parent)
		.run(as_dict=True)
	)
