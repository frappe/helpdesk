import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.api.onboarding import (
    complete_setup,
    get_setup_status,
    mark_checklist_steps,
    set_telemetry_enabled,
)
from helpdesk.consts import ONBOARDING_STEPS, WELCOME_TICKET_SUBJECT
from helpdesk.patches.mark_setup_complete_for_existing_sites import execute
from helpdesk.test_utils import (
    add_message,
    create_agent,
    create_user,
    fill_system_settings_defaults,
    make_email_account,
    make_ticket,
    unique_email,
)


class TestExistingSitePatch(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.db.set_single_value("HD Settings", "setup_complete", 0)
        for ticket in frappe.get_all(
            "HD Ticket",
            filters={"subject": ["!=", WELCOME_TICKET_SUBJECT]},
            pluck="name",
        ):
            frappe.delete_doc("HD Ticket", ticket, force=True)
        for account in frappe.get_all("Email Account", pluck="name"):
            frappe.delete_doc("Email Account", account, force=True)

    def setup_complete(self) -> int:
        return frappe.db.get_single_value("HD Settings", "setup_complete")

    def test_a_site_with_only_the_welcome_ticket_stays_pending(self) -> None:
        execute()

        self.assertEqual(self.setup_complete(), 0)

    def test_a_site_with_a_real_ticket_is_marked_complete(self) -> None:
        make_ticket(subject="A real customer question")

        execute()

        self.assertEqual(self.setup_complete(), 1)

    def test_a_site_with_an_email_account_is_marked_complete(self) -> None:
        make_email_account(enable_incoming=0)

        execute()

        self.assertEqual(self.setup_complete(), 1)


class TestSetupApiPermissions(IntegrationTestCase):
    def test_only_a_system_manager_may_use_the_setup_api(self) -> None:
        agent = create_agent(unique_email("setup-agent"))
        plain = create_user(unique_email("setup-plain"))
        calls = (
            get_setup_status,
            complete_setup,
            lambda: set_telemetry_enabled(False),
            lambda: mark_checklist_steps(["invite_agents"]),
        )

        for user in (agent.name, plain.name):
            with self.set_user(user):
                for call in calls:
                    with self.assertRaises(frappe.PermissionError):
                        call()


class TestSetupStatus(IntegrationTestCase):
    def setUp(self) -> None:
        for account in frappe.get_all("Email Account", pluck="name"):
            frappe.delete_doc("Email Account", account, force=True)
        frappe.db.delete(
            "Communication",
            {"reference_doctype": "HD Ticket", "email_account": ["is", "set"]},
        )

    def test_a_clean_site_has_nothing_connected(self) -> None:
        status = get_setup_status()

        self.assertFalse(status["email_connected"])
        self.assertFalse(status["ticket_arrived"])

    def test_an_enabled_incoming_account_counts_as_connected(self) -> None:
        make_email_account(enable_incoming=1)

        self.assertTrue(get_setup_status()["email_connected"])

    def test_a_ticket_fetched_by_the_mailbox_has_arrived(self) -> None:
        account = make_email_account()
        sender = unique_email("customer")
        ticket = make_ticket(subject="Mailbox ticket", raised_by=sender)

        add_message(ticket.name, "Received", sender, email_account=account)

        self.assertTrue(get_setup_status()["ticket_arrived"])

    def test_a_message_without_a_mailbox_does_not_count(self) -> None:
        sender = unique_email("customer")
        ticket = make_ticket(subject="Agent-made ticket", raised_by=sender)

        add_message(ticket.name, "Received", sender)

        self.assertFalse(get_setup_status()["ticket_arrived"])

    def test_telemetry_flag_follows_system_settings(self) -> None:
        fill_system_settings_defaults()
        set_telemetry_enabled(False)
        self.assertFalse(get_setup_status()["telemetry_enabled"])

        set_telemetry_enabled(True)
        self.assertTrue(get_setup_status()["telemetry_enabled"])


class TestCompleteSetup(IntegrationTestCase):
    def test_finishing_twice_leaves_the_flag_set(self) -> None:
        frappe.db.set_single_value("HD Settings", "setup_complete", 0)

        complete_setup()
        complete_setup(skipped=True)

        self.assertEqual(frappe.db.get_single_value("HD Settings", "setup_complete"), 1)


class TestMarkChecklistSteps(IntegrationTestCase):
    def setUp(self) -> None:
        frappe.db.set_value("User", "Administrator", "onboarding_status", None)

    def stored(self) -> list[dict]:
        raw = frappe.db.get_value("User", "Administrator", "onboarding_status")
        return frappe.parse_json(raw)["helpdesk_onboarding_status"]

    def test_the_canonical_list_is_stored_with_only_the_given_step_done(self) -> None:
        mark_checklist_steps(["invite_agents"])

        self.assertEqual(
            self.stored(),
            [{"name": n, "completed": n == "invite_agents"} for n in ONBOARDING_STEPS],
        )

    def test_earlier_progress_is_kept_and_obsolete_steps_dropped(self) -> None:
        frappe.db.set_value(
            "User",
            "Administrator",
            "onboarding_status",
            frappe.as_json(
                {
                    "helpdesk_onboarding_status": [
                        {"name": "old_step", "completed": False},
                        {"name": "setup_sla", "completed": True},
                    ]
                }
            ),
        )

        mark_checklist_steps(["setup_email_account"])

        stored = {step["name"]: step["completed"] for step in self.stored()}
        self.assertNotIn("old_step", stored)
        self.assertTrue(stored["setup_sla"])
        self.assertTrue(stored["setup_email_account"])

    def test_a_step_setup_does_not_own_is_refused(self) -> None:
        with self.assertRaises(frappe.ValidationError):
            mark_checklist_steps(["setup_sla"])

    def test_the_step_names_match_the_sidebar(self) -> None:
        sidebar = Path(frappe.get_app_path("helpdesk")).parent / (
            "desk/src/components/layouts/Sidebar.vue"
        )
        source = sidebar.read_text()
        steps_block = source.split("const steps = [", 1)[1].split("\n];", 1)[0]

        names = tuple(re.findall(r'^    name: "(\w+)",$', steps_block, re.M))
        self.assertEqual(names, ONBOARDING_STEPS)
