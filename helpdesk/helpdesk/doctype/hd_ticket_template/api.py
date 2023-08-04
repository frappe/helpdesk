import frappe
from frappe import _
from pypika import JoinType

from helpdesk.utils import check_permissions

DOCTYPE_TEMPLATE = "HD Ticket Template"
DOCTYPE_TEMPLATE_FIELD = "HD Ticket Template Field"


@frappe.whitelist()
def get_one(name: str):
	check_permissions(DOCTYPE_TEMPLATE, None)
	found, about = frappe.get_value(DOCTYPE_TEMPLATE, name, ["name", "about"])
	if not found:
		frappe.throw(_("Template not found"), frappe.DoesNotExistError)
	QBField = frappe.qb.DocType(DOCTYPE_TEMPLATE_FIELD)
	QBCustomField = frappe.qb.DocType("Custom Field")
	fields = (
		frappe.qb.from_(QBField)
		.select(QBField.star)
		.where(QBField.parent == name)
		.where(QBField.parentfield == "fields")
		.where(QBField.parenttype == DOCTYPE_TEMPLATE)
	)
	fields = (
		frappe.qb.from_(fields)
		.select(
			QBCustomField.description,
			QBCustomField.fieldtype,
			QBCustomField.label,
			QBCustomField.options,
			fields.fieldname,
			fields.hide_from_customer,
			fields.required,
			fields.url_method,
		)
		.join(QBCustomField, JoinType.inner)
		.on(QBCustomField.fieldname == fields.fieldname)
		.where(QBCustomField.dt == "HD Ticket")
		.run(as_dict=True)
	)

	return {
		"about": about,
		"fields": fields,
	}
