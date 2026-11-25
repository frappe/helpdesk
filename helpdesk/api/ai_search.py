"""The AI search tab's knowledge sources and skills, for System Managers."""

import frappe

from helpdesk import ai_search


@frappe.whitelist()
def get_sources() -> list[dict]:
    frappe.only_for("System Manager")
    return ai_search.get_sources()


@frappe.whitelist(methods=["POST"])
def add_source(
    source_type: str,
    url: str | None = None,
    file_url: str | None = None,
    visibility: str = "Public",
) -> dict:
    frappe.only_for("System Manager")
    return ai_search.add_source(source_type, url, file_url, visibility)


@frappe.whitelist(methods=["POST"])
def remove_source(name: str) -> None:
    frappe.only_for("System Manager")
    ai_search.remove_source(name)


@frappe.whitelist(methods=["POST"])
def resync_source(name: str) -> dict:
    frappe.only_for("System Manager")
    return ai_search.resync_source(name)


@frappe.whitelist(methods=["POST"])
def set_source_visibility(name: str, visibility: str) -> dict:
    frappe.only_for("System Manager")
    return ai_search.set_source_visibility(name, visibility)


@frappe.whitelist()
def get_skills() -> list[dict]:
    frappe.only_for("System Manager")
    return ai_search.get_skills()


@frappe.whitelist(methods=["POST"])
def add_skill(title: str, instructions: str) -> None:
    frappe.only_for("System Manager")
    ai_search.add_skill(title, instructions)


@frappe.whitelist(methods=["POST"])
def remove_skill(title: str) -> None:
    frappe.only_for("System Manager")
    ai_search.remove_skill(title)
