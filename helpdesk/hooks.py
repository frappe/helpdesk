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

doc_events = {
	"Communication": {
		"after_insert": "helpdesk.helpdesk.hooks.communication.after_insert",
	},
	"Contact": {
		"before_insert": "helpdesk.helpdesk.hooks.contact.before_insert",
	},
	"Assignment Rule": {
		"on_trash": "helpdesk.overrides.on_assignment_rule_trash",
	},
}
