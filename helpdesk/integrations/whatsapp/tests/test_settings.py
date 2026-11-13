import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.integrations.whatsapp.test_utils import (
    make_whatsapp_account,
    requires_whatsapp,
)
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


@requires_whatsapp
class TestWhatsAppAppendActions(IntegrationTestCase):
    """Helpdesk files messages itself, so an account may not append them to tickets too."""

    def tearDown(self) -> None:
        frappe.db.rollback()

    def test_an_append_action_to_hd_ticket_is_refused(self) -> None:
        with self.assertRaisesRegex(frappe.ValidationError, "remove this append"):
            make_whatsapp_account(
                append_actions=[append_action("HD Ticket", "raised_by", "subject")]
            )

    def test_an_append_action_to_another_doctype_saves(self) -> None:
        account = make_whatsapp_account(
            append_actions=[append_action("Contact", "mobile_no", "first_name")]
        )
        rows = frappe.get_doc("WA Account", account).append_actions
        self.assertEqual([row.append_to for row in rows], ["Contact"])

    def test_adding_one_to_an_existing_account_is_refused(self) -> None:
        doc = frappe.get_doc("WA Account", make_whatsapp_account())
        doc.append("append_actions", append_action("HD Ticket", "raised_by", "subject"))
        with self.assertRaisesRegex(frappe.ValidationError, "remove this append"):
            doc.save(ignore_permissions=True)


def append_action(doctype: str, sender_field: str, sender_name_field: str) -> dict:
    return {
        "append_to": doctype,
        "trigger_on": "Incoming",
        "sender_field": sender_field,
        "sender_name_field": sender_name_field,
    }
