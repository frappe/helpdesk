# Copyright (c) 2022, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.helpdesk.doctype.hd_agent.hd_agent import update_agent_role


class TestHDAgent(FrappeTestCase):
    test_user = "test_user@test.com"

    def setUp(self):
        if not frappe.db.exists("User", self.test_user):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.test_user,
                    "first_name": "Test User",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)
        else:
            frappe.get_doc("User", self.test_user)
            
        frappe.get_doc("User", self.test_user).remove_roles("System Manager", "Agent Manager")
            
    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.delete_doc("User", self.test_user, force=True, ignore_missing=True)

    def test_unauthorized_role_update(self):
        frappe.set_user(self.test_user)
        
        frappe.flags.in_test = False

        try:
            with self.assertRaises(frappe.PermissionError):
                update_agent_role(self.test_user, "System Manager")
        finally:
            frappe.flags.in_test = True

        frappe.set_user("Administrator")
