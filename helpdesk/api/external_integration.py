"""
External API Integration for HMIS and other third-party systems
Create tickets from external systems via authenticated API calls
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime
from typing import Optional


@frappe.whitelist(allow_guest=True)
def create_ticket_from_hmis(
    subject: str,
    description: str,
    raised_by_email: str,
    raised_by_name: Optional[str] = None,
    priority: Optional[str] = None,
    ticket_type: Optional[str] = None,
    category: Optional[str] = None,
    custom_fields: Optional[dict] = None,
    external_reference_id: Optional[str] = None,
    hmis_module: Optional[str] = None,
    hmis_url: Optional[str] = None,
    facility: Optional[str] = None,
    custom_phone: Optional[str] = None,
    custom_section: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    source: Optional[str] = None
):
    """
    Create a helpdesk ticket from HMIS system

    Args:
        subject: Ticket subject/title (required)
        description: Ticket description/details (required)
        raised_by_email: Email of person raising the issue (required)
        raised_by_name: Full name of person (optional)
        priority: Ticket priority - Low/Medium/High/Urgent (default: Medium)
        ticket_type: Type of ticket - Issue/Question/Incident/Feature (optional)
        category: Ticket category/classification (optional)
        custom_fields: Dictionary of custom field values (optional)
        external_reference_id: Reference ID from HMIS system (optional)
        hmis_module: Which HMIS module raised this (optional)
        hmis_url: Direct URL to issue in HMIS (optional)
        api_key: API authentication key (required for external calls)
        api_secret: API authentication secret (required for external calls)

    Returns:
        dict: Created ticket details with ticket_id, ticket_name, and ticket_url

    Example POST request:
        POST /api/method/helpdesk.api.external_integration.create_ticket_from_hmis
        Content-Type: application/json

        {
            "subject": "Unable to save patient record",
            "description": "Getting timeout error when saving patient admission form",
            "raised_by_email": "implementor@facility.com",
            "raised_by_name": "John Implementor",
            "priority": "High",
            "ticket_type": "Issue",
            "category": "Technical Support",
            "external_reference_id": "HMIS-ISSUE-12345",
            "hmis_module": "Patient Management",
            "hmis_url": "https://hmis.example.com/issues/12345",
            "api_key": "your-api-key-here",
            "api_secret": "your-api-secret-here"
        }
    """

    # Step 1: Authenticate the request
    if not _authenticate_external_request(api_key, api_secret):
        frappe.throw(
            _("Invalid API credentials. Please check your API key and secret."),
            frappe.AuthenticationError
        )

    # Step 2: Validate required fields
    if not subject or not description or not raised_by_email:
        frappe.throw(
            _("Missing required fields: subject, description, and raised_by_email are mandatory"),
            frappe.MandatoryError
        )

    valid_priorities = ["Low", "Medium", "High", "Urgent"]
    if not priority or priority not in valid_priorities:
        frappe.throw(
            _("priority is required. Must be one of: Low, Medium, High, Urgent"),
            frappe.MandatoryError
        )

    # Step 3: Get or create contact for the user
    contact = _get_or_create_contact(raised_by_email, raised_by_name)

    # Step 4: Build ticket description with HMIS context
    full_description = _build_ticket_description(
        description,
        external_reference_id,
        hmis_module,
        hmis_url
    )

    # Step 5: Prepare ticket data
    ticket_data = {
        "doctype": "HD Ticket",
        "subject": subject,
        "description": full_description,
        "raised_by": raised_by_email,
        "contact": contact.name if contact else None,
        "status": "Open",
        "priority": priority,
        "via_customer_portal": False,  # Mark as external system
    }

    # Add optional fields
    if ticket_type:
        ticket_data["ticket_type"] = ticket_type

    if category:
        ticket_data["category"] = category

    # Add custom fields if provided
    if custom_fields and isinstance(custom_fields, dict):
        ticket_data.update({k: v for k, v in custom_fields.items() if str(k).startswith("custom_")})

    # Store HMIS reference in custom field if it exists
    if external_reference_id:
        ticket_data["custom_external_reference"] = external_reference_id

    if hmis_module:
        ticket_data["custom_hmis_module"] = hmis_module

    if facility:
        # facility may be a facility_code (FID) or a full facility name — resolve either way
        facility_doc = frappe.db.get_value(
            "HD Facility",
            {"facility_code": facility},
            ["name", "county", "subcounty"],
            as_dict=True
        )
        if not facility_doc:
            facility_doc = frappe.db.get_value(
                "HD Facility",
                {"name": facility},
                ["name", "county", "subcounty"],
                as_dict=True
            )
        if facility_doc:
            ticket_data["facility"] = facility_doc.name
            if facility_doc.county:
                ticket_data["county"] = facility_doc.county
            if facility_doc.subcounty:
                ticket_data["sub_county"] = facility_doc.subcounty

    if custom_phone:
        ticket_data["custom_phone"] = custom_phone

    if custom_section:
        ticket_data["custom_section"] = custom_section

    if source in ("F360", "P360", "Admin Central"):
        ticket_data["brand"] = source
        ticket_data["source"] = source

    # Step 6: Create the ticket
    try:
        # Set system user context to bypass permissions for external API
        frappe.set_user("Administrator")

        ticket_doc = frappe.get_doc(ticket_data)
        ticket_doc.flags.ignore_permissions = True  # Allow external system to create
        ticket_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        # Step 7: Create initial comment with HMIS context
        if external_reference_id or hmis_url:
            _add_hmis_reference_comment(ticket_doc.name, external_reference_id, hmis_url)

        # Step 8: Return ticket details
        ticket_url = frappe.utils.get_url(f"/helpdesk/tickets/{ticket_doc.name}")

        return {
            "success": True,
            "ticket_id": ticket_doc.name,
            "ticket_name": ticket_doc.name,
            "ticket_url": ticket_url,
            "ticket_subject": ticket_doc.subject,
            "ticket_status": ticket_doc.status,
            "ticket_priority": ticket_doc.priority,
            "created_on": ticket_doc.creation,
            "message": f"Ticket {ticket_doc.name} created successfully"
        }

    except Exception as e:
        frappe.log_error(
            title="HMIS Ticket Creation Failed",
            message=frappe.get_traceback()
        )
        frappe.throw(
            _("Failed to create ticket: {0}").format(str(e)),
            frappe.ValidationError
        )


@frappe.whitelist(allow_guest=True)
def update_ticket_from_hmis(
    ticket_id: str,
    comment: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
):
    """
    Update an existing ticket from HMIS system

    Args:
        ticket_id: Helpdesk ticket ID/name (required)
        comment: Add a comment to the ticket (optional)
        status: Update ticket status - Open/Replied/Resolved/Closed (optional)
        priority: Update priority - Low/Medium/High/Urgent (optional)
        api_key: API authentication key (required)
        api_secret: API authentication secret (required)

    Returns:
        dict: Updated ticket details
    """

    # Authenticate
    if not _authenticate_external_request(api_key, api_secret):
        frappe.throw(_("Invalid API credentials"), frappe.AuthenticationError)

    # Set system user context to bypass permissions for external API
    frappe.set_user("Administrator")

    # Validate ticket exists
    if not frappe.db.exists("HD Ticket", ticket_id):
        frappe.throw(_("Ticket {0} not found").format(ticket_id), frappe.DoesNotExistError)

    # Get ticket
    ticket_doc = frappe.get_doc("HD Ticket", ticket_id)
    ticket_doc.flags.ignore_permissions = True

    # Update fields if provided
    updated = False

    if status:
        ticket_doc.status = status
        updated = True

    if priority:
        ticket_doc.priority = priority
        updated = True

    if updated:
        ticket_doc.save()

    # Add comment if provided
    if comment:
        ticket_doc.add_comment("Comment", comment)

    frappe.db.commit()

    return {
        "success": True,
        "ticket_id": ticket_doc.name,
        "ticket_status": ticket_doc.status,
        "ticket_priority": ticket_doc.priority,
        "message": f"Ticket {ticket_doc.name} updated successfully"
    }


@frappe.whitelist(allow_guest=True)
def get_ticket_status(
    ticket_id: str,
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
):
    """
    Get current status of a ticket from HMIS

    Args:
        ticket_id: Helpdesk ticket ID/name (required)
        api_key: API authentication key (required)
        api_secret: API authentication secret (required)

    Returns:
        dict: Ticket status and details
    """

    # Authenticate
    if not _authenticate_external_request(api_key, api_secret):
        frappe.throw(_("Invalid API credentials"), frappe.AuthenticationError)

    # Set system user context to bypass permissions for external API
    frappe.set_user("Administrator")

    # Validate ticket exists
    if not frappe.db.exists("HD Ticket", ticket_id):
        frappe.throw(_("Ticket {0} not found").format(ticket_id), frappe.DoesNotExistError)

    # Get ticket
    ticket = frappe.get_doc("HD Ticket", ticket_id)

    return {
        "success": True,
        "ticket_id": ticket.name,
        "subject": ticket.subject,
        "status": ticket.status,
        "priority": ticket.priority,
        "raised_by": ticket.raised_by,
        "agent_group": ticket.agent_group,
        "assigned_to": ticket._assign,
        "created_on": ticket.creation,
        "modified_on": ticket.modified,
        "first_response_time": ticket.first_responded_on,
        "resolution_date": ticket.resolution_date,
    }


# ============================================================================
# HELPER FUNCTIONS (Private)
# ============================================================================

def _authenticate_external_request(api_key: str, api_secret: str) -> bool:
    """
    Authenticate external API request using API key and secret

    Check against HD Settings for valid API credentials
    """

    if not api_key or not api_secret:
        return False

    # Get API credentials from HD Settings
    settings = frappe.get_cached_doc("HD Settings")

    # Check if external API is enabled
    if not settings.get("enable_external_api"):
        frappe.log_error(
            title="External API Disabled",
            message="External API integration is disabled in HD Settings"
        )
        return False

    # Validate API key and secret
    stored_api_key = settings.get("external_api_key")
    stored_api_secret = settings.get_password("external_api_secret")

    if not stored_api_key or not stored_api_secret:
        frappe.log_error(
            title="API Credentials Not Configured",
            message="External API credentials not set in HD Settings"
        )
        return False

    # Compare credentials (use secrets.compare_digest for timing attack protection)
    import secrets

    key_match = secrets.compare_digest(api_key, stored_api_key)
    secret_match = secrets.compare_digest(api_secret, stored_api_secret)

    return key_match and secret_match


def _get_or_create_contact(email: str, full_name: Optional[str] = None):
    """
    Get existing contact or create new one
    """

    # Check if contact exists
    contact = frappe.db.get_value(
        "Contact",
        {"email_id": email},
        ["name", "first_name", "last_name"],
        as_dict=True
    )

    if contact:
        return frappe.get_doc("Contact", contact.name)

    # Create new contact
    contact_doc = frappe.get_doc({
        "doctype": "Contact",
        "email_id": email,
        "first_name": full_name or email.split("@")[0],
        "status": "Passive"
    })

    contact_doc.flags.ignore_permissions = True
    contact_doc.insert()

    return contact_doc


def _build_ticket_description(
    description: str,
    external_reference_id: Optional[str],
    hmis_module: Optional[str],
    hmis_url: Optional[str]
) -> str:
    """
    Build enhanced ticket description with HMIS context
    """

    parts = [description]

    if external_reference_id or hmis_module or hmis_url:
        parts.append("\n\n---\n**HMIS Issue Details:**")

        if external_reference_id:
            parts.append(f"- **Reference ID:** {external_reference_id}")

        if hmis_module:
            parts.append(f"- **Module:** {hmis_module}")

        if hmis_url:
            parts.append(f"- **HMIS Link:** [{external_reference_id or 'View Issue'}]({hmis_url})")

    return "\n".join(parts)


def _add_hmis_reference_comment(ticket_name: str, reference_id: str, hmis_url: str):
    """
    Add a system comment with HMIS reference
    """

    comment_text = "This ticket was created from HMIS system"

    if reference_id:
        comment_text += f" (Reference: {reference_id})"

    if hmis_url:
        comment_text += f"\n\nView in HMIS: {hmis_url}"

    frappe.get_doc("HD Ticket", ticket_name).add_comment("Info", comment_text)


# ============================================================================
# WEBHOOK ENDPOINTS (Optional - for HMIS to push updates)
# ============================================================================

@frappe.whitelist(allow_guest=True)
def hmis_webhook(data: dict):
    """
    Generic webhook endpoint for HMIS to push updates

    HMIS can POST to: /api/method/helpdesk.api.external_integration.hmis_webhook

    Expected payload:
    {
        "event": "issue_created" | "issue_updated" | "issue_resolved",
        "api_key": "your-key",
        "api_secret": "your-secret",
        "data": {
            "reference_id": "HMIS-123",
            "subject": "Issue title",
            "description": "Issue details",
            ...
        }
    }
    """

    import json

    if isinstance(data, str):
        data = json.loads(data)

    event = data.get("event")
    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    payload = data.get("data", {})

    # Authenticate
    if not _authenticate_external_request(api_key, api_secret):
        frappe.throw(_("Invalid API credentials"), frappe.AuthenticationError)

    # Route based on event type
    if event == "issue_created":
        return create_ticket_from_hmis(
            subject=payload.get("subject"),
            description=payload.get("description"),
            raised_by_email=payload.get("user_email"),
            raised_by_name=payload.get("user_name"),
            priority=payload.get("priority"),
            external_reference_id=payload.get("reference_id"),
            hmis_module=payload.get("module"),
            hmis_url=payload.get("url"),
            api_key=api_key,
            api_secret=api_secret
        )

    elif event == "issue_updated":
        return update_ticket_from_hmis(
            ticket_id=payload.get("ticket_id"),
            comment=payload.get("comment"),
            status=payload.get("status"),
            api_key=api_key,
            api_secret=api_secret
        )

    else:
        frappe.throw(_("Unknown event type: {0}").format(event))
