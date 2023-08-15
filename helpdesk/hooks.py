app_name = "helpdesk"
app_title = "Helpdesk"
app_publisher = "Frappe Technologies"
app_description = "Customer Service Software"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hello@frappe.io"
app_license = "AGPLv3"

before_install = "helpdesk.setup.install.before_install"
after_install = "helpdesk.setup.install.after_install"

website_route_rules = [
	{
		"from_route": "/helpdesk/<path:app_path>",
		"to_route": "helpdesk",
	},
]

scheduler_events = {
	"daily": [
		"helpdesk.helpdesk.doctype.hd_service_level_agreement.hd_service_level_agreement.check_agreement_status",
	],
}

doc_events = {
	"HD Ticket": {
		"validate": "helpdesk.helpdesk.doctype.hd_service_level_agreement.hd_service_level_agreement.apply",
	},
	"Communication": {
		"on_update": [
			"helpdesk.helpdesk.doctype.hd_service_level_agreement.hd_service_level_agreement.on_communication_update",
			"helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.set_first_response_time",
		],
		"after_insert": [
			"helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.set_descritption_from_communication",
			"helpdesk.helpdesk.hooks.communication.after_insert",
		],
	},
	"Contact": {
		"before_insert": "helpdesk.helpdesk.hooks.contact.before_insert",
		"on_trash": [
			"helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.update_ticket",
		],
	},
	"Assignment Rule": {
		"on_trash": "helpdesk.overrides.on_assignment_rule_trash",
	},
}
