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

# TODO: the logic for has_website_permission is minimised a little for now, will need to re-check
has_website_permission = {
	"Ticket": "helpdesk.helpdesk.doctype.ticket.ticket.has_website_permission",
}

doc_events = {
	"*": {"validate": "helpdesk.helpdesk.doctype.sla.sla.apply",},
	"Communication": {
		"on_update": [
			"helpdesk.helpdesk.doctype.sla.sla.on_communication_update",
			"helpdesk.helpdesk.doctype.ticket.ticket.set_first_response_time",
		],
		"after_insert": [
			"helpdesk.helpdesk.doctype.ticket.ticket.set_descritption_from_communication",
		],
	},
	"Contact": {
		"on_trash": [
			"helpdesk.helpdesk.doctype.ticket.ticket.update_ticket",
			"helpdesk.helpdesk.doctype.helpdesk_customer.helpdesk_customer.get_contact_count",
		],
		"after_insert": [
			"helpdesk.helpdesk.doctype.helpdesk_customer.helpdesk_customer.get_contact_count"
		],
	},
	"Assignment Rule": {"on_trash": "helpdesk.overrides.on_assignment_rule_trash"},
	"Agent": {"before_insert": "helpdesk.limits.validate_agent_count"},
	"Ticket": {
		"after_insert": "helpdesk.helpdesk.doctype.helpdesk_customer.helpdesk_customer.get_ticket_count",
		"on_trash": "helpdesk.helpdesk.doctype.helpdesk_customer.helpdesk_customer.get_ticket_count",
	},
}

scheduler_events = {
	"daily": [
		"helpdesk.helpdesk.doctype.ticket.ticket.auto_close_tickets",
		"helpdesk.helpdesk.doctype.sla.sla.check_agreement_status",
	],
	"cron": {"* * * * * 0/5": ["helpdesk.overrides.pull_support_emails"]},
}

website_route_rules = [
	# Desk
	{"from_route": "/helpdesk/<path:app_path>", "to_route": "helpdesk"},
	# Customer Portal
	{"from_route": "/support/<path:app_path>", "to_route": "helpdesk"},
]
