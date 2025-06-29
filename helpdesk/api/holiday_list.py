import frappe

@frappe.whitelist()
def duplicate_holiday_list(docname):
    doc = frappe.get_doc("HD Service Holiday List", docname)
    doc.name = ""
    doc.holiday_list_name = f"{doc.holiday_list_name} (Duplicate)"
    doc.insert()
    return "success"


@frappe.whitelist()
def get_holiday_list(docname):
    holiday_list = frappe.get_doc("HD Service Holiday List", docname)
    return holiday_list
    