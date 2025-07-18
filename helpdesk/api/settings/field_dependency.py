import frappe
from frappe import _


@frappe.whitelist()
def get_fields_meta(doctype="HD Ticket", fieldtypes=None):
    """
    Returns the metadata for the given doctype.
    """

    all_fields = frappe.get_meta(doctype).fields
    if not fieldtypes:
        return all_fields
    fields = []
    for field in all_fields:
        if field.fieldtype in fieldtypes:
            fields.append(field)
    return fields


@frappe.whitelist()
def create_field_dependency(parent_field, child_field, parent_child_mapping):
    frappe.has_permission("HD Form Script", "create", throw=True)
    if not parent_field or not child_field or not parent_child_mapping:
        frappe.throw(
            _("Parent field, child field, and parent-child mapping are required.")
        )

    func = generate_on_change_function(
        parent_child_mapping=frappe.parse_json(parent_child_mapping),
        parent_field=parent_field,
        child_field=child_field,
    )

    script_doc = get_or_create_standard_form_script(parent_field, child_field)
    script_doc.script = add_function_to_script(
        parent_field,
        child_field,
        func,
    )

    script_doc.save()


def get_or_create_standard_form_script(parent_field, child_field):
    if existing_doc := frappe.db.exists(
        "HD Form Script",
        {"name": ["like", f"Field Dependency-{parent_field}-{child_field}"]},
    ):
        return frappe.get_doc("HD Form Script", existing_doc)
    else:
        doc = frappe.new_doc("HD Form Script")
        doc.is_standard = 1
        doc.enabled = 1
        doc.name = f"Field Dependency-{parent_field}-{child_field}"
        return doc


def generate_on_change_function(parent_child_mapping, parent_field, child_field):
    script = f"function update_{child_field}(value){{\n"
    for parent, children in parent_child_mapping.items():
        # replace '' with ""
        options = ",".join([f'"{child}"' for child in children])
        script += f'        if(value=="{parent}"){{\n'
        script += f"            options = [{options}]\n"
        script += f'            applyFilters("{child_field}",options)\n'
        script += "        }\n"
        script += "\n"
    script += "    }\n"
    script += "\n"
    return script


def add_function_to_script(parent_field, child_field, func):
    script = "function setupForm({doc, updateField, call, router, toast, $dialog, createToast ,applyFilters}) {"
    script += "\n"
    script += "\n"
    script += f"    {func}"
    script += "\n"
    script += f"""   return {{
        onChange: {{
            {parent_field}: (newVal) => update_{child_field}(newVal)
        }}
    }}
    """
    script += "\n"
    script += "}"
    print("\n\n", script, "\n\n")
    return script


def find_closing_brace_position(script, start_pos):
    """
    Find the position of the closing brace that matches the opening brace at start_pos
    Returns the position of the closing brace, or None if not found
    """
    brace_count = 0
    for i in range(start_pos, len(script)):
        if script[i] == "{":
            brace_count += 1
        elif script[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                return i
    return None
