import frappe

DEFAULT_PRESET = "Soft Grain"
NEW_PRESET = {
    "Blue": "Mesh Blue",
    "Violet": "Aurora Dusk",
}


def execute():
    """Move the knowledge base banner off presets that no longer exist."""
    preset = frappe.db.get_single_value("HD Settings", "banner_preset")
    options = frappe.get_meta("HD Settings").get_options("banner_preset").split("\n")
    if preset and preset not in options:
        frappe.db.set_single_value(
            "HD Settings", "banner_preset", NEW_PRESET.get(preset, DEFAULT_PRESET)
        )
