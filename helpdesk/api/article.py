import frappe


@frappe.whitelist()
def search(query):
	min_charecters = 2
	if len(query) < min_charecters:
		return []
	
	queries = query.split(" ")
	queries = [query for query in queries if len(query) >= min_charecters]
	if len(queries) == 0:
		return []
	
	or_filters = []
	
	for i in range(len(queries)):
		or_filters.append(["title", "like", "%{search}%".format(search=queries[i])])

	data = frappe.get_all(
		"HD Article",
		fields=["name", "title"],
		or_filters=or_filters,
		page_length=5,
		) or []

	return data