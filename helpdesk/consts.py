DEFAULT_TICKET_TYPE = "Unspecified"
DEFAULT_TICKET_PRIORITY = "Medium"
DEFAULT_TICKET_TEMPLATE = "Default"
DEFAULT_SLA = "Standard"
DEFAULT_ARTICLE_CATEGORY = "General"

# HD Ticket permission levels: 7 is customer-readable, 8 is agent-only
TICKET_VISIBLE_FIELD_PERMLEVEL = 7
TICKET_INTERNAL_FIELD_PERMLEVEL = 8

# set by the server: customers may read these but never supply them
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

# levels a customer may write while creating a ticket
CREATION_FILLABLE_PERMLEVELS = (0, TICKET_VISIBLE_FIELD_PERMLEVEL)

# changes the customer edit guard allows; status_category is fetched from status
CUSTOMER_EDIT_EXEMPT_FIELDS = (
    "status_category",
    "feedback",
    "feedback_extra",
)
