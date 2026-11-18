"""Controlled failure and recovery of the two state-changing operations.

A test double makes a dependency unavailable *after* the ticket row has been
written inside the transaction but *before* the request commits. The test
then does what Frappe's request handler does on an exception (roll back),
checks the persisted state, restores the dependency, retries the same
request, and checks the final state has no duplicates.

  R1  workflow A, raise a ticket: file storage is unavailable while the
      description's inline media are attached (HDTicket.after_insert ->
      handle_inline_media_new_ticket). By then the ticket and its first
      message are already inserted.
  R2  workflow B, resolve a ticket: the telemetry client is unavailable
      (HDTicket.on_update -> capture_event). By then the status row has
      been updated.

The operations run in-process against the same site so the failure can be
placed precisely; the final state is read back over HTTP as a user would.
"""

import uuid
from unittest.mock import patch

import pytest

import helpdesk.helpdesk.doctype.hd_ticket.hd_ticket as hd_ticket_module
from helpdesk.helpdesk.doctype.hd_ticket import api as ticket_api
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket


class FileStorageUnavailable(OSError):
    pass


class TelemetryUnavailable(ConnectionError):
    pass


@pytest.fixture
def acting_as(site):
    """Run in-process code as a given user, then switch back."""
    frappe = site.frappe

    def switch(email):
        frappe.set_user(email)

    yield switch
    frappe.db.rollback()
    frappe.set_user("Administrator")


def messages_on(frappe, ticket):
    return frappe.db.count("Communication", {"reference_doctype": "HD Ticket", "reference_name": ticket})


def test_r1_raise_ticket_recovers_from_file_storage_outage(site, customer_a, acting_as):
    frappe = site.frappe
    marker = uuid.uuid4().hex[:10]
    subject = f"Recovery R1 {marker}"
    request = {"subject": subject, "description": f"<p>Printer jam {marker}</p>"}
    seen = {}

    def storage_outage(self):
        # state inside the transaction at the moment the dependency fails
        seen["name"] = self.name
        seen["ticket_written"] = bool(frappe.db.exists("HD Ticket", self.name))
        seen["messages_written"] = messages_on(frappe, self.name)
        raise FileStorageUnavailable("file storage unavailable")

    site.fresh()
    acting_as(customer_a.email)

    # 1. the dependency fails before the write completes
    with patch.object(HDTicket, "handle_inline_media_new_ticket", storage_outage):
        with pytest.raises(FileStorageUnavailable):
            ticket_api.new(dict(request))
    frappe.db.rollback()  # Frappe's request handler rolls back on any exception

    assert seen["ticket_written"] is True, "the failure must come after the ticket row was written"
    assert seen["messages_written"] == 1, "...and after its first message was written"

    # 2. persisted state after the failure: nothing half-written
    site.fresh()
    assert frappe.db.count("HD Ticket", {"subject": subject}) == 0
    assert not frappe.db.exists("HD Ticket", seen["name"])
    assert frappe.db.count("Communication", {"content": ["like", f"%{marker}%"]}) == 0

    # 3. dependency restored, the same request retried
    acting_as(customer_a.email)
    created = ticket_api.new(dict(request))
    frappe.db.commit()

    # 4. final state: exactly one ticket with exactly one message
    site.fresh()
    assert frappe.db.count("HD Ticket", {"subject": subject}) == 1
    assert messages_on(frappe, created["name"]) == 1
    assert frappe.db.count("Communication", {"content": ["like", f"%{marker}%"]}) == 1
    # the rolled-back number was released and reused: no gap, no duplicate
    assert created["name"] == seen["name"]
    stored = customer_a.read(created["name"])  # over HTTP, as the customer
    assert stored["subject"] == subject
    assert stored["status"] == "Open"
    assert stored["raised_by"] == customer_a.email


def test_r2_resolve_ticket_recovers_from_telemetry_outage(site, customer_a, agent, acting_as):
    frappe = site.frappe
    name = customer_a.new_ticket(subject=f"Recovery R2 {uuid.uuid4().hex[:10]}")
    site.fresh()
    versions_before = frappe.db.count("Version", {"ref_doctype": "HD Ticket", "docname": name})
    seen = {}

    def telemetry_outage(event):
        seen["status_in_transaction"] = frappe.db.get_value("HD Ticket", name, "status")
        raise TelemetryUnavailable("telemetry service unavailable")

    # 1. the dependency fails after the status row is updated, before commit
    acting_as(agent.email)
    ticket = frappe.get_doc("HD Ticket", name)
    ticket.status = "Resolved"
    with patch.object(hd_ticket_module, "capture_event", telemetry_outage):
        with pytest.raises(TelemetryUnavailable):
            ticket.save()
    frappe.db.rollback()
    assert seen["status_in_transaction"] == "Resolved", "the failure must come after the row was updated"

    # 2. persisted state after the failure: the ticket is untouched
    site.fresh()
    after_failure = frappe.db.get_value("HD Ticket", name, ["status", "resolution_date"], as_dict=True)
    assert after_failure.status == "Open"
    assert after_failure.resolution_date is None
    assert frappe.db.count("Version", {"ref_doctype": "HD Ticket", "docname": name}) == versions_before

    # 3. dependency restored, the same change retried as a new request
    acting_as(agent.email)
    ticket = frappe.get_doc("HD Ticket", name)
    ticket.status = "Resolved"
    ticket.save()
    frappe.db.commit()

    # 4. final state: resolved once, one history entry for the change
    site.fresh()
    final = frappe.db.get_value("HD Ticket", name, ["status", "resolution_date"], as_dict=True)
    assert final.status == "Resolved"
    assert final.resolution_date is not None
    assert frappe.db.count("Version", {"ref_doctype": "HD Ticket", "docname": name}) == versions_before + 1
    stored = agent.read(name)  # over HTTP, as the agent
    assert stored["status"] == "Resolved"
    assert stored["resolution_date"] is not None
