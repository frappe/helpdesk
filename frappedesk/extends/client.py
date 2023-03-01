# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import importlib

import frappe
from frappe.model.base_document import get_controller

from .qb import get_query


@frappe.whitelist()
def get_list(
	doctype=None,
	fields=None,
	filters=None,
	order_by=None,
	start=0,
	limit=20,
	group_by=None,
	parent=None,
	debug=False,
):
	check_permissions(doctype, parent)

	query = get_query(
		table=doctype,
		fields=fields,
		filters=filters,
		order_by=order_by,
		offset=start,
		limit=limit,
		group_by=group_by,
	)

	query = apply_custom_filters(doctype, query)
	query = apply_hook(doctype, query)

	return query.run(as_dict=True, debug=debug)


def check_permissions(doctype, parent):
	user = frappe.session.user
	permissions = ("select", "read")
	has_select_permission, has_read_permission = [
		frappe.has_permission(doctype, perm, user=user, parent_doctype=parent)
		for perm in permissions
	]

	if not has_select_permission and not has_read_permission:
		frappe.throw(f"Insufficient Permission for {doctype}", frappe.PermissionError)


def apply_custom_filters(doctype: str, query):
	"""
	Apply custom filters to query
	"""
	controller = get_controller(doctype)

	if hasattr(controller, "get_list_query"):
		return_value = controller.get_list_query(query)
		if return_value is not None:
			query = return_value

	return query


def apply_hook(doctype: str, query):
	"""
	Apply hooks to query
	"""
	try:
		_module_path = "frappedesk.frappedesk.hooks." + doctype.lower()
		_module = importlib.import_module(_module_path)
		_class = getattr(_module, doctype)
		_function = getattr(_class, "get_list_query")
		return _function(query)
	except:
		return query
