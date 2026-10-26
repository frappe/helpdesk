import importlib
import pkgutil
import sys
import unittest
from contextlib import contextmanager
from typing import Iterator
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.helpdesk.doctype.hd_ticket.api import get_one, merge_ticket, split_ticket
from helpdesk.integrations.whatsapp.api import get_conversation, get_messages
from helpdesk.integrations.whatsapp.setup import (
    WHATSAPP_APP,
    add_whatsapp_source,
    before_app_uninstall,
    setup_whatsapp,
)
from helpdesk.integrations.whatsapp.test_utils import (
    make_whatsapp_account,
    mock_meta,
    receive_message,
    requires_whatsapp,
)
from helpdesk.test_utils import make_ticket

SETUP = "helpdesk.integrations.whatsapp.setup"
PACKAGE = "helpdesk.integrations.whatsapp"


@contextmanager
def fresh_test_modules() -> Iterator[None]:
    """Re-import the WhatsApp test modules from scratch, putting the loaded ones back afterwards."""
    loaded = {
        name: module
        for name, module in sys.modules.items()
        if name.startswith(f"{PACKAGE}.test")
    }
    with patch.dict(sys.modules):
        for name in loaded:
            del sys.modules[name]
        yield
    for name, module in loaded.items():
        parent, child = name.rsplit(".", 1)
        setattr(sys.modules[parent], child, module)


@contextmanager
def without_whatsapp() -> Iterator[None]:
    """Pretend the whatsapp app is not installed: gone from the app list, its doc events unhooked."""
    apps = [app for app in frappe.get_installed_apps() if app != WHATSAPP_APP]
    hooks = {
        doctype: {
            event: [m for m in methods if not m.startswith(f"{WHATSAPP_APP}.")]
            for event, methods in events.items()
        }
        for doctype, events in frappe.get_doc_hooks().items()
    }
    with (
        patch("frappe.get_installed_apps", return_value=apps),
        patch.object(frappe.local, "doc_events_hooks", hooks),
    ):
        yield


class TestWithoutWhatsApp(IntegrationTestCase):
    """Helpdesk on a site without the whatsapp app, or after it was uninstalled."""

    def setUp(self) -> None:
        self.enterContext(mock_meta())

    def tearDown(self) -> None:
        frappe.set_user("Administrator")
        frappe.db.rollback()
        frappe.clear_cache(doctype="HD Ticket")

    def test_install_hooks_are_no_ops_and_sources_stay_email_and_portal(self) -> None:
        frappe.db.delete(
            "Property Setter", {"doc_type": "HD Ticket", "field_name": "source"}
        )
        frappe.clear_cache(doctype="HD Ticket")
        with (
            without_whatsapp(),
            patch("frappe.db.add_index") as add_index,
            patch(f"{SETUP}.add_permission") as add_permission,
        ):
            setup_whatsapp()
            setup_whatsapp("helpdesk")
        add_index.assert_not_called()
        add_permission.assert_not_called()
        options = frappe.get_meta("HD Ticket").get_field("source").options
        self.assertEqual(options.split("\n"), ["Email", "Portal"])

    def test_test_modules_import_and_skip_without_the_app(self) -> None:
        blocked = {
            name: None for name in sys.modules if name.split(".")[0] == WHATSAPP_APP
        }
        with fresh_test_modules(), without_whatsapp(), patch.dict(sys.modules, blocked):
            running = {
                test_class.__name__
                for test_class in whatsapp_test_classes()
                if not getattr(test_class, "__unittest_skip__", False)
            }
        self.assertEqual(running, {"TestWithoutWhatsApp", "TestWhatsAppFormatting"})

    @requires_whatsapp
    def test_whatsapp_uninstall_is_refused_while_whatsapp_tickets_exist(self) -> None:
        self.assertIn(
            f"{SETUP}.before_app_uninstall", frappe.get_hooks("before_app_uninstall")
        )
        frappe.db.delete("HD Ticket", {"source": "WhatsApp"})
        add_whatsapp_source()
        message = receive_message("919800000202", "Hi", make_whatsapp_account())
        before_app_uninstall("erpnext")
        with self.assertRaisesRegex(
            frappe.ValidationError, r"^Delete the WhatsApp tickets first \(1 left\)"
        ):
            before_app_uninstall(WHATSAPP_APP)
        self.assertIn("WhatsApp", source_options())

        frappe.delete_doc("HD Ticket", message.reference_docname)
        before_app_uninstall(WHATSAPP_APP)
        self.assertEqual(source_options(), ["Email", "Portal"])
        self.assertFalse(
            frappe.db.exists(
                "Property Setter",
                {
                    "doc_type": "HD Ticket",
                    "field_name": "source",
                    "property": "options",
                },
            )
        )

    def test_add_source_waits_for_the_source_field(self) -> None:
        meta = MagicMock()
        meta.get_field.return_value = None
        with (
            patch(f"{SETUP}.frappe.get_meta", return_value=meta),
            patch(f"{SETUP}.make_property_setter") as make_property_setter,
        ):
            add_whatsapp_source()
        make_property_setter.assert_not_called()

    def test_email_tickets_merge_split_and_report_whatsapp_off(self) -> None:
        source = make_ticket(description="Without WhatsApp source")
        target = make_ticket(description="Without WhatsApp target")
        with without_whatsapp():
            self.assertFalse(get_one(target.name)["is_whatsapp"])
            communication = frappe.get_all(
                "Communication",
                {"reference_doctype": "HD Ticket", "reference_name": target.name},
                pluck="name",
            )[0]
            split = split_ticket(subject="Split", communication_id=communication)
            merge_ticket(source=source.name, target=target.name)
        self.assertTrue(frappe.db.exists("HD Ticket", split))
        self.assertEqual(
            frappe.db.get_value("HD Ticket", source.name, "merged_with"), target.name
        )

    @requires_whatsapp
    def test_whatsapp_ticket_after_uninstall_is_read_only_and_empty(self) -> None:
        message = receive_message(
            "919800000201", "Still there?", make_whatsapp_account()
        )
        ticket = message.reference_docname
        with without_whatsapp():
            self.assertTrue(get_one(ticket)["is_whatsapp"])
            self.assertEqual(
                get_messages(ticket),
                {
                    "installed": False,
                    "messages": [],
                    "reply_window_open": False,
                    "business_number": None,
                },
            )
            self.assertEqual(
                get_conversation(ticket),
                {
                    "installed": False,
                    "to": None,
                    "reply_window_open": False,
                    "reply_window_closes_at": None,
                    "business_number": None,
                    "templates": [],
                },
            )
        self.assertTrue(get_conversation(ticket)["installed"])


def whatsapp_test_classes() -> list[type]:
    """Every test class in the WhatsApp test package, freshly imported."""
    package = importlib.import_module(f"{PACKAGE}.tests")
    modules = [
        importlib.import_module(f"{PACKAGE}.tests.{info.name}")
        for info in pkgutil.iter_modules(package.__path__)
    ]
    return [
        value
        for module in modules
        for value in vars(module).values()
        if isinstance(value, type)
        and issubclass(value, unittest.TestCase)
        and value.__module__ == module.__name__
    ]


def source_options() -> list[str]:
    frappe.clear_cache(doctype="HD Ticket")
    return frappe.get_meta("HD Ticket").get_field("source").options.split("\n")
