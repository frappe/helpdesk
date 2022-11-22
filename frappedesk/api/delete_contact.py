import frappe

# @frappe.whitelist()
# def delete_contact(name, doctype):
#     frappe.db.sql(f"delete from `tab{doctype}` where name='{name}'")
#     tickets = frappe.db.sql_list(f"select * from `tabTicket` where contact='{name}'")
#     for ticket in tickets:
#         frappe.db.sql(f"delete from `tabTicket` where name='{ticket}'")


# @frappe.whitelist()
# def delete_bulk_contact(names, doctype):
#     for name in names:
#         print("\n\n name and doctype", name, doctype, "\n\n" )
#         frappe.db.sql(f"delete from `tab{doctype}` where name='{name}'")
#         tickets = frappe.db.sql_list(f"select * from `tabTicket` where contact='{name}'")
#         for ticket in tickets:
#             frappe.db.sql(f"delete from `tabTicket` where name='{ticket}'")


@frappe.whitelist()
def delete_contact(name, doctype):
    frappe.db.sql(f"delete from `tab{doctype}` where name='{name}'")
    tickets = frappe.db.sql_list(f"select * from `tabTicket` where contact='{name}'")
    for ticket in tickets:
        frappe.db.sql(f"delete from `tabTicket` where name='{ticket}'")


@frappe.whitelist()
def delete_bulk_contact(names, doctype):
    for name in names:
        print("\n\n name and doctype", name, doctype, "\n\n" )
        frappe.db.sql(f"delete from `tab{doctype}` where name='{name}'")
        tickets = frappe.db.sql_list(f"select * from `tabTicket` where contact='{name}'")
        for ticket in tickets:
            frappe.db.sql(f"delete from `tabTicket` where name='{ticket}'")