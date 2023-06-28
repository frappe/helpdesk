# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import importlib
import math

import frappe
from frappe.model.base_document import get_controller
from frappe.query_builder.functions import Count

from .doc import apply_sort
from .qb import get_query


@frappe.whitelist()
def get_list(
	doctype=None,
	fields=None,
	filters=None,
	order_by=None,
	start=0,
	limit=None,
	group_by=None,
	parent=None,
	debug=False,
):
	check_permissions(doctype, parent)

	query = get_query(
		table=doctype,
		fields=fields,
		filters=filters,
		offset=start,
		limit=limit,
		group_by=group_by,
	)

	query = apply_custom_filters(doctype, query)
	query = apply_hook(doctype, query)
	query = apply_sort(doctype, order_by, query)

	if not fields:
		query = apply_custom_select(doctype, query)

	return query.run(as_dict=True, debug=debug)


@frappe.whitelist()
def get_list_meta(
	doctype=None,
	filters=None,
	order_by=None,
	start: int | None = 0,
	limit=None,
	group_by=None,
	parent=None,
	debug=False,
):
	check_permissions(doctype, parent)

	query = get_query(
		table=doctype,
		filters=filters,
		group_by=group_by,
		fields=["name"],
	)

	query = apply_custom_filters(doctype, query)
	query = apply_hook(doctype, query)
	query = apply_sort(doctype, order_by, query)

	total_count = Count("*").as_("total_count")
	query = query.select(total_count)

	res = query.run(as_dict=True, debug=debug)
	total_count = res.pop().total_count
	total_pages = math.ceil(total_count / limit) if limit else 1
	current_page = start // limit + 1 if start and limit else 1
	has_next_page = current_page < total_pages
	has_previous_page = current_page > 1
	start_from = start + 1
	end_at = start + limit

	if end_at > total_count:
		end_at = total_count

	return {
		"total_count": total_count,
		"total_pages": total_pages,
		"current_page": current_page,
		"has_next_page": has_next_page,
		"has_previous_page": has_previous_page,
		"start_from": start_from,
		"end_at": end_at,
	}


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

	if hasattr(controller, "get_list_filters"):
		return_value = controller.get_list_filters(query)
		if return_value is not None:
			query = return_value

	return query


def apply_custom_select(doctype: str, query):
	"""
	Apply custom select logic to query
	"""
	controller = get_controller(doctype)

	if hasattr(controller, "get_list_select"):
		return_value = controller.get_list_select(query)
		if return_value is not None:
			query = return_value

	return query


def apply_hook(doctype: str, query):
	"""
	Apply hooks to query
	"""
	try:
		_module_path = "helpdesk.helpdesk.hooks." + doctype.lower()
		_module = importlib.import_module(_module_path)
		_class = getattr(_module, doctype)
		_function = getattr(_class, "get_list_filters")
		return _function(query)
	except:
		return query
