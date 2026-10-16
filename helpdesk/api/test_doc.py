# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.doc import get_list_data
from helpdesk.test_utils import create_contact, make_ticket


class TestGetListData(FrappeTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")

    def test_get_list_data_contact_display(self) -> None:
        contact1 = create_contact("Anna Latos", "anna.latos@example.com", user=False)
        contact2 = create_contact("Ravi Kumar", "ravi.kumar@example.com", user=False)

        ticket1 = make_ticket(subject="Machine Repair", contact=contact1["contact"])
        ticket2 = make_ticket(subject="Sewing Machine Service", contact=contact2["contact"])
        ticket3 = make_ticket(subject="Motor Issue")  # Ticket without contact

        res = get_list_data(
            doctype="HD Ticket",
            rows=["name", "subject", "contact", "status"],
            page_length=50,
        )

        data = res.get("data", [])
        ticket_map = {d["name"]: d for d in data}

        self.assertIn(ticket1.name, ticket_map)
        self.assertIn(ticket2.name, ticket_map)

        # Check contact (original ID) vs contact_display (full_name)
        t1_data = ticket_map[ticket1.name]
        self.assertEqual(t1_data.get("contact"), contact1["contact"])
        self.assertEqual(t1_data.get("contact_display"), "Anna Latos")

        t2_data = ticket_map[ticket2.name]
        self.assertEqual(t2_data.get("contact"), contact2["contact"])
        self.assertEqual(t2_data.get("contact_display"), "Ravi Kumar")

        # Ticket without contact should not fail and have empty/falsy contact_display
        if ticket3.name in ticket_map:
            t3_data = ticket_map[ticket3.name]
            self.assertEqual(t3_data.get("contact_display"), "")
