# Copyright (c) 2026, Quark Cyber Systems FZC and contributors
# For license information, please see license.txt

"""Drop the now-unused registration_key field from HDS Support Connection."""

import frappe


def execute():
	doctype = "HDS Support Connection"
	if frappe.db.has_column(doctype, "registration_key"):
		frappe.db.sql(f"ALTER TABLE `tab{doctype}` DROP COLUMN `registration_key`")

	# Clean up Auth table entries for the removed Password field.
	frappe.db.delete(
		"__Auth",
		{"doctype": doctype, "fieldname": "registration_key"},
	)
	frappe.db.commit()
