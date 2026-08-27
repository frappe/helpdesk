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
