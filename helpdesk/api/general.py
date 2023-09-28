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

	fd_preset_filter = frappe.qb.DocType("HD Preset Filter")
	preset_filters = list(
		(
			frappe.qb.from_(fd_preset_filter)
			.select(fd_preset_filter.name)
			.where(
				(
					(
						(fd_preset_filter.type == "User")
						& (fd_preset_filter.user == frappe.session.user)
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
		preset_filter_doc = frappe.get_doc("HD Preset Filter", preset_filter[0])
		options[
			"global" if preset_filter_doc.type in ["Global", "System"] else "user"
		].append(preset_filter_doc)
	return options
