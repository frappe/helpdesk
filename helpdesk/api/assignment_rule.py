import frappe


@frappe.whitelist()
def get_assignment_rules_list():
    if not frappe.has_permission("Assignment Rule", "read"):
        frappe.throw(
            frappe._("You do not have permission to access Assignment Rules"),
            frappe.PermissionError,
        )

    assignment_rules = frappe.get_list(
        "Assignment Rule",
        fields=["name", "description", "disabled", "priority"],
        order_by="modified desc",
    )

    parents_with_users = set(
        frappe.get_all(
            "Assignment Rule User",
            filters={"parent": ["in", [r.name for r in assignment_rules]]},
            pluck="parent",
        )
    )

    for rule in assignment_rules:
        rule["users_exists"] = rule.name in parents_with_users

    return assignment_rules
