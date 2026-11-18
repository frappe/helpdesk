"""Shared helpers for the team's white-box unit tests.

These tests run without a site or database. The functions under test are the
real ones from the Helpdesk source; only their collaborators (the `frappe`
module, `is_agent`, the clock) are replaced with test doubles so that every
branch can be driven deliberately.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import frappe
import pytest


class Thrown(Exception):
    """Raised by the fake `frappe.throw` so tests can inspect message and type."""

    def __init__(self, message, exc=None):
        super().__init__(message)
        self.message = message
        self.exc = exc


def make_fake_frappe(user="customer@example.com", roles=()):
    """A stand-in for the `frappe` module as seen by one module under test."""
    fake = MagicMock(name="frappe")
    fake.session = SimpleNamespace(user=user)
    fake.get_roles.return_value = list(roles)
    fake.PermissionError = frappe.PermissionError
    fake.ValidationError = frappe.ValidationError
    fake._dict = frappe._dict

    def throw(message, exc=None, *args, **kwargs):
        raise Thrown(message, exc)

    fake.throw.side_effect = throw
    return fake


class DocStub:
    """Minimal document: only the Document API the business rules rely on."""

    def __init__(self, new=False, changed=(), before=None, **fields):
        self._new = new
        self._changed = set(changed)
        self._before = before
        self.flags = frappe._dict()
        for key, value in fields.items():
            setattr(self, key, value)

    def is_new(self):
        return self._new

    def has_value_changed(self, fieldname):
        return fieldname in self._changed

    def get_doc_before_save(self):
        return self._before

    def get(self, fieldname, default=None):
        return getattr(self, fieldname, default)


def borrow(stub_cls, source_cls, *names):
    """Attach the real, unmodified methods of `source_cls` to a stub class."""
    for name in names:
        setattr(stub_cls, name, source_cls.__dict__[name])
    return stub_cls


def field(fieldname, fieldtype="Data", permlevel=0):
    return SimpleNamespace(fieldname=fieldname, fieldtype=fieldtype, permlevel=permlevel)


def fresh(text):
    """An equal but distinct string object, like a value read from the database.

    Literals in a test file are the same object as the literal in the source,
    so a mutant that swaps `==` for `is` would pass unnoticed with them.
    """
    copy = "".join(list(text))
    assert copy == text and copy is not text
    return copy


@pytest.fixture(autouse=True)
def untranslated_messages(monkeypatch):
    """`_()` needs a site to load translations. Messages are asserted in the
    source language, so translation is replaced by the identity function."""
    import helpdesk.helpdesk.doctype.hd_ticket.customer_edit_controller as cec
    import helpdesk.helpdesk.doctype.hd_ticket.hd_ticket as hd_ticket
    import helpdesk.helpdesk.doctype.hd_ticket_status.hd_ticket_status as hts

    for module in (cec, hd_ticket, hts):
        monkeypatch.setattr(module, "_", lambda message, *args, **kwargs: message)
