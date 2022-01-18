import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_breadcrumbs(route):
    print(route)
    allowed_doctypes = [
        {
            "name": "Article",
            "title_field": "title"
        },
        {
            "name": "Category",
            "title_field": "category_name"
        }
    ]
    
    parents = []
    splits = route.split("/")
    if splits:
        for index, route in enumerate(splits, start=1):
            full_route = "/".join(splits[:index])
            for doctype in allowed_doctypes:
                label = frappe.get_all(doctype["name"], filters=[["route", "=", full_route[1:]]], pluck=doctype["title_field"])
                if label:
                    parents.append({"route": full_route, "label": label[0]})
                    break
        return parents