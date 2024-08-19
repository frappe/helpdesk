import frappe

from helpdesk.search import search as hd_search


@frappe.whitelist()
def search(query: str):
	out = hd_search(query, only_articles=True)
	breakpoint()
	if not out:
		return []
	return out[0].get("items", [])
