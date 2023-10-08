import frappe


def execute():
	"""
	Move feedback rating and text from `HD Ticket Feedback Option` to `HD Ticket`.
	This is sometimes better because it avoids an extra API call when fetching.
	"""
	for t in frappe.get_all("HD Ticket"):
		t = frappe.get_doc("HD Ticket", t.name)
		if not t.feedback:
			continue
		if not frappe.db.exists("HD Ticket Feedback Option", t.feedback):
			continue
		f = frappe.get_doc("HD Ticket Feedback Option", t.feedback)
		t.db_set("feedback_rating", f.rating)
		t.db_set("feedback_text", f.label)
	frappe.db.commit()
