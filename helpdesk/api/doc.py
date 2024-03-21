import frappe
from frappe.utils.caching import redis_cache
from pypika import Criterion
from frappe.model import no_value_fields
from frappe.model.document import get_controller

from helpdesk.utils import check_permissions


@frappe.whitelist()
@redis_cache()
def get_filterable_fields(doctype):
	check_permissions(doctype, None)
	QBDocField = frappe.qb.DocType("DocField")
	QBCustomField = frappe.qb.DocType("Custom Field")
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

	from_doc_fields = (
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
		.where(Criterion.any([QBDocField.fieldtype == i for i in allowed_fieldtypes]))
		.run(as_dict=True)
	)

	from_custom_fields = (
		frappe.qb.from_(QBCustomField)
		.select(
			QBCustomField.fieldname,
			QBCustomField.fieldtype,
			QBCustomField.label,
			QBCustomField.name,
			QBCustomField.options,
		)
		.where(QBCustomField.dt == doctype)
		.where(QBCustomField.hidden == False)
		.where(
			Criterion.any([QBCustomField.fieldtype == i for i in allowed_fieldtypes])
		)
		.run(as_dict=True)
	)

	res = []
	res.extend(from_doc_fields)
	res.extend(from_custom_fields)
	res.extend(
		[{
			"fieldname": "_assign",
			"fieldtype": "Link",
			"label": "Assigned to",
			"name": "_assign",
			"options": "HD Agent",
		},
		{
			"fieldname": "name",
			"fieldtype": "Data",
			"label": "ID",
			"name": "name",
		}]
	)
	return res

@frappe.whitelist()
def get_list_data(
	doctype: str, 
	filters: dict={}, 
	order_by: str="modified desc", 
	page_length=20,
	columns=None,
	rows=None,
):
	is_default = True

	if columns or rows:
		is_default = False
		columns = frappe.parse_json(columns)
		rows = frappe.parse_json(rows)

	if not columns:
		columns = [
			{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		]

	if not rows:
		rows = ["name"]

	# if frappe.db.exists("HD List View Settings", doctype):
	# 	list_view_settings = frappe.get_doc("CRM List View Settings", doctype)
	# 	columns = frappe.parse_json(list_view_settings.columns)
	# 	rows = frappe.parse_json(list_view_settings.rows)
	# 	is_default = False
	# else:
	list = get_controller(doctype)

	if is_default:
		if hasattr(list, "default_list_data"):
			columns = list.default_list_data().get("columns")
			rows = list.default_list_data().get("rows")

	# check if rows has all keys from columns if not add them
	for column in columns:
		if column.get("key") not in rows:
			rows.append(column.get("key"))

	rows.append("name") if "name" not in rows else rows
	data = frappe.get_list(
		doctype,
		fields=rows,
		filters=filters,
		order_by=order_by,
		page_length=page_length,
	) or []

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": field.label,
			"type": field.fieldtype,
			"value": field.fieldname,
			"options": field.options,
		}
		for field in fields
		if field.label and field.fieldname
	]

	std_fields = [
		{"label": "Name", "type": "Data", "value": "name"},
		{"label": "Created On", "type": "Datetime", "value": "creation"},
		{"label": "Last Modified", "type": "Datetime", "value": "modified"},
		{
			"label": "Modified By",
			"type": "Link",
			"value": "modified_by",
			"options": "User",
		},
		{"label": "Assigned To", "type": "Text", "value": "_assign"},
		{"label": "Owner", "type": "Link", "value": "owner", "options": "User"},
	]

	for field in std_fields:
		if field.get('value') not in rows:
			rows.append(field.get('value'))
		if field not in fields:
			fields.append(field)

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"total_count": len(frappe.get_list(doctype, filters=filters)),
		"row_count": len(data),
	}

@frappe.whitelist()
def sort_options(doctype: str):
	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": field.label,
			"value": field.fieldname,
		}
		for field in fields
		if field.label and field.fieldname
	]

	standard_fields = [
		{"label": "Name", "value": "name"},
		{"label": "Created On", "value": "creation"},
		{"label": "Last Modified", "value": "modified"},
		{"label": "Modified By", "value": "modified_by"},
		{"label": "Owner", "value": "owner"},
	]

	for field in standard_fields:
		fields.append(field)

	return fields