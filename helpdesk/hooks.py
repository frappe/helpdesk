app_name = "helpdesk"
app_title = "Helpdesk"
app_publisher = "Frappe Technologies"
app_description = "Customer Service Software"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hello@frappe.io"
app_license = "AGPLv3"
required_apps = ["telephony"]
require_type_annotated_api_methods = True

add_to_apps_screen = [
    {
        "name": "helpdesk",
        "logo": "/assets/helpdesk/desk/favicon.svg",
        "title": "Helpdesk",
        "route": "/helpdesk",
        "has_permission": "helpdesk.api.permission.has_app_permission",
    }
]

get_site_info = "helpdesk.activation.get_site_info"

after_install = "helpdesk.setup.install.after_install"
after_migrate = [
    "helpdesk.search.build_index_in_background",
    "helpdesk.search.download_corpus",
]


# Full Text Search
# ------------------

sqlite_search = ["helpdesk.search_sqlite.HelpdeskSearch"]

scheduler_events = {
    "all": [
        "helpdesk.search.build_index_if_not_exists",
        "helpdesk.search.download_corpus",
    ],
    "daily": [
        "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.close_tickets_after_n_days"
    ],
    "hourly_long": [
        "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.update_sla_status_in_ticket"
    ],
}


website_route_rules = [
    {
        "from_route": "/helpdesk/<path:app_path>",
        "to_route": "helpdesk",
    },
    # Frappe ships a legacy "/kb/<category>" rule (Help Article portal) that would
    # otherwise shadow single-segment pages of the Studio-built KB app at /kb.
    # Only a fully static rule outranks that dynamic one in werkzeug's route map, so
    # every single-segment KB page needs its own entry here (multi-segment routes
    # like /kb/articles/<name> don't collide and resolve via the app renderer).
    {
        "from_route": "/kb/customer-tickets",
        "to_route": "kb",
    },
    {
        "from_route": "/kb/new-ticket",
        "to_route": "kb",
    },
]

# The studio portal at /kb replaces the old customer portal. Its ticket URLs keep
# working through these redirects until the old pages are deleted; the desk router
# hard-navigates its legacy customer routes so they resolve here too.
website_redirects = [
    {
        "source": "/helpdesk/my-tickets/new",
        "target": "/kb/new-ticket",
        "forward_query_parameters": True,
    },
    {
        "source": "/helpdesk/my-tickets",
        "target": "/kb/customer-tickets",
        "forward_query_parameters": True,
    },
    {
        "source": r"/helpdesk/my-tickets/(.*)",
        "target": r"/kb/tickets/\1",
    },
]

user_invitation = {
    "allowed_roles": {
        "Agent Manager": [
            "Agent",
            "Agent Manager",
            "HD Customer",
            "HD Customer Manager",
        ],
        "System Manager": [
            "Agent",
            "Agent Manager",
            "System Manager",
            "HD Customer",
            "HD Customer Manager",
        ],
        # Customer managers can invite members into their own organization only;
        # scoping is enforced by the User Invitation before_insert hook below.
        "HD Customer Manager": [
            "HD Customer",
            "HD Customer Manager",
        ],
    },
    "after_accept": "helpdesk.helpdesk.hooks.user_invitation.after_accept",
    "extra_invite_params": ["customer", "contact"],
}

doc_events = {
    "User Invitation": {
        "before_insert": "helpdesk.helpdesk.hooks.user_invitation.validate_customer_scope",
    },
    "Assignment Rule": {
        "on_trash": "helpdesk.extends.assignment_rule.on_assignment_rule_trash",
        "validate": "helpdesk.extends.assignment_rule.on_assignment_rule_validate",
    },
    "Customer": {
        "after_insert": "helpdesk.integrations.erpnext.customer.after_insert",
        "on_update": "helpdesk.integrations.erpnext.customer.on_update",
        "before_rename": "helpdesk.integrations.erpnext.customer.before_rename",
        "after_rename": "helpdesk.integrations.erpnext.customer.after_rename",
        "on_trash": "helpdesk.integrations.erpnext.customer.on_trash",
    },
    "User Permission": {
        "before_validate": "helpdesk.integrations.erpnext.user_permission.before_validate",
        "after_insert": "helpdesk.integrations.erpnext.user_permission.after_insert",
        "on_update": "helpdesk.integrations.erpnext.user_permission.on_update",
        "on_trash": "helpdesk.integrations.erpnext.user_permission.on_trash",
    },
    "DocShare": {
        "before_validate": "helpdesk.integrations.erpnext.doc_share.before_validate",
        "after_insert": "helpdesk.integrations.erpnext.doc_share.after_insert",
        "on_update": "helpdesk.integrations.erpnext.doc_share.on_update",
        "on_trash": "helpdesk.integrations.erpnext.doc_share.on_trash",
    },
    "Notification Log": {
        "before_insert": "helpdesk.extends.notification_log.before_insert",
    },
}

# For List View
permission_query_conditions = {
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.permission_query",
    "HD Saved Reply": "helpdesk.helpdesk.doctype.hd_saved_reply.hd_saved_reply.permission_query",
    "HD Customer": "helpdesk.helpdesk.doctype.hd_customer.hd_customer.permission_query",
}

has_permission = {
    "HD Agent": "helpdesk.helpdesk.doctype.hd_agent.hd_agent.has_permission",
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.has_permission",
    "HD Saved Reply": "helpdesk.helpdesk.doctype.hd_saved_reply.hd_saved_reply.has_permission",
    "HD Customer": "helpdesk.helpdesk.doctype.hd_customer.hd_customer.has_permission",
}


# DocType Class
# ---------------
# Override standard doctype classes
override_doctype_class = {
    "Email Account": "helpdesk.overrides.email_account.CustomEmailAccount",
    "Assignment Rule": "helpdesk.overrides.assignment_rule.HelpdeskAssignmentRule",
    "User Invitation": "helpdesk.overrides.user_invitation.HelpdeskUserInvitation",
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
auth_hooks = ["helpdesk.auth.authenticate"]
