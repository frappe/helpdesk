app_name = "helpdesk"
app_title = "HelpDesk"
app_publisher = "Frappe Technologies"
app_description = "Customer Service Software"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hello@frappe.io"
app_license = "AGPLv3"

# TODO: the logic for has_website_permission is minimised a little for now, will need to re-check
has_website_permission = {
	"Issue": "helpdesk.helpdesk.doctype.issue.issue.has_website_permission",
}

doc_events = {
    "*": {
		"validate": "helpdesk.helpdesk.doctype.service_level_agreement.service_level_agreement.apply",
    },
    "Communication": {
		"on_update": [
			"helpdesk.helpdesk.doctype.service_level_agreement.service_level_agreement.on_communication_update",
			"helpdesk.helpdesk.doctype.issue.issue.set_first_response_time"
		]
	},
    "Contact": {
		"on_trash": "helpdesk.helpdesk.doctype.issue.issue.update_issue",
	},
}

scheduler_events = {
    "daily": [
		"helpdesk.helpdesk.doctype.issue.issue.auto_close_tickets",
		"helpdesk.helpdesk.doctype.service_level_agreement.service_level_agreement.check_agreement_status",
    ]
}