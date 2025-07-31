import frappe
from frappe.model.rename_doc import update_document_title


@frappe.whitelist()
def duplicate_holiday_list(docname, new_name):
    doc = frappe.get_doc("HD Service Holiday List", docname)
    doc.name = ""
    doc.holiday_list_name = new_name
    doc.insert()
    return doc


@frappe.whitelist()
def get_holiday_list(docname):
    holiday_list = frappe.get_doc("HD Service Holiday List", docname)
    return holiday_list


@frappe.whitelist()
def update_holiday_list(docname, doc):
    holiday_list = frappe.get_doc("HD Service Holiday List", docname)
    holiday_list.update(doc)
    holiday_list.save()
    if doc["holiday_list_name"] != holiday_list.holiday_list_name:
        updatedName = {
            "doctype": "HD Service Holiday List",
            "docname": docname,
            "enqueue": False,
            "merge": 0,
            "freeze": True,
            "name": doc["holiday_list_name"],
            "freeze_message": "Updating holiday list name",
        }
        update_document_title(**updatedName)
    holiday_list = frappe.get_doc("HD Service Holiday List", doc["holiday_list_name"])
    return holiday_list
