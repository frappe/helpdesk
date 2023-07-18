import frappe
from frappe import _

from helpdesk.utils import is_agent


@frappe.whitelist(allow_guest=True)
def get_article(name: str):
	article = frappe.get_doc("HD Article", name).as_dict()

	if not is_agent() and article["status"] != "Published":
		frappe.throw(_("Access denied"), frappe.PermissionError)

	author = frappe.get_cached_doc("User", article["author"])
	sub_category = frappe.get_cached_doc("HD Article Category", article["category"])
	category = frappe.get_cached_doc(
		"HD Article Category", sub_category.parent_category
	)

	return {
		**article,
		"author": author,
		"category": category,
		"sub_category": sub_category,
	}
