import frappe

from helpdesk.api.otto.types import FeatureConfig, FeatureFlags


@frappe.whitelist()
def can_use_otto() -> bool:
    try:
        frappe.get_meta("Otto Settings")
    except Exception:
        return False

    return True


@frappe.whitelist()
def is_enabled() -> bool:
    return bool(frappe.get_single_value("HD Settings", "enable_smart_features"))


@frappe.whitelist()
def get_enabled_features() -> FeatureFlags:
    enabled_features = FeatureFlags(
        summary=False,
    )

    if not is_enabled() or not can_use_otto():
        return enabled_features

    conf = get_feature_config()

    enabled_features["summary"] = conf.get("summary", {}).get("enabled", False)
    return enabled_features


@frappe.whitelist()
def get_feature_config() -> FeatureConfig:
    import json

    from helpdesk.api.otto.summary import (
        default_summary_config,
        default_summary_guidelines,
    )

    val = frappe.get_single_value("HD Settings", "smart_feature_config") or "{}"
    conf = json.loads(val)

    if not conf.get("summary"):
        conf["summary"] = default_summary_config

    if not conf.get("summary").get("llm"):
        import otto.lib as otto

        conf["summary"]["llm"] = otto.get_model(size="Small")

    if not conf.get("summary").get("guidelines"):
        conf["summary"]["guidelines"] = default_summary_guidelines

    return conf


@frappe.whitelist()
def set_feature_config(config: dict) -> None:
    import json

    val = json.dumps(config, indent=2)
    frappe.db.set_single_value("HD Settings", "smart_feature_config", val)
