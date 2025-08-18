import frappe


@frappe.whitelist()
def get_assignment_rules_list():
    assignment_rules = []
    for docname in frappe.get_all("Assignment Rule"):
        doc = frappe.get_value(
            "Assignment Rule",
            docname,
            fieldname=[
                "name",
                "description",
                "disabled",
                "priority",
            ],
            as_dict=True,
        )
        users_exists = bool(
            frappe.db.exists("Assignment Rule User", {"parent": docname.name})
        )
        assignment_rules.append({**doc, "users_exists": users_exists})
    return assignment_rules
