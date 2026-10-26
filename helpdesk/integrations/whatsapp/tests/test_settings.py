import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.integrations.whatsapp.test_utils import requires_whatsapp
from helpdesk.test_utils import make_agent_manager


@requires_whatsapp
class TestWhatsAppSettingsAccess(IntegrationTestCase):
    """The settings page writes WA Account and WA Settings through the standard API."""

    def test_only_system_managers_can_change_accounts_and_webhook_settings(
        self,
    ) -> None:
        manager = make_agent_manager("whatsapp-settings")
        for doctype in ("WA Account", "WA Settings"):
            for ptype in ("create", "write"):
                with self.subTest(doctype=doctype, ptype=ptype):
                    self.assertTrue(
                        frappe.has_permission(doctype, ptype, user="Administrator")
                    )
                    self.assertFalse(
                        frappe.has_permission(doctype, ptype, user=manager)
                    )
