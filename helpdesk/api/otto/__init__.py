import frappe


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
def get_feature_config() -> dict:
    import json

    val = frappe.get_single_value("HD Settings", "ai_feature_config") or "{}"
    return json.loads(val)


@frappe.whitelist()
def set_feature_config(config: dict) -> None:
    import json

    val = json.dumps(config, indent=2)
    frappe.db.set_value("HD Settings", "HD Settings", "ai_feature_config", val)
