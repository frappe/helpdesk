import csv
import io
import json

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import export_grouped_list, get_grouped_list
from helpdesk.test_utils import create_agent, make_ticket, make_todo, unique_email


class TestGroupedList(IntegrationTestCase):
    """Group By counts and exports only the tickets the list itself shows."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.agent = create_agent(unique_email("grouped")).name
        cls.subject_a = frappe.generate_hash(length=8)
        cls.subject_b = frappe.generate_hash(length=8)
        for subject in (cls.subject_a, cls.subject_a, cls.subject_b):
            make_todo(make_ticket(subject=subject).name, cls.agent)
        # same subject, but not assigned to the agent
        make_ticket(subject=cls.subject_a)
        cls.filters = [
            ["subject", "in", [cls.subject_a, cls.subject_b]],
            ["__assigned_on", "is", "set"],
        ]

    def test_groups_follow_the_assigned_on_filter(self) -> None:
        with self.set_user(self.agent):
            rows = get_grouped_list(
                "HD Ticket",
                fields=["subject", {"COUNT": "name", "as": "count"}],
                filters=self.filters,
                group_by="subject",
            )

        counts = {row.subject: row.count for row in rows}
        self.assertEqual(counts, {self.subject_a: 2, self.subject_b: 1})

    def test_pages_continue_from_limit_start(self) -> None:
        params = {
            "fields": ["subject"],
            # a string, since the filters are rewritten in place on each call
            "filters": json.dumps(self.filters),
            "group_by": "subject",
            "order_by": "subject asc",
            "limit_page_length": 1,
        }
        with self.set_user(self.agent):
            first = get_grouped_list("HD Ticket", **params)
            second = get_grouped_list("HD Ticket", limit_start=1, **params)

        subjects = [row.subject for row in first + second]
        self.assertEqual(subjects, sorted([self.subject_a, self.subject_b]))

    def test_export_has_the_same_groups(self) -> None:
        with self.set_user(self.agent):
            frappe.local.form_dict = frappe._dict(
                title="HD Ticket",
                file_format_type="CSV",
                fields=json.dumps(["subject", {"COUNT": "name", "as": "count"}]),
                group_by="subject",
                order_by="subject asc",
                view="Report",
            )
            export_grouped_list("HD Ticket", filters=json.dumps(self.filters))

        content = frappe.response["filecontent"]
        if isinstance(content, bytes):
            content = content.decode()
        rows = list(csv.DictReader(io.StringIO(content)))
        counts = {row["Subject"]: int(row["Count"]) for row in rows}
        self.assertEqual(counts, {self.subject_a: 2, self.subject_b: 1})
