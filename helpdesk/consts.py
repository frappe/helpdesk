DEFAULT_TICKET_TYPE = "Unspecified"
DEFAULT_TICKET_PRIORITY = "Medium"
DEFAULT_TICKET_TEMPLATE = "Default"
DEFAULT_SLA = "Standard"
DEFAULT_ARTICLE_CATEGORY = "General"

# Permission levels for HD Ticket fields. Customers can see level 7 fields
# and fill them while creating a ticket. Level 8 fields are for agents only.
TICKET_VISIBLE_FIELD_PERMLEVEL = 7
TICKET_INTERNAL_FIELD_PERMLEVEL = 8

# Response stamps and SLA outputs: the server works these out, so a customer
# may read them but never supply them. The ticket keeps them out of the
# creation form's exemption, and the template refuses to show them.
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

# Kept out of the permlevel reset while a customer raises a ticket. customer
# is the odd one: the portal picker sends it and set_customer checks it.
PORTAL_INSERT_EXEMPT_FIELDS = [
    "key",
    "raised_by",
    "via_customer_portal",
    "customer",
]

# Levels a customer may write while creating a ticket: the open level and the
# one the default template puts its visible fields at.
CREATION_FILLABLE_PERMLEVELS = (0, TICKET_VISIBLE_FIELD_PERMLEVEL)

# Changes the customer edit guard must not refuse. status_category is fetched
# from status, so closing rewrites it before the guard ever looks.
CUSTOMER_EDIT_EXEMPT_FIELDS = (
    "status_category",
    "feedback",
    "feedback_extra",
)
