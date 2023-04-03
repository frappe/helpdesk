import frappe
from frappe import _


class PaywallReachedError(frappe.ValidationError):
	pass


def validate_agent_count(doc, method):
	plan = frappe.conf.plan
	count = frappe.db.count("HD Agent")

	if plan == "Starter" and count >= 3:
		frappe.throw(
			_("Only a maximum of 3 agents are allowed as per your plan"), exc=PaywallReachedError
		)
	elif plan == "Essential" and count >= 10:
		frappe.throw(
			_("Only a maximum of 10 agents are allowed as per your plan"),
			exc=PaywallReachedError,
		)
	elif plan == "Custom":
		# TODO: add custom plans here via some api or something.
		pass
