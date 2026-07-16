import frappe
from frappe.core.doctype.user_invitation.user_invitation import UserInvitation


class HelpdeskUserInvitation(UserInvitation):
    def _get_email_title(self):
        # Use the org's brand name (set during onboarding) in the invitation
        # subject — "You've been invited to join <brand>" — falling back to the
        # framework app title when it isn't set. The override class is
        # registered site-wide, so invitations from other apps (ERPNext, etc.)
        # must keep their own app title.
        if self.app_name != "helpdesk":
            return super()._get_email_title()
        return (
            frappe.db.get_single_value("HD Settings", "brand_name")
            or super()._get_email_title()
        )
