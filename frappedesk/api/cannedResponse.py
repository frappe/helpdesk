import frappe


@frappe.whitelist()
def get_canned_response(title=None):
    if title == None:
        response_list = frappe.db.get_list(
            "Canned Response", fields=["name", "title", "message"]
        )
    else:
        response_list = frappe.db.get_list(
            "Canned Response",
            fields=["name", "title", "message"],
            filters={"title": ["like", "%{}%".format(title)]},
        )

    return response_list
