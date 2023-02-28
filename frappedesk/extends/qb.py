import frappe
from frappe.query_builder import Order

VERSION = frappe.__version__


def get_query(*args, **kwargs):
	if not VERSION.startswith("15"):
		query = frappe.qb.engine.get_query(*args, **kwargs)

		# Frappe framework version below 15 (as of this) does not support
		# order by for `get_query`. Hence it is needed to manually add it
		# to our query
		table = kwargs.get("table")
		order_field, order_dir = kwargs.get("order_by").split(" ")
		QBTable = frappe.qb.DocType(table)
		query = query.orderby(QBTable[order_field], order=Order[order_dir])

		return query

	return frappe.qb.get_query(*args, **kwargs)
