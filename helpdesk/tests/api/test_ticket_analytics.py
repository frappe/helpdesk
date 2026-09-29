import json

import frappe
from frappe.desk.form import assign_to
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date

from helpdesk.api.ticket_analytics import get_ticket_analytics
from helpdesk.test_utils import (
    add_comment,
    add_message,
    create_agent,
    create_contact,
    get_current_week_monday,
    make_ticket,
    timeline_node,
)

AGENT = "analytics-agent@example.com"
AGENT_TWO = "analytics-agent-two@example.com"
CUSTOMER = "analytics-customer@example.com"


class TestTicketAnalytics(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_agent(AGENT, "Analytics", "Agent")
        create_agent(AGENT_TWO, "Second", "Agent")

    def setUp(self):
        frappe.set_user("Administrator")
        self.monday = get_current_week_monday()

    def tearDown(self):
        frappe.set_user("Administrator")

    def make_high_ticket(self, **args):
        # High priority on the test SLA: 1h response, 4h resolution, Mon-Fri 10:00-18:00
        with self.freeze_time(self.monday):
            return make_ticket(subject="Analytics ticket", priority="High", **args)

    def test_gap_walk_metrics_and_summary(self):
        # ticket insert auto-creates the first Received message from the description
        ticket = self.make_high_ticket()
        with self.freeze_time(add_to_date(self.monday, hours=1)):
            add_message(ticket.name, "Sent", AGENT)
        with self.freeze_time(add_to_date(self.monday, hours=1, minutes=30)):
            add_message(ticket.name, "Sent", AGENT)
        with self.freeze_time(add_to_date(self.monday, hours=2)):
            add_message(ticket.name, "Received", CUSTOMER)
        with self.freeze_time(add_to_date(self.monday, hours=4)):
            add_message(ticket.name, "Sent", AGENT_TWO)
        add_comment(ticket.name)

        result = get_ticket_analytics(ticket.name)

        # the description and the first Sent (= first response) render as
        # milestones, so events start at the follow-up; its gap still counts
        events = result["events"]
        self.assertEqual([e["side"] for e in events], ["agent", "customer", "agent"])
        self.assertEqual([e["wait_seconds"] for e in events], [None, None, 7200])
        self.assertEqual(events[0]["sender"], AGENT)
        self.assertTrue(events[0]["sender_name"])
        self.assertEqual(result["metrics"]["avg_agent_gap"], 5400)
        # only Sent->Received hand-off: the 1h30m follow-up to the 2h reply
        self.assertEqual(result["metrics"]["avg_customer_gap"], 1800)
        self.assertIsNone(result["metrics"]["hold_time"])

        summary = result["summary"]
        self.assertEqual(summary["customer_messages"], 2)
        self.assertEqual(summary["agent_messages"], 3)
        self.assertEqual(summary["internal_comments"], 1)
        self.assertEqual(
            [a["email"] for a in summary["agents_involved"]], [AGENT, AGENT_TWO]
        )

    def test_agents_involved_includes_assignees_who_never_replied(self):
        ticket = self.make_high_ticket()
        with self.freeze_time(add_to_date(self.monday, hours=1)):
            add_message(ticket.name, "Sent", AGENT)
        # AGENT replied and is assigned; AGENT_TWO only holds the assignment
        assign_to.add(
            {
                "doctype": "HD Ticket",
                "name": ticket.name,
                "assign_to": [AGENT, AGENT_TWO],
            }
        )

        involved = get_ticket_analytics(ticket.name)["summary"]["agents_involved"]

        # repliers keep their conversation order, assignees follow
        self.assertEqual([a["email"] for a in involved], [AGENT, AGENT_TWO])
        # avatar payload is ready to render, no client-side user lookup
        self.assertTrue(all(a["name"] for a in involved))

    def test_weekend_gap_counts_business_hours_only(self):
        friday = add_to_date(self.monday, days=4, hours=6)
        with self.freeze_time(friday):
            ticket = make_ticket(subject="Weekend gap", priority="High")
            add_message(ticket.name, "Received", CUSTOMER)
        with self.freeze_time(add_to_date(self.monday, days=7)):
            add_message(ticket.name, "Sent", AGENT)

        result = get_ticket_analytics(ticket.name)
        # Fri 17:00-18:00 + Mon 10:00-11:00; the reply is the first response,
        # so its gap surfaces through metrics rather than an event
        self.assertEqual(result["metrics"]["avg_agent_gap"], 7200)
        self.assertEqual([e["side"] for e in result["events"]], ["customer"])

    def test_no_sla_falls_back_to_wall_clock(self):
        # every ticket save re-selects an SLA, so clear the fields after the last write
        evening = add_to_date(self.monday, hours=8)
        with self.freeze_time(evening):
            ticket = make_ticket(subject="No SLA")
        with self.freeze_time(add_to_date(evening, hours=1, minutes=30)):
            add_message(ticket.name, "Sent", AGENT)
        frappe.db.set_value(
            "HD Ticket",
            ticket.name,
            {
                "sla": None,
                "response_by": None,
                "resolution_by": None,
                "first_response_time": None,
                "service_level_agreement_creation": None,
            },
        )
        result = get_ticket_analytics(ticket.name)

        self.assertFalse(result["has_sla"])
        # 19:00 to 20:30 is outside business hours; wall-clock still counts it
        self.assertEqual(result["metrics"]["avg_agent_gap"], 5400)
        first_response = timeline_node(result, "first_response")
        self.assertEqual(first_response["state"], "done")
        self.assertEqual(first_response["badge"]["text"], "Responded in 1h 30m")
        self.assertIsNone(first_response["target"])
        resolution = timeline_node(result, "resolution")
        self.assertEqual(resolution["state"], "pending")
        self.assertIsNone(resolution["eta"])
        self.assertIsNone(resolution["badge"])

    def test_open_ticket_pending_milestones(self):
        ticket = self.make_high_ticket()
        with self.freeze_time(add_to_date(self.monday, minutes=30)):
            result = get_ticket_analytics(ticket.name)

        first_response = timeline_node(result, "first_response")
        self.assertEqual(first_response["state"], "pending")
        self.assertEqual(first_response["eta"], ticket.response_by)
        self.assertEqual(first_response["took"], 1800)
        self.assertEqual(first_response["target"], 3600)

        resolution = timeline_node(result, "resolution")
        self.assertEqual(resolution["state"], "pending")
        self.assertIsNone(timeline_node(result, "hold"))

    def test_unresponded_past_due_is_overdue_breach(self):
        ticket = self.make_high_ticket()
        with self.freeze_time(add_to_date(self.monday, hours=2)):
            result = get_ticket_analytics(ticket.name)

        first_response = timeline_node(result, "first_response")
        self.assertEqual(first_response["state"], "breach")
        self.assertEqual(first_response["badge"]["text"], "Overdue by 1h")
        self.assertEqual(first_response["took"], 7200)

    def test_first_response_within_sla(self):
        ticket = self.make_high_ticket()
        ticket.reload()
        with self.freeze_time(add_to_date(self.monday, minutes=30)):
            ticket.status = "Replied"
            ticket.save()
        with self.freeze_time(add_to_date(self.monday, minutes=45)):
            add_message(ticket.name, "Sent", AGENT)
        result = get_ticket_analytics(ticket.name)

        # description and first response render as milestones, not events
        self.assertEqual(result["events"], [])
        first_response = timeline_node(result, "first_response")
        self.assertEqual(first_response["state"], "done")
        self.assertEqual(first_response["badge"]["tone"], "green")
        self.assertEqual(first_response["took"], 1800)
        self.assertEqual(first_response["target"], 3600)

    def test_fulfilled_duration_survives_sla_reapply(self):
        # an SLA change stamps a new service_level_agreement_creation that can
        # postdate the response; the duration must not clamp to zero (it falls
        # back to wall clock from creation, mirroring the sidebar)
        ticket = self.make_high_ticket()
        frappe.db.set_value(
            "HD Ticket",
            ticket.name,
            {
                "first_responded_on": add_to_date(self.monday, minutes=30),
                "first_response_time": 0,
                "service_level_agreement_creation": add_to_date(self.monday, days=2),
            },
        )
        result = get_ticket_analytics(ticket.name)

        first_response = timeline_node(result, "first_response")
        self.assertEqual(first_response["took"], 1800)
        self.assertEqual(first_response["badge"]["text"], "Fulfilled in 30m")

    def test_first_response_breach(self):
        ticket = self.make_high_ticket()
        ticket.reload()
        with self.freeze_time(add_to_date(self.monday, hours=2)):
            ticket.status = "Replied"
            ticket.save()
        result = get_ticket_analytics(ticket.name)

        first_response = timeline_node(result, "first_response")
        self.assertEqual(first_response["state"], "breach")
        self.assertEqual(first_response["badge"]["text"], "Failed by 1h")
        self.assertEqual(first_response["took"], 7200)
        self.assertEqual(first_response["target"], 3600)

    def test_resolution_with_spare(self):
        ticket = self.make_high_ticket()
        ticket.reload()
        with self.freeze_time(add_to_date(self.monday, minutes=30)):
            ticket.status = "Resolved"
            ticket.save()
        result = get_ticket_analytics(ticket.name)

        resolution = timeline_node(result, "resolution")
        self.assertEqual(resolution["state"], "done")
        self.assertEqual(resolution["badge"]["text"], "3h 30m to spare")
        self.assertEqual(resolution["took"], 1800)
        self.assertEqual(resolution["target"], 14400)

    def test_resolution_breach(self):
        ticket = self.make_high_ticket()
        ticket.reload()
        with self.freeze_time(add_to_date(self.monday, days=1)):
            ticket.status = "Resolved"
            ticket.save()
        result = get_ticket_analytics(ticket.name)

        # Mon 11:00-18:00 + Tue 10:00-11:00 = 8h took, target 4h
        resolution = timeline_node(result, "resolution")
        self.assertEqual(resolution["state"], "breach")
        self.assertEqual(resolution["badge"]["text"], "Failed by 4h")
        self.assertEqual(resolution["took"], 28800)

    def test_hold_live_then_resumed_window(self):
        ticket = self.make_high_ticket()
        ticket.reload()
        pause_at = add_to_date(self.monday, minutes=30)
        with self.freeze_time(pause_at):
            ticket.status = "Replied"
            ticket.save(ignore_version=False)

        with self.freeze_time(add_to_date(self.monday, hours=1)):
            result = get_ticket_analytics(ticket.name)
            hold = timeline_node(result, "hold")
            self.assertTrue(hold["active"])
            self.assertEqual(hold["badge"]["text"], "30m paused")
            self.assertEqual(result["metrics"]["hold_time"], 1800)
            self.assertEqual(hold["window"]["start"], pause_at)
            self.assertIsNone(hold["window"]["end"])
            resolution = timeline_node(result, "resolution")
            self.assertEqual(resolution["state"], "pending")

        ticket.reload()
        resume_at = add_to_date(self.monday, hours=1, minutes=30)
        with self.freeze_time(resume_at):
            ticket.status = "Open"
            ticket.save(ignore_version=False)
        with self.freeze_time(add_to_date(self.monday, hours=2)):
            result = get_ticket_analytics(ticket.name)

        hold = timeline_node(result, "hold")
        self.assertFalse(hold["active"])
        self.assertEqual(hold["badge"]["text"], "1h paused")
        self.assertEqual(result["metrics"]["hold_time"], 3600)
        self.assertEqual(hold["window"]["start"], pause_at)
        self.assertEqual(hold["window"]["end"], resume_at)

    def test_agent_gap_excludes_paused_time(self):
        # description at 10:00, paused 10:30-11:00, agent reply at 11:30:
        # the 1h30m raw gap loses the 30m the SLA clock was stopped
        ticket = self.make_high_ticket()
        ticket.reload()
        with self.freeze_time(add_to_date(self.monday, minutes=30)):
            ticket.status = "Replied"
            ticket.save(ignore_version=False)
        ticket.reload()
        with self.freeze_time(add_to_date(self.monday, hours=1)):
            ticket.status = "Open"
            ticket.save(ignore_version=False)
        with self.freeze_time(add_to_date(self.monday, hours=1, minutes=30)):
            add_message(ticket.name, "Sent", AGENT)

        result = get_ticket_analytics(ticket.name)
        self.assertEqual(result["metrics"]["avg_agent_gap"], 3600)

    def test_closed_without_resolution(self):
        ticket = self.make_high_ticket()
        frappe.db.set_value(
            "HD Ticket",
            ticket.name,
            {
                "status": "Closed",
                "status_category": "Resolved",
                "resolution_date": None,
            },
        )
        result = get_ticket_analytics(ticket.name)

        resolution = timeline_node(result, "resolution")
        self.assertEqual(resolution["state"], "done")
        self.assertEqual(resolution["badge"]["text"], "Closed without resolution")
        self.assertEqual(resolution["badge"]["tone"], "gray")

    def test_churn_counts(self):
        with self.freeze_time(self.monday):
            # Medium falls to the default SLA; High re-selects the priority SLA
            ticket = make_ticket(subject="Churn ticket", priority="Medium")
        ticket.reload()
        with self.freeze_time(add_to_date(self.monday, minutes=10)):
            ticket.priority = "High"
            # tests default to ignore_version, which would hide the diffs churn reads
            ticket.save(ignore_version=False)
        # a real HD Team insert leaks its assignment rule across test
        # transactions and breaks unrelated suites, so the team change is
        # recorded directly as the Version diff churn() reads
        frappe.get_doc(
            {
                "doctype": "Version",
                "ref_doctype": "HD Ticket",
                "docname": ticket.name,
                "data": json.dumps(
                    {"changed": [["agent_group", "", "Analytics Team"]]}
                ),
            }
        ).insert(ignore_permissions=True)

        churn = get_ticket_analytics(ticket.name)["summary"]["churn"]
        self.assertEqual(churn["sla_changes"], 1)
        self.assertEqual(churn["team_changes"], 1)

    def test_non_agent_is_rejected(self):
        ticket = self.make_high_ticket()
        contact = create_contact("Analytics Customer", CUSTOMER)
        frappe.set_user(contact["user"])
        with self.assertRaises(frappe.PermissionError):
            get_ticket_analytics(ticket.name)
