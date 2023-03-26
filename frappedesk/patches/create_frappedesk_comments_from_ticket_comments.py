import frappe


def execute():
	all_ticket_comments = frappe.get_all(
		"Comment",
		filters={"comment_type": "Comment", "reference_doctype": "Ticket"},
		fields=["reference_name", "name", "content", "comment_email"],
	)
	for ticket_comment in all_ticket_comments:
		frappe.get_doc(
			{
				"doctype": "HD Ticket Comment",
				"reference_ticket": ticket_comment.reference_name,
				"content": ticket_comment.content,
				"commented_by": ticket_comment.comment_email,
			}
		).insert()
