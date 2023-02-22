app_name = "frappedesk"
app_title = "FrappeDesk"
app_publisher = "Frappe Technologies"
app_description = "Customer Service Software"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hello@frappe.io"
app_license = "AGPLv3"

before_install = "frappedesk.setup.install.before_install"
after_install = "frappedesk.setup.install.after_install"

# TODO: the logic for has_website_permission is minimised a little for now, will need to re-check
has_website_permission = {
	"Ticket": "frappedesk.frappedesk.doctype.ticket.ticket.has_website_permission",
}

override_whitelisted_methods = {
	"frappe.client.get_list": "frappedesk.extends.client.get_list",
}

doc_events = {
	"*": {"validate": "frappedesk.frappedesk.doctype.sla.sla.apply",},
	"Communication": {
		"on_update": [
			"frappedesk.frappedesk.doctype.sla.sla.on_communication_update",
			"frappedesk.frappedesk.doctype.ticket.ticket.set_first_response_time",
		],
		"after_insert": [
			"frappedesk.frappedesk.doctype.ticket.ticket.set_descritption_from_communication",
		],
	},
	"Contact": {
		"on_trash": [
			"frappedesk.frappedesk.doctype.ticket.ticket.update_ticket",
			"frappedesk.frappedesk.doctype.fd_customer.fd_customer.get_contact_count",
		],
		"after_insert": [
			"frappedesk.frappedesk.doctype.fd_customer.fd_customer.get_contact_count"
		],
	},
	"Assignment Rule": {"on_trash": "frappedesk.overrides.on_assignment_rule_trash"},
	"Agent": {"before_insert": "frappedesk.limits.validate_agent_count"},
	"Ticket": {
		"after_insert": (
			"frappedesk.frappedesk.doctype.fd_customer.fd_customer.get_ticket_count"
		),
		"on_trash": "frappedesk.frappedesk.doctype.fd_customer.fd_customer.get_ticket_count",
	},
}

scheduler_events = {
	"daily": [
		"frappedesk.frappedesk.doctype.ticket.ticket.auto_close_tickets",
		"frappedesk.frappedesk.doctype.sla.sla.check_agreement_status",
	],
	"cron": {"* * * * * 0/5": ["frappedesk.overrides.pull_support_emails"]},
}

website_route_rules = [
	# Desk
	{"from_route": "/frappedesk/<path:app_path>", "to_route": "frappedesk"},
	# Customer Portal
	{"from_route": "/support/<path:app_path>", "to_route": "frappedesk"},
]
