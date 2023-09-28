# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

import importlib
import math

import frappe
from frappe import _
from frappe.model.base_document import get_controller
from frappe.query_builder.functions import Count
from frappe.utils import get_user_info_for_avatar
from frappe.utils.caching import redis_cache

from helpdesk.utils import check_permissions

from .doc import apply_sort


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
	check_allowed(doctype)
	check_permissions(doctype, parent)

	query = frappe.qb.get_query(
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

	res = query.run(as_dict=True, debug=debug)
	res = transform_avatar(doctype, res)
	res = transform_assign(res)
	return res


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
	check_allowed(doctype)
	check_permissions(doctype, parent)

	query = frappe.qb.get_query(
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
	except Exception:
		return query


def transform_avatar(doctype: str, r):
	m = frappe.get_meta(doctype)
	f = [i for i in m.fields if i.fieldtype == "Link" and i.options == "User"]
	for i in f:
		for j in r:
			if j.get(i.fieldname):
				j[i.fieldname] = get_user_info_for_avatar(j[i.fieldname])
	return r


def transform_assign(r):
	for row in r:
		if assign := row.get("_assign"):
			j = frappe.parse_json(assign)
			if len(j) < 1:
				continue
			row["assignee"] = get_user_info_for_avatar(j.pop())
	return r


@redis_cache()
def check_allowed(doctype: str):
	"""
	Allow only `Helpdesk` doctypes. This is to prevent users from accessing
	other doctypes.

	:param doctype: Doctype name
	"""
	allowed = ["Contact"]
	if not (doctype in allowed or frappe.get_meta(doctype).module == "Helpdesk"):
		text = _("You are not allowed to access {0}").format(doctype)
		frappe.throw(text, frappe.PermissionError)
