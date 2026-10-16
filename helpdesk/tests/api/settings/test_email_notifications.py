from collections.abc import Callable

import frappe
from frappe.tests import IntegrationTestCase
from frappe.tests.utils import change_settings

from helpdesk.api.settings.email_notifications import (
    get_data,
    update_acknowledgement,
    update_reply_to_agents,
    update_reply_via_agent,
    update_share_feedback,
)
from helpdesk.helpdesk.doctype.hd_settings.helpers import get_default_email_content
from helpdesk.test_utils import (
    create_agent,
    make_agent_manager,
    make_status,
    unique_email,
    unique_name,
)

# notification name: (update function, enabled field, content field)
SIMPLE_NOTIFICATIONS: dict[str, tuple[Callable, str, str]] = {
    "acknowledgement": (
        update_acknowledgement,
        "send_acknowledgement_email",
        "acknowledgement_email_content",
    ),
    "reply_to_agents": (
        update_reply_to_agents,
        "enable_reply_email_to_agent",
        "reply_email_to_agent_content",
    ),
    "reply_via_agent": (
        update_reply_via_agent,
        "enable_reply_email_via_agent",
        "reply_via_agent_email_content",
    ),
}
FEEDBACK_FIELDS = [
    "enable_email_ticket_feedback",
    "send_email_feedback_on_status",
    "feedback_email_content",
]
CONTENT_FIELDS = [fields[2] for fields in SIMPLE_NOTIFICATIONS.values()] + [
    "feedback_email_content"
]
CUSTOM_CONTENT = "<p>Custom {{ doc.name }}</p>"


class TestEmailNotifications(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.set_user("Administrator")
        self.enterContext(
            change_settings("HD Settings", self.current_notification_settings())
        )
        self.resolved_status = make_status(unique_name("Done"), "Resolved").name

    def tearDown(self) -> None:
        frappe.set_user("Administrator")

    def test_update_saves_and_get_data_reads_it_back(self) -> None:
        for name, (
            update,
            enabled_field,
            content_field,
        ) in SIMPLE_NOTIFICATIONS.items():
            result = update(enabled=True, content=CUSTOM_CONTENT)

            self.assertEqual(result, {"enabled": True, "content": CUSTOM_CONTENT})
            self.assertEqual(self.saved(enabled_field), 1)
            self.assertEqual(self.saved(content_field), CUSTOM_CONTENT)
            data = get_data(name)
            self.assertTrue(data["enabled"])
            self.assertEqual(data["content"], CUSTOM_CONTENT)
            self.assertEqual(data["default_content"], get_default_email_content(name))

    def test_disabling_a_notification_saves_zero(self) -> None:
        for name, (update, enabled_field, _) in SIMPLE_NOTIFICATIONS.items():
            update(enabled=True, content=CUSTOM_CONTENT)
            update(enabled=False, content=CUSTOM_CONTENT)

            self.assertEqual(self.saved(enabled_field), 0)
            self.assertIs(get_data(name)["enabled"], False)

    def test_unconfigured_content_falls_back_to_default(self) -> None:
        with change_settings("HD Settings", {field: None for field in CONTENT_FIELDS}):
            for name in [*SIMPLE_NOTIFICATIONS, "share_feedback"]:
                self.assertEqual(
                    get_data(name)["content"], get_default_email_content(name)
                )

    def test_blank_content_falls_back_to_default(self) -> None:
        update_acknowledgement(enabled=True, content="   ")

        self.assertEqual(
            get_data("acknowledgement")["content"],
            get_default_email_content("acknowledgement"),
        )

    def test_invalid_template_is_rejected_and_nothing_saved(self) -> None:
        update_reply_to_agents(enabled=False, content=CUSTOM_CONTENT)

        with self.assertRaises(frappe.ValidationError):
            update_reply_to_agents(enabled=True, content="<p>{{ doc.name </p>")

        self.assertEqual(self.saved("enable_reply_email_to_agent"), 0)
        self.assertEqual(self.saved("reply_email_to_agent_content"), CUSTOM_CONTENT)

    def test_unknown_notification_is_rejected(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            get_data("unknown_notification")

    def test_share_feedback_saves_status_and_returns_it(self) -> None:
        status = {"label": self.resolved_status, "value": self.resolved_status}

        result = update_share_feedback(status, True, CUSTOM_CONTENT)

        self.assertEqual(result["ticket_status"], status)
        self.assertEqual(self.saved("enable_email_ticket_feedback"), 1)
        self.assertEqual(
            self.saved("send_email_feedback_on_status"), self.resolved_status
        )
        data = get_data("share_feedback")
        self.assertEqual(data["ticket_status"], status)
        self.assertTrue(data["enabled"])
        self.assertEqual(data["content"], CUSTOM_CONTENT)

    def test_share_feedback_status_defaults_to_closed_when_unset(self) -> None:
        with change_settings(
            "HD Settings",
            {"enable_email_ticket_feedback": 0, "send_email_feedback_on_status": None},
        ):
            data = get_data("share_feedback")

        self.assertEqual(data["ticket_status"], {"label": "Closed", "value": "Closed"})

    def test_share_feedback_rejects_status_outside_resolved_category(self) -> None:
        open_status = make_status(unique_name("Waiting"), "Open").name
        update_share_feedback(
            {"label": self.resolved_status, "value": self.resolved_status},
            False,
            CUSTOM_CONTENT,
        )

        with self.assertRaises(frappe.ValidationError):
            update_share_feedback(
                {"label": open_status, "value": open_status}, True, CUSTOM_CONTENT
            )

        self.assertEqual(self.saved("enable_email_ticket_feedback"), 0)
        self.assertEqual(
            self.saved("send_email_feedback_on_status"), self.resolved_status
        )

    def test_agent_cannot_read_notification_settings(self) -> None:
        with self.set_user(create_agent(unique_email("notify-agent")).name):
            for name in [*SIMPLE_NOTIFICATIONS, "share_feedback"]:
                with self.assertRaises(frappe.PermissionError):
                    get_data(name)

    def test_agent_cannot_update_notification_settings(self) -> None:
        before = self.current_notification_settings()

        with self.set_user(create_agent(unique_email("notify-agent")).name):
            for update, _, _ in SIMPLE_NOTIFICATIONS.values():
                with self.assertRaises(frappe.PermissionError):
                    update(enabled=True, content=CUSTOM_CONTENT)
            with self.assertRaises(frappe.PermissionError):
                update_share_feedback(
                    {"label": "Closed", "value": "Closed"}, True, CUSTOM_CONTENT
                )

        self.assertEqual(self.current_notification_settings(), before)

    def test_agent_manager_can_read_and_update_notification_settings(self) -> None:
        manager = make_agent_manager("notify-manager")

        with self.set_user(manager):
            update_acknowledgement(enabled=True, content=CUSTOM_CONTENT)
            data = get_data("acknowledgement")

        self.assertEqual(self.saved("send_acknowledgement_email"), 1)
        self.assertEqual(data["content"], CUSTOM_CONTENT)

    def current_notification_settings(self) -> dict:
        fields = [field for _, *pair in SIMPLE_NOTIFICATIONS.values() for field in pair]
        return {field: self.saved(field) for field in fields + FEEDBACK_FIELDS}

    def saved(self, field: str):
        return frappe.db.get_single_value("HD Settings", field, cache=False)
