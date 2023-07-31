import frappe
from frappe.utils.caching import redis_cache
from pypika import Criterion, Order

from helpdesk.utils import check_permissions


@frappe.whitelist()
def delete_items(items, doctype):
	for item in items:
		frappe.delete_doc(doctype, item)


@frappe.whitelist()
@redis_cache()
def get_filterable_fields(doctype):
	check_permissions(doctype, None)
	QBDocField = frappe.qb.DocType("DocField")
	allowed_fieldtypes = [
		"Check",
		"Data",
		"Float",
		"Int",
		"Link",
		"Long Text",
		"Select",
		"Small Text",
		"Text Editor",
		"Text",
	]
	conditions_fieldtype = [QBDocField.fieldtype == i for i in allowed_fieldtypes]
	q = (
		frappe.qb.from_(QBDocField)
		.select(
			QBDocField.fieldname,
			QBDocField.fieldtype,
			QBDocField.label,
			QBDocField.name,
			QBDocField.options,
		)
		.where(QBDocField.parent == doctype)
		.where(QBDocField.hidden == False)
		.where(Criterion.any(conditions_fieldtype))
		.orderby(QBDocField.label, order=Order.asc)
	)
	return q.run(as_dict=True)
