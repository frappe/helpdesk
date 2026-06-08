# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_subcounties_by_county(doctype, txt, searchfield, start, page_len, filters):
	"""
	Filter subcounties based on the selected county.
	Returns (name, subcounty_name) where name is the document ID.
	"""
	county = filters.get('county')

	if not county:
		return []

	# Return name (the document ID) as first field so Frappe can link properly
	return frappe.db.sql("""
		SELECT name, subcounty_name
		FROM `tabHD Subcounty`
		WHERE county = %(county)s
		AND (subcounty_name LIKE %(txt)s OR name LIKE %(txt)s)
		ORDER BY subcounty_name
		LIMIT %(start)s, %(page_len)s
	""", {
		'county': county,
		'txt': f'%{txt}%',
		'start': start,
		'page_len': page_len
	})


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_facilities_by_county_subcounty(doctype, txt, searchfield, start, page_len, filters):
	"""
	Filter facilities based on selected county and optionally subcounty
	"""
	county = filters.get('county')
	subcounty = filters.get('sub_county')

	if not county:
		return []

	conditions = ["county = %(county)s", "status = 'Active'"]
	params = {
		'county': county,
		'txt': f'%{txt}%',
		'start': start,
		'page_len': page_len
	}

	if subcounty:
		conditions.append("subcounty = %(subcounty)s")
		params['subcounty'] = subcounty

	where_clause = " AND ".join(conditions)

	return frappe.db.sql(f"""
		SELECT name, facility_name, facility_type
		FROM `tabHD Facility`
		WHERE {where_clause}
		AND (facility_name LIKE %(txt)s OR name LIKE %(txt)s OR facility_code LIKE %(txt)s)
		ORDER BY facility_name
		LIMIT %(start)s, %(page_len)s
	""", params)
