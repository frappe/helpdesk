import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.doc import (
    get_list_data,
    handle_assigned_on_filter,
    handle_at_me_support,
    remove_assignments,
)
from helpdesk.test_utils import create_agent, create_contact, make_team, make_ticket

ASSIGNED_AT = {
    "day_before": "2026-01-04 23:59:59",
    "midnight": "2026-01-05 00:00:00",
    "evening": "2026-01-05 18:30:00",
    "day_after": "2026-01-06 09:00:00",
}


def assign(ticket: str, user: str, at: str | None = None) -> str:
    """Open a ToDo for `user` on `ticket`, optionally backdated to `at`."""
    todo = frappe.get_doc(
        {
            "doctype": "ToDo",
            "allocated_to": user,
            "reference_type": "HD Ticket",
            "reference_name": ticket,
            "description": "Assigned in test",
        }
    ).insert(ignore_permissions=True)
    if at:
        frappe.db.set_value("ToDo", todo.name, "creation", at, update_modified=False)
    return todo.name


def unique_email(prefix: str) -> str:
    return f"{prefix}-{frappe.generate_hash(length=8)}@example.com"


class TestAtMeSupport(IntegrationTestCase):
    """`@me` in a saved or typed filter means whoever is looking at the list."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.agent = create_agent(unique_email("at-me")).name

    def test_list_conditions_replace_every_at_me(self) -> None:
        filters = [
            ["owner", "=", "@me"],
            ["_assign", "like", "%@me%"],
            ["HD Ticket", "raised_by", "=", "@me"],
            ["owner", "in", ["x@example.com", "@me", "@me"]],
            ["status", "=", "Open"],
            [],
        ]

        with self.set_user(self.agent):
            handle_at_me_support(filters)

        me = self.agent
        self.assertEqual(
            filters,
            [
                ["owner", "=", me],
                ["_assign", "like", f"%{me}%"],
                ["HD Ticket", "raised_by", "=", me],
                ["owner", "in", ["x@example.com", me, me]],
                ["status", "=", "Open"],
                [],
            ],
        )

    def test_dict_filters_replace_nested_at_me(self) -> None:
        filters = {
            "owner": "@me",
            "_assign": ["like", "%@me%"],
            "raised_by": ["in", ["@me", "x@example.com"]],
        }

        with self.set_user(self.agent):
            handle_at_me_support(filters)

        me = self.agent
        self.assertEqual(filters["owner"], me)
        self.assertEqual(filters["_assign"], ["like", f"%{me}%"])
        self.assertEqual(filters["raised_by"], ["in", [me, "x@example.com"]])


class TestAssignedOnFilter(IntegrationTestCase):
    """The "Assigned on" Date filter matches the session user's open ToDos."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.agent = create_agent(unique_email("assigned-on")).name
        cls.tickets = {}
        for label, at in ASSIGNED_AT.items():
            cls.tickets[label] = make_ticket(subject=f"Assigned on {label}").name
            assign(cls.tickets[label], cls.agent, at)

    def test_each_operator_treats_the_value_as_a_whole_day(self) -> None:
        cases = [
            ("=", "2026-01-05", {"midnight", "evening"}),
            ("!=", "2026-01-05", {"day_before", "day_after"}),
            (">", "2026-01-05", {"day_after"}),
            ("<", "2026-01-05", {"day_before"}),
            (">=", "2026-01-05", {"midnight", "evening", "day_after"}),
            ("<=", "2026-01-05", {"day_before", "midnight", "evening"}),
            ("between", ["2026-01-04", "2026-01-05"], set(ASSIGNED_AT) - {"day_after"}),
            ("is", "set", set(ASSIGNED_AT)),
            ("is", "not set", set()),
        ]
        for operator, value, expected in cases:
            with self.subTest(operator=operator, value=value):
                self.assertEqual(self.matches(operator, value), expected)

    def test_timespan_covers_the_full_system_day(self) -> None:
        with self.freeze_time("2026-01-05 23:59:00"):
            self.assertEqual(self.matches("timespan", "today"), {"midnight", "evening"})
            self.assertEqual(self.matches("timespan", "yesterday"), {"day_before"})

    def test_dict_filters_default_to_equals(self) -> None:
        filters = {"__assigned_on": "2026-01-05"}

        with self.set_user(self.agent):
            handle_assigned_on_filter(filters, "HD Ticket")

        self.assertNotIn("__assigned_on", filters)
        self.assertEqual(self.labels(filters["name"][1]), {"midnight", "evening"})

    def test_only_own_open_assignments_count(self) -> None:
        other_agent = create_agent(unique_email("assigned-on-other")).name
        ticket = make_ticket(subject="Assigned to someone else").name
        assign(ticket, other_agent, ASSIGNED_AT["evening"])
        cancelled = assign(ticket, self.agent, ASSIGNED_AT["evening"])
        frappe.db.set_value("ToDo", cancelled, "status", "Cancelled")

        self.assertNotIn(ticket, self.matching_names("=", "2026-01-05"))

    def test_no_match_lists_no_tickets(self) -> None:
        with self.set_user(self.agent):
            result = get_list_data(
                "HD Ticket", filters=[["__assigned_on", "=", "2020-01-01"]]
            )

        self.assertEqual(result["data"], [])
        self.assertEqual(result["total_count"], 0)

    def test_intersects_an_existing_name_in_filter(self) -> None:
        keep = [self.tickets["midnight"], self.tickets["day_before"]]
        list_filters = [
            ["name", "in", list(keep)],
            ["__assigned_on", "=", "2026-01-05"],
        ]
        dict_filters = {
            "name": ["in", list(keep)],
            "__assigned_on": ["=", "2026-01-05"],
        }

        with self.set_user(self.agent):
            handle_assigned_on_filter(list_filters, "HD Ticket")
            handle_assigned_on_filter(dict_filters, "HD Ticket")

        self.assertEqual(list_filters, [["name", "in", [self.tickets["midnight"]]]])
        self.assertEqual(dict_filters["name"], ["in", [self.tickets["midnight"]]])

    def matches(self, operator: str, value: str | list) -> set[str]:
        return self.labels(self.matching_names(operator, value))

    def matching_names(self, operator: str, value: str | list) -> list[str]:
        filters = [["__assigned_on", operator, value]]
        with self.set_user(self.agent):
            handle_assigned_on_filter(filters, "HD Ticket")
        return filters[0][2]

    def labels(self, names: list[str]) -> set[str]:
        by_name = {name: label for label, name in self.tickets.items()}
        return {by_name[name] for name in names if name in by_name}


class TestRemoveAssignments(IntegrationTestCase):
    """The assignee popover sends removed agents to `remove_assignments`."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.agent = create_agent(unique_email("unassigning")).name
        cls.assignee = create_agent(unique_email("assignee")).name
        cls.customer = create_contact("Unassign", unique_email("unassign-customer"))

    def setUp(self) -> None:
        self.ticket = make_ticket(raised_by=self.customer["user"]).name
        self.todo = assign(self.ticket, self.assignee)

    def test_agent_removes_assignment(self) -> None:
        with self.set_user(self.agent):
            remove_assignments("HD Ticket", self.ticket, [self.assignee])

        self.assertEqual(frappe.db.get_value("ToDo", self.todo, "status"), "Cancelled")
        assigned = frappe.db.get_value("HD Ticket", self.ticket, "_assign")
        self.assertNotIn(self.assignee, frappe.parse_json(assigned or "[]"))

    def test_admin_removes_assignment(self) -> None:
        remove_assignments("HD Ticket", self.ticket, [self.assignee])

        self.assertEqual(frappe.db.get_value("ToDo", self.todo, "status"), "Cancelled")

    def test_empty_assignees_change_nothing(self) -> None:
        with self.set_user(self.agent):
            self.assertIsNone(remove_assignments("HD Ticket", self.ticket, []))

        self.assertEqual(frappe.db.get_value("ToDo", self.todo, "status"), "Open")

    def test_customer_cannot_remove_assignments(self) -> None:
        with self.set_user(self.customer["user"]):
            with self.assertRaises(frappe.PermissionError):
                remove_assignments("HD Ticket", self.ticket, [self.assignee])

        self.assertEqual(frappe.db.get_value("ToDo", self.todo, "status"), "Open")

    def test_agent_outside_the_team_cannot_remove_assignments(self) -> None:
        team = make_team(f"Unassign {frappe.generate_hash(length=6)}", [self.assignee])
        frappe.db.set_value("HD Ticket", self.ticket, "agent_group", team.name)

        with change_settings("HD Settings", {"restrict_tickets_by_agent_group": 1}):
            with self.set_user(self.agent):
                with self.assertRaises(frappe.PermissionError):
                    remove_assignments("HD Ticket", self.ticket, [self.assignee])

        self.assertEqual(frappe.db.get_value("ToDo", self.todo, "status"), "Open")
