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

website_route_rules = [
    {
        "from_route": "/frappedesk/<path:app_path>",
        "to_route": "frappedesk",
    },
    {
        "from_route": "/support/<path:app_path>",
        "to_route": "frappedesk",
    },
]

has_website_permission = {
	"Ticket": "frappedesk.frappedesk.doctype.hd_ticket.hd_ticket.has_website_permission",
}

scheduler_events = {
	"daily": [
		"frappedesk.frappedesk.doctype.hd_ticket.hd_ticket.auto_close_tickets",
		"frappedesk.frappedesk.doctype.hd_service_level_agreement.hd_service_level_agreement.check_agreement_status",
	],
	"cron": {"* * * * * 0/5": ["frappedesk.overrides.pull_support_emails"]},
}

doc_events = {
	"*": {
        "validate": "frappedesk.frappedesk.doctype.hd_service_level_agreement.hd_service_level_agreement.apply",
    },
	"Communication": {
		"on_update": [
			"frappedesk.frappedesk.doctype.hd_service_level_agreement.hd_service_level_agreement.on_communication_update",
			"frappedesk.frappedesk.doctype.hd_ticket.hd_ticket.set_first_response_time",
		],
		"after_insert": [
			"frappedesk.frappedesk.doctype.hd_ticket.hd_ticket.set_descritption_from_communication",
			"frappedesk.frappedesk.hooks.communication.after_insert",
		],
	},
	"Contact": {
		"on_trash": [
			"frappedesk.frappedesk.doctype.hd_ticket.hd_ticket.update_ticket",
			"frappedesk.frappedesk.doctype.hd_customer.hd_customer.get_contact_count",
		],
		"after_insert": [
			"frappedesk.frappedesk.doctype.hd_customer.hd_customer.get_contact_count"
		],
	},
	"Assignment Rule": {
        "on_trash": "frappedesk.overrides.on_assignment_rule_trash",
    },
	"Agent": {
        "before_insert": "frappedesk.limits.validate_agent_count",
    },
	"Ticket": {
		"after_insert": (
			"frappedesk.frappedesk.doctype.hd_customer.hd_customer.get_ticket_count"
		),
		"on_trash": "frappedesk.frappedesk.doctype.hd_customer.hd_customer.get_ticket_count",
	},
}
