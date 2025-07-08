import frappe


def before_insert(doc, method=None):
    if doc.email_id:
        domain = doc.email_id.split("@")[1]
        hd_customers = frappe.get_all(
            "HD Customer", filters={"domain": domain}, fields=["name"]
        )
        if hd_customers:
            doc.append(
                "links",
                {"link_doctype": "HD Customer", "link_name": hd_customers[0].name},
            )
