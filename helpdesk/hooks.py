app_name = "helpdesk"
app_title = "Helpdesk"
app_publisher = "Frappe Technologies"
app_description = "Customer Service Software"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hello@frappe.io"
app_license = "AGPLv3"
required_apps = ["telephony"]

add_to_apps_screen = [
    {
        "name": "helpdesk",
        "logo": "/assets/helpdesk/desk/favicon.svg",
        "title": "Helpdesk",
        "route": "/helpdesk",
        "has_permission": "helpdesk.api.permission.has_app_permission",
    }
]

after_install = "helpdesk.setup.install.after_install"
after_migrate = [
    "helpdesk.search.build_index_in_background",
    "helpdesk.search.download_corpus",
]

scheduler_events = {
    "all": [
        "helpdesk.search.build_index_if_not_exists",
        "helpdesk.search.download_corpus",
    ],
    "daily": [
        "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.close_tickets_after_n_days"
    ],
}


website_route_rules = [
    {
        "from_route": "/helpdesk/<path:app_path>",
        "to_route": "helpdesk",
    },
]

user_invitation = {
    "allowed_roles": {
        "Agent Manager": ["Agent", "Agent Manager"],
        "System Manager": ["Agent", "Agent Manager", "System Manager"],
    },
    "after_accept": "helpdesk.helpdesk.hooks.user_invitation.after_accept",
}

doc_events = {
    "Contact": {
        "before_insert": "helpdesk.overrides.contact.before_insert",
    },
    "Assignment Rule": {
        "on_trash": "helpdesk.extends.assignment_rule.on_assignment_rule_trash",
    },
}

has_permission = {
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.has_permission",
}

permission_query_conditions = {
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.permission_query",
}

# DocType Class
# ---------------
# Override standard doctype classes
override_doctype_class = {
    "Email Account": "helpdesk.overrides.email_account.CustomEmailAccount",
}

ignore_links_on_delete = [
    "HD Notification",
    "HD Ticket Comment",
]

# setup wizard
# setup_wizard_requires = "assets/helpdesk/js/setup_wizard.js"
# setup_wizard_stages = "helpdesk.setup.setup_wizard.get_setup_stages"
setup_wizard_complete = "helpdesk.setup.setup_wizard.setup_complete"


# Testing
# ---------------

before_tests = "helpdesk.test_utils.before_tests"
