import frappe
from pypika import Order


@frappe.whitelist()
def get_preset_filters(doctype):
	"""
	Args:
	                doctype (_type_): _description_

	Returns:
	                Dict {"user": [], "global": []}: Returns the preset filters for a given doctype
	"""

	options = {"user": [], "global": []}

	fd_preset_filter = frappe.qb.DocType("FD Preset Filter")
	preset_filters = list(
		(
			frappe.qb.from_(fd_preset_filter)
			.select(fd_preset_filter.name)
			.where(
				(
					(
						(fd_preset_filter.type == "User") & (fd_preset_filter.user == frappe.session.user)
					)
					| (fd_preset_filter.type.isin(["Global", "System"]))
				)
				& (fd_preset_filter.reference_doctype == doctype)
			)
			.orderby(fd_preset_filter.type)
			.orderby(fd_preset_filter.modified, order=Order.desc)
		).run()
	)

	for preset_filter in preset_filters:
		preset_filter_doc = frappe.get_doc("FD Preset Filter", preset_filter[0])
		options[
			"global" if preset_filter_doc.type in ["Global", "System"] else "user"
		].append(preset_filter_doc)
	return options


@frappe.whitelist()
def get_field_data_type(doctype, fieldname):
	"""_summary_

	Args:
	                doctype (_type_): Doctype name
	                fieldname (_type_): Fieldname

	Returns:
	                String: Data type of the field
	"""

	# handle special fieldnames
	if fieldname == "name":
		return ["Data"]
	elif fieldname == "_assign":
		return ["Link", "Agent"]
	elif fieldname in ["creation", "modified"]:
		return ["Datetime"]

	field = frappe.get_meta(doctype).get_field(fieldname)

	if not field:
		return "Data"  # for custom fields, TODO: to be handled properly

	return (
		[field.fieldtype] if field.fieldtype != "Link" else [field.fieldtype, field.options]
	)


@frappe.whitelist()
def get_filtered_select_field_options(doctype, fieldname, query, docname=None):
	"""_summary_

	Args:
	                doctype (_type_): Doctype name
	                fieldname (_type_): Fieldname

	Returns:
	                List: Filtered list of options for the field
	"""

	field = frappe.get_meta(doctype).get_field(fieldname)
	if field.fieldtype == "Select":
		# Handling conditional select fields
		if doctype == "Ticket" and docname is not None:
			field_config = frappe.get_doc("Ticket Fields Config")
			for _field in field_config.conditional_select_fields:
				if _field.fieldname == fieldname:
					doc = frappe.get_doc(
						"Ticket", docname
					)  # don't remove this line, its used inside eval(_field.condition)
					print(doc)
					if eval(_field.condition):
						return [
							x
							for x in _field.options.split("\n")
							if query.lower() in x[0 : len(query)].lower()
						]

		return [
			x for x in field.options.split("\n") if query.lower() in x[0 : len(query)].lower()
		]
	else:
		frappe.throw("Select options are only available for Select fields")


@frappe.whitelist()
def save_filter_preset(doctype, is_global, title, filters):
	"""_summary_

	Args:
	                doctype (_type_): Doctype name
	                name (_type_): Name of the preset filter
	                filters (_type_): Filters
	                sort_by (_type_): Sort by
	                sort_order (_type_): Sort order

	Returns:
	                _type_:
	"""

	fd_preset_filter_items = []
	for filter in filters:
		print(f"label : {filter['label']}")
		fd_preset_filter_items.append(
			{
				"doctype": "FD Preset Filter Item",
				"label": filter["label"],
				"fieldname": filter["fieldname"],
				"filter_type": filter["filter_type"],
				"value": filter["value"],
			}
		)

	preset_filter = frappe.get_doc(
		{
			"doctype": "FD Preset Filter",
			"reference_doctype": doctype,
			"type": "Global" if is_global else "User",
			"title": title,
			"filters": fd_preset_filter_items,
		}
	)
	preset_filter.save(ignore_permissions=True)
	return preset_filter.name
