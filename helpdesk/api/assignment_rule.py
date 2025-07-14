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
    ticket_counts = [
        dict(
            user=d.user,
            count=frappe.db.count(
                "ToDo",
                dict(
                    reference_type="HD Ticket",
                    allocated_to=d.user,
                    status="Open",
                ),
            ),
        )
        for d in doc.users
    ]

    return {**doc.as_dict(), "ticket_counts": ticket_counts}


@frappe.whitelist()
def save_assignment_rule(doc, is_new):
    assignment_rule = None
    if is_new:
        assignment_rule = frappe.client.insert(
            {
                **doc,
                "name": doc["assignment_rule_name"],
                "doctype": "Assignment Rule",
            }
        )
    else:
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
