import frappe


@frappe.whitelist()
def get_many():
	fields = [
		"name",
		"title",
		"is_chart",
		"chart_type",
		"snippet",
	]
	filters = {
		"enabled": True,
	}
	items = frappe.get_list("HD Dashboard Item", fields=fields, filters=filters)

	def m(item):
		exec(item.snippet)
		item["data"] = locals()["res"]
		del item["snippet"]
		return item

	with_data = filter(lambda x: x.data, map(lambda i: m(i), items))
	return with_data
