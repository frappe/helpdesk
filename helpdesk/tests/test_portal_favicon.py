import frappe
from frappe.tests import IntegrationTestCase
from frappe.website.serve import get_response_content


class TestPortalHead(IntegrationTestCase):
    def setUp(self) -> None:
        # Rendering the portal commits (Studio App.get_context), so a rollback undoes nothing
        settings = frappe.db.get_value(
            "HD Settings", None, ["favicon", "brand_name"], as_dict=True
        )
        app = frappe.db.get_value(
            "Studio App", "helpdesk", ["favicon", "modified"], as_dict=True
        )
        self.addCleanup(self.restore, settings, app)

    def restore(self, settings: dict, app: dict) -> None:
        frappe.db.set_single_value("HD Settings", settings)
        frappe.db.set_value("Studio App", "helpdesk", app, update_modified=False)
        frappe.db.commit()
        frappe.clear_document_cache("Studio App", "helpdesk")

    def render_portal(self) -> str:
        frappe.set_user("Guest")
        try:
            return get_response_content("help")
        finally:
            frappe.set_user("Administrator")

    def test_portal_uses_the_desk_brand(self) -> None:
        frappe.db.set_single_value(
            "HD Settings", {"favicon": "/files/hd-favicon.png", "brand_name": "Acme"}
        )
        html = self.render_portal()
        self.assertIn('rel="icon" href="/files/hd-favicon.png"', html)
        self.assertIn("<title>Acme</title>", html)
        self.assertIn('"brand_name": "Acme"', html)

    def test_studio_app_favicon_wins(self) -> None:
        frappe.db.set_single_value("HD Settings", "favicon", "/files/hd-favicon.png")
        frappe.db.set_value(
            "Studio App",
            "helpdesk",
            "favicon",
            "/files/studio.png",
            update_modified=False,
        )
        frappe.clear_document_cache("Studio App", "helpdesk")
        self.assertIn('rel="icon" href="/files/studio.png"', self.render_portal())
