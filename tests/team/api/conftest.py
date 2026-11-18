"""Fixtures for the team's API and integration tests.

The tests talk to the running bench over HTTP with `requests`, as the seeded
agent and customers. A second, in-process connection to the same site (`site`)
is used only where the workflow has no HTTP route: recording an agent's reply
without an outgoing mail server, ageing a conversation, running the daily
auto-close job, and reading records straight from the database.
"""

import datetime
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests

TEAM_DIR = Path(__file__).resolve().parent.parent
BENCH_DIR = TEAM_DIR.parent.parent.parent.parent
ENV_FILE = TEAM_DIR / ".env"

NEW = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.new"
ONE = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_one"
ASSIGNEES = "/api/method/helpdesk.helpdesk.doctype.hd_ticket.api.get_ticket_assignees"
RUN_DOC_METHOD = "/api/method/run_doc_method"

# (operationId, status code) of every call made through Client.call; read by
# test_zz_api_coverage.py to check the API coverage criteria.
CALL_LOG = []


def load_env():
    if not ENV_FILE.exists():
        raise RuntimeError("tests/team/.env is missing: run `bash tests/team/seed.sh seed` first")
    values = {}
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


ENV = load_env()
BASE = ENV["SQE_BASE_URL"]


class Client:
    """One logged-in (or anonymous) HTTP session against the site."""

    def __init__(self, role, prefix=None):
        self.role = role
        self.email = ENV[f"{prefix}_EMAIL"] if prefix else None
        self.session = requests.Session()
        self.session.headers["Host"] = ENV["SQE_SITE"]
        if prefix:
            response = self.session.post(
                BASE + "/api/method/login",
                json={"usr": self.email, "pwd": ENV[f"{prefix}_PASSWORD"]},
                timeout=30,
            )
            assert response.status_code == 200, f"login failed for the seeded {role}"

    def call(self, operation, method, path, **kwargs):
        response = self.session.request(method, BASE + path, timeout=60, **kwargs)
        CALL_LOG.append((operation, response.status_code))
        return response

    # --- the four operations of the contract -------------------------------

    def create_ticket(self, body):
        return self.call("createTicket", "POST", NEW, json=body)

    def get_ticket(self, params):
        return self.call("getTicket", "GET", ONE, params=params)

    def update_ticket(self, name, body):
        return self.call("updateTicket", "PUT", f"/api/resource/HD Ticket/{name}", json=body)

    def assign_agent(self, body):
        return self.call("assignAgent", "POST", RUN_DOC_METHOD, json=body)

    # --- conveniences --------------------------------------------------------

    def new_ticket(self, subject="Printer on floor 2 is jammed", description="<p>Paper is stuck.</p>"):
        response = self.create_ticket({"doc": {"subject": subject, "description": description}})
        assert response.status_code == 200, response.text
        return response.json()["message"]["name"]

    def read(self, name):
        response = self.get_ticket({"name": name})
        assert response.status_code == 200, response.text
        return response.json()["message"]

    def assignees(self, name):
        response = self.session.get(BASE + ASSIGNEES, params={"ticket": name}, timeout=60)
        assert response.status_code == 200, response.text
        return [row["name"] for row in response.json()["message"]]


def assign_body(ticket, agent):
    return {"dt": "HD Ticket", "dn": ticket, "method": "assign_agent", "args": {"agent": agent}}


def error_text(response):
    """Everything the server said about a failure, as one string."""
    try:
        body = response.json()
    except ValueError:
        return response.text
    return " ".join(str(body.get(key, "")) for key in ("exception", "_server_messages", "_error_message"))


class Site:
    """In-process access to the same site, for steps that have no HTTP route."""

    def __init__(self):
        import frappe

        self.frappe = frappe
        os.chdir(BENCH_DIR / "sites")
        frappe.init(ENV["SQE_SITE"])
        frappe.connect()
        frappe.set_user("Administrator")

    def fresh(self):
        """Drop this connection's snapshot so the next read sees the server's commits."""
        self.frappe.db.rollback()

    def ticket(self, name):
        self.fresh()
        return self.frappe.db.get_value("HD Ticket", name, "*", as_dict=True)

    def count(self, doctype, filters):
        self.fresh()
        return self.frappe.db.count(doctype, filters)

    def settings(self, **values):
        self.fresh()
        doc = self.frappe.get_doc("HD Settings")
        for key, value in values.items():
            doc.set(key, value)
        doc.save(ignore_permissions=True)
        self.frappe.db.commit()

    def add_agent_reply(self, ticket, agent, customer):
        """Record a sent reply, as the agent desk does when mail is configured."""
        self.fresh()
        self.frappe.get_doc(
            {
                "doctype": "Communication",
                "communication_type": "Communication",
                "communication_medium": "Email",
                "sent_or_received": "Sent",
                "reference_doctype": "HD Ticket",
                "reference_name": ticket,
                "subject": "Re: your ticket",
                "content": "<p>Please try restarting the printer.</p>",
                "sender": agent,
                "recipients": customer,
            }
        ).insert(ignore_permissions=True)
        self.frappe.db.commit()

    def age_conversation(self, ticket, days):
        """Make every message on the ticket `days` days old."""
        self.fresh()
        moment = self.frappe.utils.now_datetime() - datetime.timedelta(days=days)
        self.frappe.db.sql(
            "update `tabCommunication` set communication_date=%s "
            "where reference_doctype='HD Ticket' and reference_name=%s",
            (moment, ticket),
        )
        self.frappe.db.commit()

    def age_ticket(self, ticket, days):
        self.fresh()
        moment = self.frappe.utils.now_datetime() - datetime.timedelta(days=days)
        self.frappe.db.sql(
            "update `tabHD Ticket` set creation=%s, modified=%s where name=%s", (moment, moment, ticket)
        )
        self.frappe.db.commit()

    def run_auto_close(self):
        from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import close_tickets_after_n_days

        self.fresh()
        close_tickets_after_n_days()
        self.frappe.db.commit()

    def auto_close_comments(self, ticket):
        self.fresh()
        return self.frappe.get_all(
            "Comment",
            filters={
                "reference_doctype": "HD Ticket",
                "reference_name": ticket,
                "content": ["like", "%automatically closed%"],
            },
            pluck="content",
        )


def run_seed(command):
    # The bench's own background workers touch the same rows, so a delete can
    # occasionally lose a lock race; the script is idempotent, so retry it.
    for attempt in range(3):
        result = subprocess.run(
            ["bash", str(TEAM_DIR / "seed.sh"), command, ENV["SQE_SITE"]],
            capture_output=True,
            text=True,
            cwd=TEAM_DIR,
        )
        if result.returncode == 0:
            return
        time.sleep(2)
    raise RuntimeError(f"seed.sh {command} failed 3 times:\n{result.stderr[-2000:]}")


@pytest.fixture(scope="session", autouse=True)
def clean_site():
    """Every run starts from, and returns to, the seeded state."""
    run_seed("reset")
    yield
    run_seed("reset")


@pytest.fixture(scope="session")
def site(clean_site):
    helper = Site()
    yield helper
    helper.frappe.destroy()


@pytest.fixture(scope="session")
def customer_a(clean_site):
    return Client("customer", "SQE_CUSTOMER_A")


@pytest.fixture(scope="session")
def customer_b(clean_site):
    return Client("customer", "SQE_CUSTOMER_B")


@pytest.fixture(scope="session")
def agent(clean_site):
    return Client("agent", "SQE_AGENT")


@pytest.fixture(scope="session")
def anonymous(clean_site):
    return Client("anonymous")


@pytest.fixture
def ticket(customer_a):
    """A fresh ticket raised by customer A (workflow A's output, workflow B's input)."""
    return customer_a.new_ticket()
