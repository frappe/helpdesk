# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Pre-install fixes for QCS Support Hub."""

import frappe

# Helpdesk ships HD Ticket.raised_outside_working_hours as a Check field with
# default 'False'. Frappe only accepts '0' or '1', so validate_fields() throws
# the moment anything touches HD Ticket's meta — which our fixture import does.
# The result is that installing this app onto a fresh Helpdesk site always
# fails with:
#   The default value for the Check field "Ticket raised outside working
#   hours" must be either '0' or '1'
ILLEGAL_CHECK_DEFAULTS = (
	("HD Ticket", "raised_outside_working_hours"),
)


def before_install():
	"""Normalise illegal Check defaults before our fixtures import.

	Idempotent and a silent no-op when the field is absent or already legal,
	so it is safe on every install and re-install.
	"""
	normalise_illegal_check_defaults()


def normalise_illegal_check_defaults():
	for doctype, fieldname in ILLEGAL_CHECK_DEFAULTS:
		if not frappe.db.exists("DocType", doctype):
			continue

		current = frappe.db.get_value(
			"DocField", {"parent": doctype, "fieldname": fieldname}, "default"
		)
		if current is None or current in ("0", "1"):
			continue

		# Fix the DocField itself; a Property Setter would be layered on top
		# but the underlying value would still fail validation on the next
		# app that syncs this doctype.
		frappe.db.set_value(
			"DocField",
			{"parent": doctype, "fieldname": fieldname},
			"default",
			"1" if str(current).lower() in ("true", "yes") else "0",
			update_modified=False,
		)
		frappe.clear_cache(doctype=doctype)
