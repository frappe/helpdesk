// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ticket Summary"] = {
	filters: [
		{
			fieldname: "based_on",
			label: __("Based On"),
			fieldtype: "Select",
			options: [
				"Contact",
				"Ticket Type",
				"Ticket Priority",
				"Assigned To",
			],
			default: "Contact",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_global_default("year_start_date"),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.defaults.get_global_default("year_end_date"),
			reqd: 1,
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: [
				"",
				{ label: __("Open"), value: "Open" },
				{ label: __("Replied"), value: "Replied" },
				{ label: __("Resolved"), value: "Resolved" },
				{ label: __("Closed"), value: "Closed" },
			],
		},
		{
			fieldname: "priority",
			label: __("Ticket Priority"),
			fieldtype: "Link",
			options: "HD Ticket Priority",
		},
		{
			fieldname: "contact",
			label: __("Contact"),
			fieldtype: "Link",
			options: "Contact",
		},
		{
			fieldname: "assigned_to",
			label: __("Assigned To"),
			fieldtype: "Link",
			options: "User",
		},
	],
}
