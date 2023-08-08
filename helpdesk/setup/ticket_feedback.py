import frappe

OPTIONS = {
	0.2: ["Response did not help", "No resolution provided"],
	0.4: ["Delayed response time", "Adequate help, bit slow"],
	0.6: ["Clear guidance given", "Helpful answers, reasonable wait"],
	0.8: ["Quick and precise solutions", "Prompt, informative support"],
	1.0: ["Exceptional support experience", "Instant, top-notch help"],
}


def create_ticket_feedback_options():
	for rating in OPTIONS:
		for label in OPTIONS[rating]:
			doc = {
				"doctype": "HD Ticket Feedback Option",
				"rating": rating,
				"label": label,
			}
			if not frappe.db.exists(doc):
				frappe.get_doc(doc).insert()
