import frappe

from helpdesk.utils import get_customer, is_agent


# Check if `user` has access to this specific ticket (`doc`). This implements extra
# permission checks which is not possible with standard permission system. This function
# is being called from hooks. `doc` is the ticket to check against
def ticket(doc, user=None):
	return (
		doc.contact == user
		or doc.raised_by == user
		or doc.owner == user
		or is_agent(user)
		or doc.customer in get_customer(user)
	)


# Check if `user` has access to this specific comment (`doc`). This can be done by
# checking if parent doc (ticket) is accessible by `user`.
def comment(doc):
	if doc.comment_type == "Private" and not is_agent():
		return False
	return frappe.get_doc(doc.reference_doctype, doc.reference_name).has_permission()
