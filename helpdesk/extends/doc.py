from types import FunctionType

import frappe
from frappe.model.document import get_controller
from frappe.query_builder import Order, Query

SORT_OPTIONS_METHOD = "sort_options"
DEFAULT_SORT_FIELD = "modified"
DEFAULT_SORT_DIRECTION = Order.desc


@frappe.whitelist()
def sort_options(doctype: str):
	c = get_controller(doctype)

	if not hasattr(c, SORT_OPTIONS_METHOD):
		return []

	return c.sort_options().keys()


def apply_sort(doctype: str, order_by: str, query: Query):
	controller = get_controller(doctype)
	fallback = query.orderby(DEFAULT_SORT_FIELD, order=DEFAULT_SORT_DIRECTION)

	if not hasattr(controller, SORT_OPTIONS_METHOD):
		return fallback

	action = controller.sort_options().get(order_by)

	if isinstance(action, FunctionType):
		return action(query)

	if isinstance(action, (list, tuple)):
		return query.orderby(action[0], order=action[1])

	if isinstance(action, str):
		return query.orderby(action, order=DEFAULT_SORT_DIRECTION)

	return fallback
