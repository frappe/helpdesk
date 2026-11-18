import importlib.util
from pathlib import Path

from frappe.tests import IntegrationTestCase

SCRIPT = Path(__file__).parents[2] / ".github" / "scripts" / "stamp_whats_new.py"


def load_script():
    spec = importlib.util.spec_from_file_location("stamp_whats_new", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UNRELEASED = "---\ntitle: Thing\nversion: unreleased\n---\nBody: **kept**\n"


class TestStampWhatsNew(IntegrationTestCase):
    def setUp(self) -> None:
        self.stamp = load_script().stamp

    def test_unreleased_note_gets_version_and_date(self) -> None:
        self.assertEqual(
            self.stamp(UNRELEASED, "1.4.0", "2026-03-05"),
            "---\ntitle: Thing\nversion: 1.4.0\ndate: 2026-03-05\n---\nBody: **kept**\n",
        )

    def test_released_note_is_left_alone(self) -> None:
        released = UNRELEASED.replace("unreleased", "1.0.0")
        self.assertIsNone(self.stamp(released, "1.4.0", "2026-03-05"))

    def test_existing_date_is_replaced(self) -> None:
        text = UNRELEASED.replace("---\nBody", "date: 2020-01-01\n---\nBody")
        stamped = self.stamp(text, "1.4.0", "2026-03-05")
        self.assertEqual(stamped.count("date:"), 1)
        self.assertIn("date: 2026-03-05", stamped)

    def test_text_without_frontmatter_is_left_alone(self) -> None:
        self.assertIsNone(self.stamp("version: unreleased\n", "1.4.0", "2026-03-05"))
