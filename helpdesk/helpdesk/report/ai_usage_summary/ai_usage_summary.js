// Copyright (c) 2026, Quark Cyber Systems FZC and contributors
// For license information, please see license.txt

frappe.query_reports["AI Usage Summary"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
			reqd: 0,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.nowdate(),
			reqd: 0,
		},
		{
			fieldname: "model",
			label: __("Model"),
			fieldtype: "Data",
			reqd: 0,
		},
	],
};
