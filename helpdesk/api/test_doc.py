import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.doc import get_list_data


class TestGetListData(FrappeTestCase):
    original_user = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_user = frappe.session.user

    def tearDown(self):
        frappe.set_user(self.original_user or "Administrator")

    def test_kanban_view_expands_select_group_by_field(self):
        """For a kanban view on a Select field the response must expose
        group_by_field as {name, options:[{label,value}, ...]} so the
        Vue renderer can build columns."""
        res = get_list_data(
            doctype="HD Ticket",
            view={
                "name": None,
                "view_type": "kanban",
                "group_by_field": "status",
            },
        )
        self.assertEqual(res.get("view_type"), "kanban")
        gbf = res.get("group_by_field")
        self.assertIsInstance(gbf, dict)
        self.assertEqual(gbf.get("name"), "status")
        options = gbf.get("options")
        self.assertIsInstance(options, list)
        self.assertGreater(len(options), 0)
        first = options[0]
        self.assertIn("label", first)
        self.assertIn("value", first)

    def test_group_by_view_expands_select_group_by_field(self):
        """The same Select-options normalisation applies to the existing
        group_by view type, so the list and kanban renderers can share
        the data shape."""
        res = get_list_data(
            doctype="HD Ticket",
            view={
                "name": None,
                "view_type": "group_by",
                "group_by_field": "status",
            },
        )
        self.assertEqual(res.get("view_type"), "group_by")
        gbf = res.get("group_by_field")
        self.assertIsInstance(gbf, dict)
        self.assertIsInstance(gbf.get("options"), list)
        for opt in gbf["options"]:
            self.assertIsInstance(opt, dict)
            self.assertIn("value", opt)
            self.assertIn("label", opt)

    def test_list_view_leaves_group_by_field_alone(self):
        """A plain list view must not expand group_by_field — the field
        stays whatever the caller passed in (string or None)."""
        res = get_list_data(
            doctype="HD Ticket",
            view={
                "name": None,
                "view_type": "list",
                "group_by_field": "status",
            },
        )
        self.assertEqual(res.get("view_type"), "list")
        self.assertEqual(res.get("group_by_field"), "status")

    def test_kanban_shows_empty_swim_lanes_for_select(self):
        """Kanban columns must come from the field schema, not the data,
        so a status with zero tickets still gets a column."""
        res = get_list_data(
            doctype="HD Ticket",
            view={
                "name": None,
                "view_type": "kanban",
                "group_by_field": "status",
            },
        )
        gbf = res.get("group_by_field")
        values = [o.get("value") for o in gbf.get("options") or []]
        # All non-empty schema options must be present, even those with
        # zero matching tickets in `data`.
        meta = frappe.get_meta("HD Ticket")
        status_field = next(f for f in meta.fields if f.fieldname == "status")
        schema_values = [
            v.strip()
            for v in (status_field.options or "").split("\n")
            if v and v.strip()
        ]
        for v in schema_values:
            self.assertIn(v, values, f"Status '{v}' is missing from kanban columns")
        # No phantom empty-string column from a leading "\n" in the schema
        self.assertNotIn("", values)

    def test_kanban_link_field_returns_all_linked_records(self):
        """For a Link group_by_field in kanban mode, every record of the
        linked doctype should produce a column — empty swim lanes are
        important for drag-and-drop targeting."""
        res = get_list_data(
            doctype="HD Ticket",
            view={
                "name": None,
                "view_type": "kanban",
                "group_by_field": "priority",
            },
        )
        gbf = res.get("group_by_field")
        self.assertIsInstance(gbf, dict)
        column_values = {o.get("value") for o in gbf.get("options") or []}
        priorities = {
            p["name"] for p in frappe.get_all("HD Ticket Priority", fields=["name"])
        }
        # Every defined priority shows up as a column, regardless of usage
        self.assertEqual(column_values, priorities)
