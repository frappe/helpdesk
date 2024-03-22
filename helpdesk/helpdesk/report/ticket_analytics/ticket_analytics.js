// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ticket Analytics"] = {
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
			default: frappe.datetime.add_days(frappe.datetime.nowdate(), -30),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.nowdate(),
			reqd: 1,
		},
		{
			fieldname: "range",
			label: __("Range"),
			fieldtype: "Select",
			options: [
				{ value: "Weekly", label: __("Weekly") },
				{ value: "Monthly", label: __("Monthly") },
				{ value: "Quarterly", label: __("Quarterly") },
				{ value: "Yearly", label: __("Yearly") },
			],
			default: "Weekly",
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
	after_datatable_render: function (datatable_obj) {
		$(datatable_obj.wrapper).find("input[type=checkbox]")[0].click()
	},

	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true,
			events: {
				onCheckRow: function (data) {
					if (data && data.length) {
						row_name = data[2].content
						row_values = data.slice(3).map(function (column) {
							return column.content
						})
						entry = {
							name: row_name,
							values: row_values,
						}
						let raw_data = frappe.query_report.chart.data
						let new_datasets = raw_data.datasets

						var found = false

						for (var i = 0; i < new_datasets.length; i++) {
							if (new_datasets[i].name == row_name) {
								found = true
								new_datasets.splice(i, 1)
								break
							}
						}

						if (!found) {
							new_datasets.push(entry)
						}

						let new_data = {
							labels: raw_data.labels,
							datasets: new_datasets,
						}

						setTimeout(() => {
							frappe.query_report.chart.update(new_data)
						}, 500)

						setTimeout(() => {
							frappe.query_report.chart.draw(true)
						}, 1000)
						frappe.query_report.raw_chart_data = new_data
					}
				},
			},
		})
	},
}
