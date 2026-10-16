import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.doc import get_list_data
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket
from helpdesk.test_utils import (
    create_agent,
    create_contact,
    delete_default_views,
    make_article,
    make_default_view,
    make_ticket,
    unique_email,
)

PORTAL_FIELDS = {
    "name",
    "subject",
    "status",
    "priority",
    "response_by",
    "resolution_by",
    "creation",
}


class TestGetListData(IntegrationTestCase):
    """`get_list_data` feeds every desk and portal list through ListViewBuilder."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.token = frappe.generate_hash(length=8)
        cls.agent = create_agent(unique_email("doc-list-agent")).name
        cls.customer = create_contact("DocList", unique_email("doc-list"))
        other = create_contact("DocListOther", unique_email("doc-other"))
        cls.tickets = {
            suffix: make_ticket(subject=f"{cls.token} {suffix}").name
            for suffix in ("a", "b", "c")
        }
        cls.own_ticket = make_ticket(
            subject=f"{cls.token} own", raised_by=cls.customer["user"]
        ).name
        cls.other_ticket = make_ticket(
            subject=f"{cls.token} other", raised_by=other["user"]
        ).name

    def test_filters_sort_and_pagination(self) -> None:
        with self.set_user(self.agent):
            result = get_list_data(
                "HD Ticket",
                filters=[["name", "in", list(self.tickets.values())]],
                order_by="subject asc",
                page_length=2,
            )

        names = [row.name for row in result["data"]]
        self.assertEqual(names, [self.tickets["a"], self.tickets["b"]])
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["total_count"], 3)

    def test_empty_filters_list_everything(self) -> None:
        for empty in ({}, []):
            with self.subTest(filters=empty), self.set_user(self.agent):
                result = get_list_data("HD Ticket", filters=empty, page_length=1)
            self.assertEqual(result["row_count"], 1)
            self.assertGreaterEqual(result["total_count"], 5)

    def test_at_me_filter_resolves_to_session_user(self) -> None:
        filters = [["owner", "=", "@me"], *self.subject_filter(self.token)]

        result = get_list_data("HD Ticket", filters=filters)

        self.assertEqual(result["total_count"], 5)

    def test_custom_columns_are_fetched_as_rows(self) -> None:
        columns = [{"label": "Priority", "type": "Link", "key": "priority"}]
        view = {"view_type": "list", "group_by_field": "agent_group"}

        with self.set_user(self.agent):
            result = get_list_data(
                "HD Ticket",
                filters=self.subject_filter(self.token),
                columns=columns,
                rows=["subject"],
                view=view,
            )

        self.assertEqual(result["columns"], columns)
        row = result["data"][0]
        for field in ("name", "subject", "priority", "agent_group", "_seen", "sla"):
            self.assertIn(field, row)

    def test_agent_default_columns_without_saved_view(self) -> None:
        delete_default_views(self.agent)

        with self.set_user(self.agent):
            result = get_list_data(
                "HD Ticket", filters=self.subject_filter(self.token), is_default=True
            )

        self.assertEqual(result["columns"], HDTicket.default_list_data()["columns"])
        self.assertIn("_assign", result["data"][0])
        self.assertIn("agent_group", {f["value"] for f in result["fields"]})

    def test_customer_gets_portal_columns_and_fields(self) -> None:
        delete_default_views(self.customer["user"])

        with self.set_user(self.customer["user"]):
            result = get_list_data(
                "HD Ticket", is_default=True, show_customer_portal_fields=True
            )

        portal_columns = HDTicket.default_list_data(True)["columns"]
        self.assertEqual(result["columns"], portal_columns)
        self.assertLessEqual({f["value"] for f in result["fields"]}, PORTAL_FIELDS)

    def test_customer_sees_only_own_tickets(self) -> None:
        with self.set_user(self.customer["user"]):
            result = get_list_data(
                "HD Ticket",
                filters=self.subject_filter(self.token),
                show_customer_portal_fields=True,
            )

        self.assertEqual([row.name for row in result["data"]], [self.own_ticket])
        self.assertEqual(result["total_count"], 1)

    def test_default_view_supplies_columns_and_rows(self) -> None:
        columns = [{"label": "Subject", "type": "Data", "key": "subject"}]
        make_default_view(self.agent, columns=columns, rows=["ticket_type"])

        with self.set_user(self.agent):
            result = get_list_data(
                "HD Ticket", filters=self.subject_filter(self.token), is_default=True
            )

        self.assertEqual(result["columns"], columns)
        self.assertIn("ticket_type", result["data"][0])

    def test_default_view_without_columns_falls_back_to_defaults(self) -> None:
        make_default_view(self.agent, columns=[], rows=[])

        with self.set_user(self.agent):
            result = get_list_data(
                "HD Ticket", filters=self.subject_filter(self.token), is_default=True
            )

        self.assertEqual(result["columns"], HDTicket.default_list_data()["columns"])
        self.assertIn("resolution_date", result["rows"])

    def test_default_filters_apply_only_without_filters(self) -> None:
        make_default_view(self.agent)
        default_filters = {"subject": ["like", f"{self.token} a"]}

        with self.set_user(self.agent):
            unfiltered = self.list_default(default_filters, filters=[])
            filtered = self.list_default(
                default_filters, self.subject_filter(f"{self.token} b")
            )

        self.assertEqual([row.name for row in unfiltered["data"]], [self.tickets["a"]])
        self.assertEqual([row.name for row in filtered["data"]], [self.tickets["b"]])

    def test_default_filters_resolve_at_me(self) -> None:
        make_default_view(self.customer["user"])

        with self.set_user(self.customer["user"]):
            result = self.list_default({"raised_by": "@me"}, filters=[])

        self.assertEqual([row.name for row in result["data"]], [self.own_ticket])

    def list_default(self, default_filters: dict, filters: list) -> dict:
        return get_list_data(
            "HD Ticket",
            filters=filters,
            default_filters=default_filters,
            is_default=True,
        )

    def subject_filter(self, text: str) -> list:
        return [["subject", "like", f"%{text}%"]]


class TestGroupByView(IntegrationTestCase):
    """The knowledge base groups articles by category through a group_by view."""

    VIEW = {
        "view_type": "group_by",
        "group_by_field": "category",
        "label_doc": "HD Article Category",
        "label_field": "category_name",
    }

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.token = frappe.generate_hash(length=8)
        categories = [
            frappe.get_doc({"doctype": "HD Article Category", "category_name": label})
            .insert(ignore_permissions=True)
            .name
            for label in ("Zeta", "Alpha")
        ]
        general = {"category_name": "General"}
        categories += [frappe.db.get_value("HD Article Category", general), None]
        for category in categories:
            make_article(f"{cls.token} {category}", "Draft", category)

    def test_categories_sorted_by_label_with_general_first(self) -> None:
        options = self.group_options(order_by="modified desc")

        self.assertEqual(
            [o["label"] for o in options], ["General", "", "Alpha", "Zeta"]
        )

    def test_descending_sort_on_group_field_keeps_general_first(self) -> None:
        options = self.group_options(order_by="category desc")

        self.assertEqual(
            [o["label"] for o in options], ["General", "Zeta", "Alpha", ""]
        )

    def test_select_field_groups_by_its_options(self) -> None:
        view = {"view_type": "group_by", "group_by_field": "status"}

        result = get_list_data("HD Article", filters=self.title_filter(), view=view)

        options = result["group_by_field"]["options"]
        self.assertEqual(options, ["Published", "Draft", "Archived"])

    def group_options(self, order_by: str) -> list[dict]:
        result = get_list_data(
            "HD Article", filters=self.title_filter(), order_by=order_by, view=self.VIEW
        )
        self.assertEqual(result["view_type"], "group_by")
        self.assertEqual(result["group_by_field"]["name"], "category")
        return result["group_by_field"]["options"]

    def title_filter(self) -> list:
        return [["title", "like", f"{self.token}%"]]
