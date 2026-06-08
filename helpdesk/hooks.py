app_name = "helpdesk"
app_title = "ServiceDesk"
app_publisher = "Frappe Technologies"
app_description = "Customer Service Software"
app_icon = "fa fa-headset"
app_color = "grey"
app_email = "hello@frappe.io"
app_license = "AGPLv3"
required_apps = ["telephony"]
require_type_annotated_api_methods = True

add_to_apps_screen = [
    {
        "name": "helpdesk",
        "logo": "/assets/helpdesk/desk/favicon.svg",
        "title": "ServiceDesk",
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
    "cron": {
        # SLA monitor: fires sla_warning and sla_breached automation triggers
        # Chat session cleanup: ends inactive sessions (Story 3.2)
        "*/5 * * * *": [
            "helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.check_sla_breaches",
            "helpdesk.helpdesk.chat.session_cleanup.cleanup_inactive_sessions",
            "helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler.auto_escalate_tickets",
        ],
        # Chat response timeout: sends auto-message after 2 min with no agent reply (Story 3.4)
        "*/1 * * * *": [
            "helpdesk.helpdesk.chat.response_timeout.check_unanswered_sessions",
        ],
        # CSAT survey batch send: enqueues survey emails for eligible resolved tickets (Story 3.7)
        "0 */1 * * *": [
            "helpdesk.helpdesk.doctype.hd_csat_response.csat_scheduler.send_pending_surveys",
        ],
    },
    "daily": [
        "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.close_tickets_after_n_days",
        "helpdesk.helpdesk.doctype.hd_automation_log.cleanup.purge_old_logs",
        "helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders",
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
        "validate": "helpdesk.extends.assignment_rule.on_assignment_rule_validate",
    },
    "HD Ticket": {
        "before_insert": "helpdesk.overrides.hd_ticket_brand.assign_brand_from_email",
        "after_insert": "helpdesk.helpdesk.automation.engine.on_ticket_created",
        "on_update": "helpdesk.helpdesk.automation.engine.on_ticket_updated",
    },
    "HD Brand": {
        "on_update": "helpdesk.overrides.hd_ticket_brand.invalidate_brand_cache",
        "after_insert": "helpdesk.overrides.hd_ticket_brand.invalidate_brand_cache",
        "on_trash": "helpdesk.overrides.hd_ticket_brand.invalidate_brand_cache",
    },
}

has_permission = {
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.has_permission",
    "HD Saved Reply": "helpdesk.helpdesk.doctype.hd_saved_reply.hd_saved_reply.has_permission",
}

permission_query_conditions = {
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.permission_query",
    "HD Saved Reply": "helpdesk.helpdesk.doctype.hd_saved_reply.hd_saved_reply.permission_query",
}

# DocType Class
# ---------------
# Override standard doctype classes
override_doctype_class = {
    "Email Account": "helpdesk.overrides.email_account.CustomEmailAccount",
    "Email Queue": "helpdesk.email.email_queue_override.SesAwareEmailQueue",
}

# Email Override
# --------------
# AWS SES email transport override
override_email_send = "helpdesk.email.aws_ses_override.send"

ignore_links_on_delete = [
    "HD Notification",
    "HD Ticket Comment",
    "HD Automation Log",
]

# setup wizard
# setup_wizard_requires = "assets/helpdesk/js/setup_wizard.js"
# setup_wizard_stages = "helpdesk.setup.setup_wizard.get_setup_stages"
setup_wizard_complete = "helpdesk.setup.setup_wizard.setup_complete"


# Testing
# ---------------

before_tests = "helpdesk.test_utils.before_tests"
auth_hooks = ["helpdesk.auth.authenticate"]

# Fixtures
# --------
fixtures = [
    {"dt": "HD Incident Model"},
    {"dt": "HD Support Level"},
    {"dt": "Workflow", "filters": [["document_type", "=", "HD Article"]]},
]

# CLI Commands
# ------------
# Custom bench commands for helpdesk app
# Temporarily disabled to avoid pickle issues during migration
# from helpdesk.commands.brand_fixtures import commands
