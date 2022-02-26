app_name = "helpdesk"
app_title = "HelpDesk"
app_publisher = "Frappe Technologies"
app_description = "Customer Service Software"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hello@frappe.io"
app_license = "AGPLv3"

before_install = "helpdesk.setup.install.before_install"
after_install = "helpdesk.setup.install.after_install"

# TODO: the logic for has_website_permission is minimised a little for now, will need to re-check
has_website_permission = {
	"Ticket": "helpdesk.helpdesk.doctype.ticket.ticket.has_website_permission",
}

doc_events = {
	"*": {
		"validate": "helpdesk.helpdesk.doctype.service_level_agreement.service_level_agreement.apply",
	},
	"Communication": {
		"on_update": [
			"helpdesk.helpdesk.doctype.service_level_agreement.service_level_agreement.on_communication_update",
			"helpdesk.helpdesk.doctype.ticket.ticket.set_first_response_time",
		]
	},
	"Contact": {"on_trash": "helpdesk.helpdesk.doctype.ticket.ticket.update_ticket",},
}

scheduler_events = {
	"daily": [
		"helpdesk.helpdesk.doctype.ticket.ticket.auto_close_tickets",
		"helpdesk.helpdesk.doctype.service_level_agreement.service_level_agreement.check_agreement_status",
	]
}

website_route_rules = [
	{"from_route": "/helpdesk/<path:app_path>", "to_route": "helpdesk"},
	{"from_route": "/support/tickets/<path:app_path>", "to_route": "support/tickets"},
]