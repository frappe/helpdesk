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

# Fields kept out of the permlevel reset while a customer raises a ticket.
# The server writes key, raised_by and via_customer_portal itself. customer
# comes from the portal's own picker, and set_customer checks it belongs to
# the contact. The exemption is insert only: later saves revert these fields.
PORTAL_INSERT_EXEMPT_FIELDS = [
    "key",
    "raised_by",
    "via_customer_portal",
    "customer",
]

# Levels a customer may write while creating a ticket: the open level and the
# one the default template puts its visible fields at.
CREATION_FILLABLE_PERMLEVELS = (0, TICKET_VISIBLE_FIELD_PERMLEVEL)

# A customer fills the template's fields once, while raising the ticket.
# Afterwards only closing the ticket and rating it are still theirs.
# status_category is not really theirs: it is fetched from status, so the
# framework rewrites it on every save before any of our hooks look at it.
CUSTOMER_WRITABLE_AFTER_CREATION = (
    "status_category",
    "feedback",
    "feedback_extra",
)
