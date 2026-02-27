# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import remove_assignments


class TestDocAPI(IntegrationTestCase):
    def test_remove_assignments_strict_parameters(self):

        with self.assertRaises(TypeError):
            remove_assignments(
                doctype="HD Ticket",
                name="TIC-001",
                assignees="[]",
                ignore_permissions=True,
            )
