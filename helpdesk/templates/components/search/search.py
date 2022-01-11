import frappe


@frappe.whitelist(allow_guest=True)
def search_text(text):
	return [
		{
			"title": "Result 1",
			"description": "This is a simple result",
			"route": "hc/billing",
		},
		{
			"title": "Result 2",
			"description": "This is a simple result",
			"route": "hc/billing",
		},
		{"title": "Result 3", "route": "hc/billing"},
	]
