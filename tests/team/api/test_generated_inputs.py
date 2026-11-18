"""EP and 3-point BVA on every API input, driven by the generated test data.

No input value in this file is hand-picked: each test case comes from
generated/testdata.json, which generate_testdata.py derives from openapi.yaml.
One case changes one input. After a valid request the stored record is read
back and must show the value; after an invalid request the response must be
the documented rejection and the stored records must be unchanged.

Cases where the running system does not behave as the contract says are listed
in known_weaknesses.yaml. They run as strict expected failures: the weakness
is reported, and the test starts failing loudly the day the behaviour changes.
"""

import copy
import json
import os
from pathlib import Path

import pytest
import yaml
from conftest import assign_body

HERE = Path(__file__).resolve().parent
# SQE_TESTDATA points the tests at another generated file (see demo_constraint_change.sh)
DATA = json.loads(Path(os.environ.get("SQE_TESTDATA") or HERE / "generated" / "testdata.json").read_text())
WEAKNESSES = yaml.safe_load((HERE / "known_weaknesses.yaml").read_text()) or {}
MISSING = "__MISSING__"
WATCHED = ("subject", "status", "priority", "ticket_type", "feedback", "feedback_extra")

BASELINE_NEW = {"doc": {"subject": "Printer on floor 2 is jammed", "description": "<p>Paper is stuck.</p>"}}


def weakness_key(case):
    return f"{case['operationId']} | {case['input']} | {case['class']}"


def as_param(case):
    weakness = WEAKNESSES.get("generated", {}).get(weakness_key(case))
    marks = [pytest.mark.xfail(strict=True, reason=f"{weakness['id']}: {weakness['observed']}")] if weakness else []
    return pytest.param(case, id=case["id"], marks=marks)


def cases_for(operation):
    return [as_param(case) for case in DATA["cases"] if case["operationId"] == operation]


def put(container, dotted, value):
    """Set (or, for MISSING, remove) one input in a nested request body."""
    *parents, leaf = dotted.split(".")
    for key in parents:
        container = container[key]
    if value == MISSING:
        container.pop(leaf, None)
    else:
        container[leaf] = value


def resolve(value, fixtures):
    if isinstance(value, dict) and "fixture" in value:
        return fixtures[value["fixture"]]
    return value


def split(case):
    location, path = case["input"].split(":", 1)
    return location, path


# --- createTicket -------------------------------------------------------------


@pytest.mark.parametrize("case", cases_for("createTicket"))
def test_create_ticket_input(case, customer_a, site):
    _, path = split(case)
    body = copy.deepcopy(BASELINE_NEW)
    put(body, path, case["value"])
    before = site.count("HD Ticket", {"raised_by": customer_a.email})

    response = customer_a.create_ticket(body)

    assert response.status_code == case["expect_status"], response.text[:300]
    after = site.count("HD Ticket", {"raised_by": customer_a.email})
    if case["valid"]:
        assert after == before + 1
        stored = customer_a.read(response.json()["message"]["name"])
        field = path.split(".")[-1]
        if field == "subject":
            assert stored["subject"] == case["value"]
        else:
            assert stored["communications"], "the description should open the conversation"
    else:
        assert after == before, "a rejected request must not create a ticket"


# --- getTicket ----------------------------------------------------------------


@pytest.mark.parametrize("case", cases_for("getTicket"))
def test_get_ticket_input(case, customer_a, ticket):
    value = resolve(case["value"], {"ticket_name": ticket})
    params = {} if value == MISSING else {"name": value}

    response = customer_a.get_ticket(params)

    assert response.status_code == case["expect_status"], response.text[:300]
    if case["valid"]:
        assert response.json()["message"]["name"] == ticket


# --- updateTicket -------------------------------------------------------------


@pytest.mark.parametrize("case", cases_for("updateTicket"))
def test_update_ticket_input(case, agent, ticket):
    location, path = split(case)
    before = {key: value for key, value in agent.read(ticket).items() if key in WATCHED}
    if location == "path":
        name, body = resolve(case["value"], {"ticket_name": ticket}), {"priority": "High"}
    else:
        name, body = ticket, {}
        put(body, path, case["value"])

    response = agent.update_ticket(name, body)

    assert response.status_code == case["expect_status"], response.text[:300]
    after = {key: value for key, value in agent.read(ticket).items() if key in WATCHED}
    if case["valid"]:
        expected = dict(before, **body)
        assert after == expected, "the stored ticket must show exactly the requested change"
    else:
        assert after == before, "a rejected update must leave the ticket unchanged"


# --- assignAgent --------------------------------------------------------------


@pytest.mark.parametrize("case", cases_for("assignAgent"))
def test_assign_agent_input(case, agent, ticket):
    _, path = split(case)
    body = assign_body(ticket, agent.email)
    put(body, path, resolve(case["value"], {"ticket_name": ticket, "agent_email": agent.email}))

    response = agent.assign_agent(body)

    assert response.status_code == case["expect_status"], response.text[:300]
    assignees = agent.assignees(ticket)
    if case["valid"]:
        assert assignees == [agent.email]
    else:
        assert assignees == [], "a rejected assignment must leave the ticket unassigned"


def test_every_generated_case_is_bound_to_a_test():
    handled = {"createTicket", "getTicket", "updateTicket", "assignAgent"}
    assert {case["operationId"] for case in DATA["cases"]} <= handled
