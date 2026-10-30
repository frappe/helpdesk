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

after_install = [
    "helpdesk.patches.add_user_force_password_change.execute",
    "helpdesk.setup.install.after_install",
]
after_migrate = [
    "helpdesk.search.build_index_in_background",
    "helpdesk.search.download_corpus",
]

# Session hooks for role-based redirects (commented out - using frontend router instead)
# on_session_creation = "helpdesk.overrides.session.on_session_creation"

# Request middleware to block customer desk access
before_request = ["helpdesk.overrides.desk_middleware.block_customer_desk_access"]

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
            "helpdesk.integrations.zenhub.retry_failed",
            # PAUSED 2026-09-28 -- mass reassignment/notification flooding from a
            # large SLA-breach backlog (180 tickets). Re-enable once the backlog
            # is triaged/closed and the L1-L4 tier structure is finalized.
            # "helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler.auto_escalate_tickets",
            # "helpdesk.helpdesk.doctype.hd_ticket.escalation_rule_engine.run_age_based_rules",
            # "helpdesk.helpdesk.doctype.hd_ticket.agent_rotation.run_agent_rotation",
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
    "hourly": [
        "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.escalate_ticket_priorities",
    ],
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
        "before_insert": [
            "helpdesk.overrides.l1_raised_routing.route_l1_raised_tickets",
            "helpdesk.overrides.l2_raised_routing.route_l2_raised_tickets",
            "helpdesk.overrides.hd_ticket_brand.assign_brand_from_email",
        ],
        "validate": "helpdesk.overrides.hd_ticket_phone.validate_phone_format",
        "after_insert": [
            "helpdesk.helpdesk.automation.engine.on_ticket_created",
            "helpdesk.overrides.assignment_rule_dedupe.apply_once",
            "helpdesk.overrides.report_registration_routing.route_report_registration_tickets",
            "helpdesk.overrides.feature_request_routing.route_feature_requests",
            "helpdesk.search.build_index_in_background", # <-- ADD THIS
            "helpdesk.overrides.hd_ticket_phone.sync_owner_mobile_no",
        ],
        "on_update": [
            "helpdesk.helpdesk.automation.engine.on_ticket_updated",
            "helpdesk.overrides.assignment_rule_dedupe.apply_once",
            "helpdesk.search.build_index_in_background", # <-- ADD THIS
            "helpdesk.overrides.feature_request_routing.route_changed_to_feature_request",
        ],

        "on_trash": [
        "helpdesk.search.build_index_in_background", # <-- ADD THIS
        ],
    },
    "HD Brand": {
        "on_update": "helpdesk.overrides.hd_ticket_brand.invalidate_brand_cache",
        "after_insert": "helpdesk.overrides.hd_ticket_brand.invalidate_brand_cache",
        "on_trash": "helpdesk.overrides.hd_ticket_brand.invalidate_brand_cache",
    },
    "ToDo": {
        "after_insert": "helpdesk.overrides.todo_assignment.notify_hd_ticket_assignment",
    },
    "HD Agent Absence": {
        "validate": "helpdesk.integrations.agent_absence.validate",
    },
}

has_permission = {
    "HD Ticket Activity": "helpdesk.helpdesk.doctype.hd_ticket_activity.hd_ticket_activity.has_permission",
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.has_permission",
    "HD Saved Reply": "helpdesk.helpdesk.doctype.hd_saved_reply.hd_saved_reply.has_permission",
    "HD Agent": "helpdesk.overrides.hd_agent_permission.has_permission",
}

permission_query_conditions = {
    "HD Ticket Activity": "helpdesk.helpdesk.doctype.hd_ticket_activity.hd_ticket_activity.permission_query",
    "HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.permission_query",
    "HD Saved Reply": "helpdesk.helpdesk.doctype.hd_saved_reply.hd_saved_reply.permission_query",
    "HD Agent": "helpdesk.overrides.hd_agent_permission.permission_query",
    "Contact": "helpdesk.overrides.contact_scope.permission_query",
    "HD Brand": "helpdesk.overrides.brand_scope.permission_query",
}

# DocType Class
# ---------------
# Override standard doctype classes
override_doctype_class = {
    "Email Account": "helpdesk.overrides.email_account.CustomEmailAccount",
    "Email Queue": "helpdesk.email.email_queue_override.SesAwareEmailQueue",
    "User": "helpdesk.overrides.user.HelpdeskUser",
    "Assignment Rule": "helpdesk.overrides.assignment_rule_absence.AbsenceAwareAssignmentRule",
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
    {"dt": "HD Team"},  # includes HD Team Member child rows (regional/county assignments)
]

# CLI Commands
# ------------
# Custom bench commands for helpdesk app
# Temporarily disabled to avoid pickle issues during migration
# from helpdesk.commands.brand_fixtures import commands

# SSO — Microsoft Entra ID
# ------------------------
# Replaces core's login_via_office365 with a hardened version that validates
# the ID token (signature, issuer, audience, tenant), enforces a domain
# allowlist, and pins each user to one Entra identity.
override_whitelisted_methods = {
    "frappe.integrations.oauth2_logins.login_via_office365": "helpdesk.sso.entra.login_via_entra",
}
