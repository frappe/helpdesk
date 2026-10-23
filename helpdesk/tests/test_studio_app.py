from frappe.tests import UnitTestCase

from helpdesk.helpdesk.hooks.studio_app import escape_for_shell


class TestPageShell(UnitTestCase):
    def test_a_brand_name_cannot_break_out_of_the_shell(self) -> None:
        # renderer.html prints it in <title> and inside a JS string
        escaped = escape_for_shell('Acme "Help" </title><script>\\\nx')
        for unsafe in ('"', "<", ">", "\\", "\n"):
            self.assertNotIn(unsafe, escaped)

    def test_an_empty_value_stays_empty(self) -> None:
        self.assertEqual(escape_for_shell(None), "")
