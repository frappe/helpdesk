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
		return "Data"
	elif fieldname == "_assign":
		return "Link"
	elif fieldname in ["creation", "modified"]:
		return "Datetime"

	field = frappe.get_meta(doctype).get_field(fieldname)

	if not field:
		return "Data"  # for custom fields, TODO: to be handled properly

	return field.fieldtype
