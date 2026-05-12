import frappe


@frappe.whitelist()
def get_one(name):

    doc = frappe.get_doc("HD Ticket", name)

    tasks = frappe.get_all(
        "HD Task",
        filters={"reference_ticket": doc.name},
        fields=[
            "name",
            "title",
            "description",
            "priority",
            "due_date",
            "is_completed",
            "creation",
        ],
        order_by="creation asc",
    )

    data = doc.as_dict()

    data["tasks"] = tasks

    return data
