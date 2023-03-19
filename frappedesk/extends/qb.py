import frappe
from frappe.query_builder import Order

VERSION = frappe.__version__
ORDER_BY_FIELD = "order_by"
DEFAULT_ORDER_FIELD = "modified"
DEFAULT_ORDER_DIR = "desc"


def get_query(*args, **kwargs):
	"""
	Create a query builder instance, with backward compatibility.

	:return: QueryBuilder instance
	"""
	if not VERSION.startswith("15"):
		query = frappe.qb.engine.get_query(*args, **kwargs)

		# Frappe framework version below 15 (as of this) does not support
		# order by for `get_query`. Hence it is needed to manually add it
		# to our query
		table = kwargs.get("table")
		order_by_field, order_by_dir = extract_order_by(kwargs)
		QBTable = frappe.qb.DocType(table)
		query = query.orderby(
			QBTable[order_by_field], order=Order[order_by_dir.lower()]
		)

		return query

	return frappe.qb.get_query(*args, **kwargs)


def extract_order_by(params: dict) -> tuple[str, str]:
	"""
	Extract order by field from parameters. Needed for backward compatibility.

	:param params: Dict of call parameters
	:return: Order by field and order direction
	"""
	order_by = params.get(ORDER_BY_FIELD) or DEFAULT_ORDER_FIELD
	result: list = order_by.split(" ")

	if len(result) < 2:
		return result.pop(), DEFAULT_ORDER_DIR

	return result
