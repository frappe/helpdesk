// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.views.calendar["Service Holiday List"] = {
	field_map: {
		"start": "holiday_date",
		"end": "holiday_date",
		"id": "name",
		"title": "description",
		"allDay": "allDay"
	},
	order_by: `from_date`,
	get_events_method: "helpdesk.helpdesk.doctype.holiday_list.holiday_list.get_events",
	filters: [
		{
			'fieldtype': 'Link',
			'fieldname': 'holiday_list',
			'options': 'Service Holiday List',
			'label': __('Service Holiday List')
		}
	]
}
