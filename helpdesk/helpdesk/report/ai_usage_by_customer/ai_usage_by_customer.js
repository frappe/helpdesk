// Copyright (c) 2026, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt

frappe.query_reports["AI Usage by Customer"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.nowdate(),
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nActive\nCompleted\nFailed\nCancelled",
		},
	],
};
