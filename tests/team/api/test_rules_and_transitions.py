"""Rule rejections, state transitions, repeated requests and cross-workflow checks.

Workflow A (raise a ticket) creates the shared HD Ticket record; workflow B
(handle a ticket) reads and changes it. Every test reads the record back after
the request, on success and on rejection.

Tests marked `weakness(...)` describe behaviour the business rules or the
contract do not allow but the baseline does. They are strict expected
failures; the catalogue is in WEAKNESSES.md.
"""

import pytest
from conftest import NEW, assign_body, error_text

STATUSES = ["Open", "Replied", "Resolved", "Closed"]
CATEGORY = {"Open": "Open", "Replied": "Paused", "Resolved": "Resolved", "Closed": "Resolved"}
FEEDBACK = "Clear guidance given"
FEEDBACK_RATING = 0.6


def weakness(identifier, observed):
    return pytest.mark.xfail(strict=True, reason=f"{identifier}: {observed}")


def set_status(client, ticket, status):
    response = client.update_ticket(ticket, {"status": status})
    assert response.status_code == 200, response.text[:300]
    return client.read(ticket)


# === Workflow A: raise a ticket =================================================


def test_new_ticket_gets_the_default_state_and_the_callers_identity(customer_a):
    name = customer_a.new_ticket(subject="Monitor flickers")
    stored = customer_a.read(name)
    assert stored["subject"] == "Monitor flickers"
    assert stored["status"] == "Open"
    assert stored["status_category"] == "Open"
    assert stored["priority"] == "Medium"
    assert stored["raised_by"] == customer_a.email
    assert stored["resolution_date"] is None


@pytest.mark.parametrize(
    ("field", "sent", "stored_as"),
    [
        ("raised_by", "someone.else@sqe.test", None),  # replaced by the session user
        ("status", "Closed", "Open"),
        ("priority", "Urgent", "Medium"),
        ("resolution_date", "2020-01-01 00:00:00", None),
    ],
)
def test_customer_cannot_set_server_controlled_fields_when_raising(customer_a, field, sent, stored_as):
    response = customer_a.create_ticket({"doc": {"subject": "Server fields", "description": "x", field: sent}})
    assert response.status_code == 200
    stored = customer_a.read(response.json()["message"]["name"])
    assert stored[field] == (customer_a.email if field == "raised_by" else stored_as)


def test_anonymous_visitor_cannot_raise_a_ticket(anonymous, site):
    before = site.count("HD Ticket", {})
    response = anonymous.create_ticket({"doc": {"subject": "No session", "description": "x"}})
    assert response.status_code == 403
    assert site.count("HD Ticket", {}) == before


def test_ticket_is_private_to_its_customer_and_visible_to_agents(customer_a, customer_b, agent, anonymous, ticket):
    assert customer_b.get_ticket({"name": ticket}).status_code == 403
    assert anonymous.get_ticket({"name": ticket}).status_code == 403
    # cross-workflow: the record workflow A created is what workflow B reads
    seen_by_agent = agent.read(ticket)
    assert seen_by_agent["raised_by"] == customer_a.email
    assert seen_by_agent["status"] == "Open"


# === Workflow B: BR4, what a customer may change ===============================


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"subject": "Edited after raising"}, "You cannot change Subject after the ticket is raised"),
        ({"priority": "Urgent"}, "You do not have permission to change Priority"),
        ({"status": "Resolved"}, "You cannot change Status after the ticket is raised"),
        ({"feedback_rating": 1}, "You cannot change Rating after the ticket is raised"),
    ],
    ids=["subject", "priority", "status-resolved", "rating"],
)
def test_customer_edit_is_refused_and_explained(customer_a, ticket, change, message):
    before = customer_a.read(ticket)
    response = customer_a.update_ticket(ticket, change)
    assert response.status_code == 403
    assert message in error_text(response)
    after = customer_a.read(ticket)
    for field in change:
        assert after[field] == before[field]


def test_another_customer_cannot_update_the_ticket(customer_a, customer_b, ticket):
    response = customer_b.update_ticket(ticket, {"status": "Closed"})
    assert response.status_code == 403
    assert customer_a.read(ticket)["status"] == "Open"


def test_another_customer_cannot_assign_the_ticket(customer_b, agent, ticket):
    response = customer_b.assign_agent(assign_body(ticket, agent.email))
    assert response.status_code == 403
    assert agent.assignees(ticket) == []


@pytest.mark.parametrize(
    ("closed", "rated", "allowed"),
    [(False, False, True), (False, True, False), (True, False, False), (True, True, False)],
    ids=["FF-allowed", "FT-rated", "TF-closed", "TT-closed-and-rated"],
)
def test_decision_table_closed_or_rated_locks_the_ticket_for_the_customer(
    customer_a, agent, ticket, closed, rated, allowed
):
    """BR4 decision table at API level. The attempted update is a feedback comment,
    a field a customer may always write, so only the closed/rated state decides."""
    if rated:
        assert agent.update_ticket(ticket, {"feedback": FEEDBACK}).status_code == 200
    if closed:
        set_status(agent, ticket, "Closed")
    before = customer_a.read(ticket)

    response = customer_a.update_ticket(ticket, {"feedback_extra": "one more thing"})

    after = customer_a.read(ticket)
    if allowed:
        assert response.status_code == 200
        assert after["feedback_extra"] == "one more thing"
    else:
        assert response.status_code == 403
        assert "Closed or rated tickets cannot be updated by non-agents" in error_text(response)
        assert after["feedback_extra"] == before["feedback_extra"]
        assert after["status"] == before["status"]


def test_agent_is_not_locked_out_of_a_closed_and_rated_ticket(agent, ticket):
    agent.update_ticket(ticket, {"feedback": FEEDBACK})
    set_status(agent, ticket, "Closed")
    assert set_status(agent, ticket, "Open")["status"] == "Open"


# === Workflow B: BR3, state transitions =========================================


def expected_resolution(source, target):
    """What BR3 says happens to the resolution date on source -> target."""
    if CATEGORY[target] != "Resolved":
        return "cleared"
    return "kept" if CATEGORY[source] == "Resolved" else "stamped"


@pytest.mark.parametrize(
    ("source", "target"),
    [(s, t) for s in STATUSES for t in STATUSES if s != t],
    ids=lambda value: value,
)
def test_agent_may_make_every_status_change(agent, ticket, source, target):
    """All 12 changes between the four statuses are allowed for an agent."""
    if source != "Open":
        set_status(agent, ticket, source)
    before = agent.read(ticket)

    after = set_status(agent, ticket, target)

    assert after["status"] == target
    assert after["status_category"] == CATEGORY[target]
    outcome = expected_resolution(source, target)
    if outcome == "cleared":
        assert after["resolution_date"] is None
    elif outcome == "kept":
        assert after["resolution_date"] == before["resolution_date"]
    else:
        assert before["resolution_date"] is None
        assert after["resolution_date"] is not None
    assert agent.read(ticket)["status"] == target  # read back


def test_customer_may_close_an_open_ticket(customer_a, ticket):
    response = customer_a.update_ticket(ticket, {"status": "Closed"})
    assert response.status_code == 200
    stored = customer_a.read(ticket)
    assert stored["status"] == "Closed"
    assert stored["status_category"] == "Resolved"
    assert stored["resolution_date"] is not None


@pytest.mark.parametrize(
    ("state", "attempt"),
    [("Open", "Resolved"), ("Replied", "Open"), ("Resolved", "Open"), ("Closed", "Open")],
    ids=["from-Open", "from-Replied", "from-Resolved", "from-Closed"],
)
def test_one_disallowed_change_from_each_state_for_the_customer(customer_a, agent, ticket, state, attempt):
    if state != "Open":
        set_status(agent, ticket, state)
    before = customer_a.read(ticket)

    response = customer_a.update_ticket(ticket, {"status": attempt})

    assert response.status_code == 403
    after = customer_a.read(ticket)
    assert after["status"] == state
    assert after["resolution_date"] == before["resolution_date"]


def test_unknown_status_is_not_a_transition(agent, ticket):
    response = agent.update_ticket(ticket, {"status": "Archived"})
    assert response.status_code == 417
    assert "Could not find Status: Archived" in error_text(response)
    assert agent.read(ticket)["status"] == "Open"


# === Workflow B: BR2, feedback is required to close a resolved ticket ===========


@pytest.fixture
def resolved_with_reply(customer_a, agent, site, ticket):
    site.add_agent_reply(ticket, agent.email, customer_a.email)
    set_status(agent, ticket, "Resolved")
    return ticket


def test_customer_cannot_close_a_resolved_ticket_without_feedback(customer_a, resolved_with_reply):
    response = customer_a.update_ticket(resolved_with_reply, {"status": "Closed"})
    assert response.status_code == 417
    assert "Ticket must be resolved with a feedback" in error_text(response)
    stored = customer_a.read(resolved_with_reply)
    assert stored["status"] == "Resolved"
    assert stored["feedback"] is None


def test_customer_closes_a_resolved_ticket_with_feedback(customer_a, resolved_with_reply):
    before = customer_a.read(resolved_with_reply)
    response = customer_a.update_ticket(resolved_with_reply, {"status": "Closed", "feedback": FEEDBACK})
    assert response.status_code == 200
    stored = customer_a.read(resolved_with_reply)
    assert stored["status"] == "Closed"
    assert stored["feedback"] == FEEDBACK
    assert stored["feedback_rating"] == FEEDBACK_RATING
    assert stored["resolution_date"] == before["resolution_date"]  # BR3: closing keeps it


def test_feedback_is_not_required_before_any_agent_reply(customer_a, agent, ticket):
    set_status(agent, ticket, "Resolved")
    assert customer_a.update_ticket(ticket, {"status": "Closed"}).status_code == 200
    assert customer_a.read(ticket)["status"] == "Closed"


def test_feedback_is_not_required_from_an_agent(agent, resolved_with_reply):
    assert set_status(agent, resolved_with_reply, "Closed")["status"] == "Closed"


def test_feedback_is_not_required_when_the_setting_is_off(customer_a, site, resolved_with_reply):
    site.settings(is_feedback_mandatory=0)
    try:
        response = customer_a.update_ticket(resolved_with_reply, {"status": "Closed"})
        assert response.status_code == 200
        assert customer_a.read(resolved_with_reply)["status"] == "Closed"
    finally:
        site.settings(is_feedback_mandatory=1)


def test_unknown_feedback_option_is_rejected(customer_a, resolved_with_reply):
    response = customer_a.update_ticket(resolved_with_reply, {"status": "Closed", "feedback": "Five stars"})
    assert response.status_code == 417
    stored = customer_a.read(resolved_with_reply)
    assert stored["status"] == "Resolved"
    assert stored["feedback"] is None


# === Repeated requests ==========================================================


def test_repeating_a_resolve_request_does_not_restamp_the_resolution_date(agent, ticket):
    first = set_status(agent, ticket, "Resolved")
    second = set_status(agent, ticket, "Resolved")
    assert second["resolution_date"] == first["resolution_date"]


def test_repeating_an_assignment_does_not_assign_twice(agent, site, ticket):
    for _ in range(3):
        assert agent.assign_agent(assign_body(ticket, agent.email)).status_code == 200
    assert agent.assignees(ticket) == [agent.email]
    open_todos = site.count(
        "ToDo", {"reference_type": "HD Ticket", "reference_name": ticket, "status": "Open"}
    )
    assert open_todos == 1


def test_repeating_a_close_request_keeps_one_closed_ticket(customer_a, ticket):
    assert customer_a.update_ticket(ticket, {"status": "Closed"}).status_code == 200
    first = customer_a.read(ticket)
    # the second identical request is refused (the ticket is now closed) and changes nothing
    assert customer_a.update_ticket(ticket, {"status": "Closed"}).status_code in (200, 403)
    second = customer_a.read(ticket)
    assert second["status"] == "Closed"
    assert second["resolution_date"] == first["resolution_date"]


@weakness("W-API-04", "an identical create request sent twice makes two tickets; there is no idempotency key")
def test_repeating_a_create_request_does_not_duplicate_the_ticket(customer_a, site):
    body = {"doc": {"subject": "Double submit W-API-04", "description": "<p>sent twice</p>"}}
    assert customer_a.create_ticket(body).status_code == 200
    assert customer_a.create_ticket(body).status_code == 200
    assert site.count("HD Ticket", {"subject": "Double submit W-API-04"}) == 1


# === Endpoint weaknesses ========================================================


@weakness("W-API-05", "the ticket's customer can assign an agent to it (200); assignment is an agent action")
def test_customer_cannot_assign_an_agent(customer_a, agent, ticket):
    response = customer_a.assign_agent(assign_body(ticket, agent.email))
    assert response.status_code == 403
    assert agent.assignees(ticket) == []


@weakness("W-API-06", "a ticket can be assigned to a customer account, which then gains read access to it")
def test_ticket_cannot_be_assigned_to_a_non_agent(customer_b, agent, ticket):
    response = agent.assign_agent(assign_body(ticket, customer_b.email))
    assert response.status_code in (403, 417)
    assert customer_b.get_ticket({"name": ticket}).status_code == 403


@weakness("W-API-07", "a customer can rate a ticket that is still open and is then locked out of closing it")
def test_rating_an_open_ticket_does_not_lock_the_customer_out(customer_a, ticket):
    rated = customer_a.update_ticket(ticket, {"feedback": FEEDBACK})
    closed = customer_a.update_ticket(ticket, {"status": "Closed"})
    assert rated.status_code == 403 or closed.status_code == 200


@weakness("W-API-08", "an agent can overwrite the server-computed resolution date through the API")
def test_resolution_date_cannot_be_written_directly(agent, ticket):
    agent.update_ticket(ticket, {"resolution_date": "2020-01-01 00:00:00"})
    assert agent.read(ticket)["resolution_date"] is None


@weakness("W-API-02", "a request without the `doc` argument returns 500 with a traceback instead of a 4xx")
def test_create_without_a_document_is_a_client_error(customer_a):
    response = customer_a.call("createTicket", "POST", NEW, json={})
    assert 400 <= response.status_code < 500


@weakness("W-API-09", "moving a ticket to a team (agent_group) returns 500 IndexError")
def test_agent_can_route_a_ticket_to_a_team(agent, ticket):
    response = agent.update_ticket(ticket, {"agent_group": "Billing"})
    assert response.status_code == 200
    assert agent.read(ticket)["agent_group"] == "Billing"
