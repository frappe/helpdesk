DEFAULT_TICKET_TYPE = "Unspecified"
DEFAULT_TICKET_PRIORITY = "Medium"
DEFAULT_TICKET_TEMPLATE = "Default"
DEFAULT_SLA = "Standard"
DEFAULT_ARTICLE_CATEGORY = "General"

# the ticket every install creates; it is not a sign the site is in use
WELCOME_TICKET_SUBJECT = "Welcome to Helpdesk"

# 7 is set as customer-readable, 8 is agent reserved
TICKET_VISIBLE_FIELD_PERMLEVEL = 7
TICKET_INTERNAL_FIELD_PERMLEVEL = 8

# set by the server: customers reads these but never themselves should submit
SERVER_COMPUTED_FIELDS = [
    "last_customer_response",
    "last_agent_response",
    "first_responded_on",
    "sla",
    "response_by",
    "resolution_by",
    "resolution_date",
    "status_category",
    "on_hold_since",
    "first_response_time",
    "resolution_time",
    "first_response_failed_by",
    "resolution_failed_by",
]

# the key authenticates guest feedback links; a secret is never display data
NEVER_CUSTOMER_VISIBLE_FIELDS = ("key",)

# kept out of the permlevel reset while a customer raises a ticket;
# customer is here because the portal picker sends it and set_customer checks it
PORTAL_INSERT_EXEMPT_FIELDS = [
    "key",
    "raised_by",
    "via_customer_portal",
    "customer",
]

# a customer may always change these: closing sets status_category, rating the feedback
CUSTOMER_ALWAYS_WRITABLE_FIELDS = (
    "status_category",
    "feedback",
    "feedback_extra",
)

# shown on the agent details tab from meta, whether or not the template lists them
CORE_TICKET_FIELDS = ("priority", "ticket_type", "customer", "agent_group")

# the sidebar's "Getting started" steps, in the order Sidebar.vue lists them
ONBOARDING_STEPS = (
    "setup_email_account",
    "invite_agents",
    "setup_sla",
    "create_first_ticket",
    "assign_to_agent",
    "reply_on_ticket",
    "comment_on_ticket",
    "first_article",
    "add_invite_contact",
    "explore_customer_portal",
)

# the steps the first-run setup can tick for the admin
SETUP_CHECKLIST_STEPS = ("setup_email_account", "invite_agents")
