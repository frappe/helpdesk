import frappe
from frappe.model.rename_doc import update_document_title


@frappe.whitelist()
def get_assignment_rules_list():
    assignment_rules = []
    for docname in frappe.get_all("Assignment Rule"):
        doc = frappe.get_doc("Assignment Rule", docname)
        assignment_rules.append(doc.as_dict())
    return assignment_rules


@frappe.whitelist()
def get_assignment_rule(docname):
    doc = frappe.get_doc("Assignment Rule", docname)
    users = []
    for user in doc.users:
        user = frappe.get_value(
            "User",
            user.user,
            fieldname=["name", "email", "full_name", "user_image"],
            as_dict=True,
        )
        users.append(user)

    return {**doc.as_dict(), "users": users}


@frappe.whitelist()
def save_assignment_rule(doc):
    assignment_rule = frappe.get_doc("Assignment Rule", doc["name"])
    assignment_rule.update(
        {
            **doc,
        }
    )
    assignment_rule.save()

    if assignment_rule.name != doc["assignment_rule_name"]:
        update_document_title(
            **{
                "doctype": "Assignment Rule",
                "docname": doc["name"],
                "enqueue": False,
                "merge": 0,
                "freeze": True,
                "name": doc["assignment_rule_name"],
                "freeze_message": "Updating assignment rule name",
            }
        )
    assignment_rule = frappe.get_doc("Assignment Rule", doc["assignment_rule_name"])

    return assignment_rule
