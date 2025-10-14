from __future__ import annotations

import frappe

from helpdesk.api.otto.summary import default_summary_config
from helpdesk.api.otto.types import FeatureConfig, FeatureFlags, Summary


@frappe.whitelist()
def can_use_otto() -> bool:
    try:
        frappe.get_meta("Otto Settings")
    except Exception:
        return False

    return True


@frappe.whitelist()
def is_enabled() -> bool:
    return bool(frappe.get_single_value("HD Settings", "enable_ai_features"))


@frappe.whitelist()
def get_enabled_features() -> FeatureFlags:
    enabled_features = FeatureFlags(summary=False)

    if not can_use_otto() or not is_enabled():
        return enabled_features

    conf = get_feature_config()

    enabled_features["summary"] = conf.get("summary", {}).get("enabled", False)
    return enabled_features


@frappe.whitelist()
def get_feature_config() -> FeatureConfig:
    import json

    val = frappe.get_single_value("HD Settings", "ai_feature_config") or "{}"
    conf = json.loads(val)

    if not conf.get("summary"):
        conf["summary"] = default_summary_config

    return conf


@frappe.whitelist()
def set_feature_config(config: dict) -> None:
    import json

    val = json.dumps(config, indent=2)
    frappe.db.set_value("HD Settings", "HD Settings", "ai_feature_config", val)


@frappe.whitelist()
def summarize_ticket(ticket_id: str):
    return {"message": "Summarized ticket"}


@frappe.whitelist()
def get_summaries(ticket: str) -> list[Summary]:
    if not get_enabled_features().get("summary"):
        return []

    import frappe.utils

    last = Summary(
        creation=frappe.utils.now(),
        summarizer="Lin Flo",
        summarized_by="lin.flo@example.com",
        content=to_html(
            "### This is a test summary\n\nThis is a test summary\nThis is a test summary"
        ),
        snippet="This is a test snippet",
    )
    return [last]


def to_html(content: str):
    """Converts provided markdown to HTML"""
    from markdown2 import markdown

    extras = {
        "fenced-code-blocks": None,
        "tables": None,
        "strike": None,
        "cuddled-lists": None,
        "footnotes": None,
        "header-ids": None,
        "target-blank-links": None,
        "html-classes": {"table": "table table-bordered", "img": "screenshot"},
    }

    return markdown(content, extras=extras)
