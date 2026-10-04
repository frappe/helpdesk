import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.doc import get_filterable_fields, get_quick_filters, sort_options
from helpdesk.test_utils import create_agent, create_contact, create_user, unique_email

AGENT_ONLY_FIELDS = {"_assign", "_user_tags", "agent_group", "ticket_type", "contact"}


class FieldPersonas(IntegrationTestCase):
    """An agent and a customer, created once per test class."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.agent = create_agent(unique_email("doc-fields-agent")).name
        cls.customer = create_contact("DocFields", unique_email("doc-fields"))["user"]


class TestFilterableFields(FieldPersonas):
    """The filter picker lists what `get_filterable_fields` returns."""

    def test_agent_gets_ticket_and_pseudo_fields(self) -> None:
        with self.set_user(self.agent):
            fields = self.fieldnames(get_filterable_fields("HD Ticket"))

        for field in ("subject", "agent_group", "_assign", "_user_tags", "owner"):
            self.assertIn(field, fields)
        self.assertIn("__assigned_on", fields)
        self.assertNotIn("service_level_agreement_creation", fields)
        self.assertEqual(len(fields), len(set(fields)))

    def test_customer_gets_only_portal_fields(self) -> None:
        with self.set_user(self.customer):
            fields = self.fieldnames(get_filterable_fields("HD Ticket", True))

        self.assertIn("subject", fields)
        self.assertIn("status", fields)
        self.assertFalse(AGENT_ONLY_FIELDS & set(fields))

    def test_team_restriction_hides_team_unless_ignored(self) -> None:
        with change_settings("HD Settings", {"restrict_tickets_by_agent_group": 1}):
            with self.set_user(self.agent):
                restricted = self.fieldnames(get_filterable_fields("HD Ticket"))
                unrestricted = self.fieldnames(
                    get_filterable_fields("HD Ticket", ignore_team_restrictions=True)
                )

        self.assertNotIn("agent_group", restricted)
        self.assertIn("agent_group", unrestricted)

    def test_user_without_read_access_is_refused_even_when_cached(self) -> None:
        get_filterable_fields("HD Agent")
        outsider = create_user(unique_email("doc-fields-outsider")).name

        with self.set_user(outsider):
            with self.assertRaises(frappe.PermissionError):
                get_filterable_fields("HD Agent")

    def fieldnames(self, fields: list[dict]) -> list[str]:
        return [field["fieldname"] for field in fields]


class TestSortOptions(FieldPersonas):
    def test_agent_can_sort_by_any_labelled_field(self) -> None:
        with self.set_user(self.agent):
            values = self.values(sort_options("HD Ticket"))

        for field in ("subject", "agent_group", "priority", "modified", "owner"):
            self.assertIn(field, values)

    def test_customer_sorts_only_by_portal_fields(self) -> None:
        with self.set_user(self.customer):
            values = self.values(sort_options("HD Ticket", True))

        self.assertIn("subject", values)
        self.assertIn("modified", values)
        self.assertFalse(AGENT_ONLY_FIELDS & set(values))

    def values(self, options: list[dict]) -> list[str]:
        return [option["value"] for option in options]


class TestQuickFilters(FieldPersonas):
    def test_agent_ticket_quick_filters(self) -> None:
        with self.set_user(self.agent):
            names = self.names(get_quick_filters("HD Ticket"))

        self.assertEqual(names[:1], ["name"])
        self.assertIn("subject", names)
        self.assertIn("customer", names)

    def test_customer_ticket_quick_filters_drop_customer(self) -> None:
        with self.set_user(self.customer):
            names = self.names(get_quick_filters("HD Ticket", True))

        self.assertIn("subject", names)
        self.assertNotIn("customer", names)

    def test_select_filter_starts_with_an_empty_option(self) -> None:
        with self.set_user(self.agent):
            filters = get_quick_filters("HD Article")

        status = next(f for f in filters if f["name"] == "status")
        self.assertEqual(status["options"][0], {"label": "", "value": ""})
        self.assertIn({"label": "Draft", "value": "Draft"}, status["options"])
        self.assertNotIn("name", self.names(filters))

    def test_contact_offers_only_the_id_filter(self) -> None:
        with self.set_user(self.agent):
            self.assertEqual(self.names(get_quick_filters("Contact")), ["name"])

    def names(self, filters: list[dict]) -> list[str]:
        return [f["name"] for f in filters]
