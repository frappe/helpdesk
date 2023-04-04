import frappe


old_module = "FrappeDesk"
new_module = "Helpdesk"
doctypes = [
	"Report",
	"Server Script",
	"Web Form",
]


def execute():
	for doctype in doctypes:
		QBTable = frappe.qb.DocType(doctype)

		frappe.qb.update(QBTable).set(QBTable.module, new_module).where(
			QBTable.module == old_module
		).run()
