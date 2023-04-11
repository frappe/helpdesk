import frappe


BUILTIN_PRIORITIES = {
	"Urgent": 100,
	"High": 200,
	"Medium": 300,
	"Low": 400,
}


def execute():
	for p in BUILTIN_PRIORITIES:
		d = frappe.get_doc("HD Ticket Priority", p)

		if d.integer_value:
			continue

		d.integer_value = BUILTIN_PRIORITIES[p]
		d.save()
