import frappe

@frappe.whitelist()
def get_user_projects(doctype=None, txt="", searchfield="name", start=0, page_len=20, filters=None):
    return frappe.db.sql("""
        SELECT p.name, p.project_name
        FROM `tabProject` p
        INNER JOIN `tabProject User` pu
            ON pu.parent = p.name
        WHERE pu.user = %(user)s
        AND p.name LIKE %(txt)s
        LIMIT %(start)s, %(page_len)s
    """, {
        "user": frappe.session.user,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })
