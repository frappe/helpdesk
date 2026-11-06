# Copyright (c) 2025, Frappe Technologies and Contributors
# See license.txt

import csv
import io

import frappe
from frappe.desk.reportview import export_query
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import (
    create_contact,
    create_customer,
    make_organization,
    make_ticket,
    unique_email,
    unique_name,
)


class TestTicketExport(IntegrationTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.customer, cls.owner, cls.manager, cls.member = make_organization("Export")
        cls.outsider = create_contact(
            "Export Outsider", unique_email("export-outsider")
        )
        cls.other_customer = create_customer(
            unique_name("Test Other Export"),
            [{"contact_name": cls.outsider["contact"]}],
        )
        cls.member_ticket = cls.raise_ticket(cls.member, cls.customer.name)
        cls.owner_ticket = cls.raise_ticket(cls.owner, cls.customer.name)
        cls.outsider_ticket = cls.raise_ticket(cls.outsider, cls.other_customer.name)

    @staticmethod
    def raise_ticket(contact: dict, customer: str) -> str:
        ticket = make_ticket(raised_by=contact["user"], customer=customer)
        ticket.db_set("customer", customer, update_modified=False)
        return ticket.name

    def exported(self, user: str) -> set[str]:
        with self.set_user(user):
            # set after switching user, which resets the request
            frappe.local.form_dict = frappe._dict(
                doctype="HD Ticket",
                file_format_type="CSV",
                fields='["name"]',
                filters="[]",
            )
            export_query()
        rows = list(csv.reader(io.StringIO(frappe.response["filecontent"].decode())))
        # the export adds a serial number before and the owner after the asked fields
        return {row[1] for row in rows[1:]}

    def test_a_member_exports_only_their_own_tickets(self) -> None:
        exported = self.exported(self.member["user"])
        self.assertIn(self.member_ticket, exported)
        self.assertNotIn(self.owner_ticket, exported)
        self.assertNotIn(self.outsider_ticket, exported)

    def test_a_manager_exports_only_their_organizations_tickets(self) -> None:
        exported = self.exported(self.manager["user"])
        self.assertIn(self.member_ticket, exported)
        self.assertIn(self.owner_ticket, exported)
        self.assertNotIn(self.outsider_ticket, exported)
