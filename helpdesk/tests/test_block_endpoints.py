from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.auth import authenticate
from helpdesk.test_utils import create_contact, unique_email


class TestBlockEndpoints(IntegrationTestCase):
    def setUp(self) -> None:
        self.contact = create_contact("Blocked Caller", unique_email("blocked-caller"))
        # System Users skip the check; the role's desk access varies by site
        frappe.db.set_value("User", self.contact["user"], "user_type", "Website User")
        self.enterContext(patch.dict(frappe.conf, {"block_endpoints": 1}))
        self.enterContext(patch.object(frappe.local, "request", None, create=True))
        self.enterContext(patch.dict(frappe.form_dict, {"cmd": None}))
        self.enterContext(self.set_user(self.contact["user"]))

    def call(self, path: str) -> None:
        frappe.local.request = frappe._dict(path=path)
        authenticate()

    def test_v1_and_v2_method_paths_follow_the_method_rules(self) -> None:
        # frappectl calls methods through /api/v2/method/
        self.call("/api/v2/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one")
        self.call("/api/v1/method/helpdesk.api.contact.search_contacts")
        self.call("/api/v2/method/frappe.client.get_list")
        with self.assertRaises(frappe.PermissionError):
            self.call("/api/v2/method/frappe.auth.get_logged_user")

    def test_v2_document_routes_stay_blocked(self) -> None:
        with self.assertRaises(frappe.PermissionError):
            self.call("/api/v2/document/HD Ticket")
