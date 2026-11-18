"""BR1 at integration level: tickets are auto-closed after N days of inactivity.

The ticket is raised and moved to the auto-close status over HTTP (workflows A
and B). The daily job has no HTTP route, so it is run in-process against the
same site, and the result is read back over HTTP.

Test basis (source: close_tickets_after_n_days): a ticket in the configured
status is closed when its newest message is *older than* now minus N days. The
seeded settings are status "Replied" and N = 7. The boundary values come from
the generator's 3-point rule: N-1, N, N+1.
"""

import pytest
from generate_testdata import three_point
from test_rules_and_transitions import weakness

N = 7  # seeded HD Settings.auto_close_after_days
AUTO_CLOSE_STATUS = "Replied"


def waiting_ticket(customer_a, agent, status=AUTO_CLOSE_STATUS):
    name = customer_a.new_ticket(subject="Auto-close boundary")
    if status != "Open":
        assert agent.update_ticket(name, {"status": status}).status_code == 200
    return name


@pytest.mark.parametrize(
    ("days_inactive", "expected_status"),
    list(zip(three_point(N), [AUTO_CLOSE_STATUS, "Closed", "Closed"])),
    ids=["N-1-stays", "N-closes", "N+1-closes"],
)
def test_three_point_boundary_on_days_of_inactivity(customer_a, agent, site, days_inactive, expected_status):
    name = waiting_ticket(customer_a, agent)
    site.age_conversation(name, days_inactive)

    site.run_auto_close()

    stored = agent.read(name)
    assert stored["status"] == expected_status
    if expected_status == "Closed":
        assert stored["status_category"] == "Resolved"
        assert site.auto_close_comments(name) == [
            f"automatically closed the ticket after {N} days of inactivity"
        ]
    else:
        assert stored["resolution_date"] is None
        assert site.auto_close_comments(name) == []


def test_auto_closed_ticket_gets_a_resolution_date_like_any_closed_ticket(customer_a, agent, site):
    """Cross-rule check: BR1's job changes the status that BR3 reacts to.

    Was pinned as weakness D-01 (DEF-01, strict xfail) until the fix PR.
    """
    name = waiting_ticket(customer_a, agent)
    site.age_conversation(name, N + 1)

    site.run_auto_close()

    stored = agent.read(name)
    assert stored["status"] == "Closed"
    assert stored["resolution_date"] is not None


def test_running_the_job_again_does_not_close_or_comment_twice(customer_a, agent, site):
    name = waiting_ticket(customer_a, agent)
    site.age_conversation(name, N + 1)
    site.run_auto_close()
    first = agent.read(name)

    site.run_auto_close()

    second = agent.read(name)
    assert second["status"] == "Closed"
    assert second["resolution_date"] == first["resolution_date"]
    assert len(site.auto_close_comments(name)) == 1


@pytest.mark.parametrize("status", ["Open", "Resolved"])
def test_only_tickets_in_the_configured_status_are_closed(customer_a, agent, site, status):
    name = waiting_ticket(customer_a, agent, status=status)
    site.age_conversation(name, N + 1)

    site.run_auto_close()

    assert agent.read(name)["status"] == status


def test_nothing_is_closed_when_auto_close_is_switched_off(customer_a, agent, site):
    name = waiting_ticket(customer_a, agent)
    site.age_conversation(name, N + 1)
    site.settings(auto_close_tickets=0)
    try:
        site.run_auto_close()
        assert agent.read(name)["status"] == AUTO_CLOSE_STATUS
    finally:
        site.settings(auto_close_tickets=1)


def test_the_threshold_follows_the_setting(customer_a, agent, site):
    """Same ticket age, different N: N=7 leaves a 5-day-old ticket, N=5 closes it."""
    name = waiting_ticket(customer_a, agent)
    site.age_conversation(name, 5)
    site.run_auto_close()
    assert agent.read(name)["status"] == AUTO_CLOSE_STATUS

    site.settings(auto_close_after_days=5)
    try:
        site.run_auto_close()
        assert agent.read(name)["status"] == "Closed"
    finally:
        site.settings(auto_close_after_days=N)


def test_a_new_customer_message_restarts_the_clock(customer_a, agent, site):
    name = waiting_ticket(customer_a, agent)
    site.age_conversation(name, N + 1)
    site.add_agent_reply(name, agent.email, customer_a.email)  # a message dated now
    assert agent.update_ticket(name, {"status": AUTO_CLOSE_STATUS}).status_code == 200

    site.run_auto_close()

    assert agent.read(name)["status"] == AUTO_CLOSE_STATUS


@weakness("W-API-10", "a ticket with no messages at all is never auto-closed, however old it is")
def test_inactive_ticket_without_any_message_is_closed(customer_a, agent, site):
    response = customer_a.create_ticket({"doc": {"subject": "No description, no messages"}})
    name = response.json()["message"]["name"]
    assert agent.update_ticket(name, {"status": AUTO_CLOSE_STATUS}).status_code == 200
    site.age_ticket(name, N + 1)

    site.run_auto_close()

    assert agent.read(name)["status"] == "Closed"
