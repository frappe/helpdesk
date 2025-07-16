import re

import frappe
from frappe import _


@frappe.whitelist()
def get_fields_meta(doctype="HD Ticket", fieldtypes=None):
    """
    Returns the metadata for the given doctype.
    """

    all_fields = frappe.get_meta(doctype).fields
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

    script_doc = get_or_create_standard_form_script()
    script_doc.script = add_function_to_script(
        script_doc.script, func, parent_field, child_field
    )

    script_doc.save()


def get_or_create_standard_form_script():
    if existing_doc := frappe.db.exists("HD Form Script", {"is_standard": 1}):
        return frappe.get_doc("HD Form Script", existing_doc)
    else:
        doc = frappe.new_doc("HD Form Script")
        doc.is_standard = 1
        doc.enabled = 1
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
    script += "    }\n"
    script += "\n"
    return script


def add_function_to_script(script, func, parent_field, child_field):
    # Add function above the return statement
    match = re.search(r"return\s*{", script)
    if match:
        insert_position = match.start()
        script = (
            script[:insert_position] + "\n    " + func + "\n" + script[insert_position:]
        )

    # Check if the script value is default (true for new_doc)
    if re.search(r"actions:\s*\[\s*\]", script):
        script = handle_new_doc_script(script, parent_field, child_field)
    else:
        script = handle_existing_doc_script(script, parent_field, child_field)
    return script


def handle_new_doc_script(script, parent_field, child_field):
    return_match = re.search(r"return\s*{", script)
    if return_match:
        start_pos = return_match.start()
        pos = return_match.end() - 1
        ending_pos = find_closing_brace_position(script, pos)
        if ending_pos:
            ending_pos += 1
            new_return_block = f"""return {{
        onChange: {{
            {parent_field}: (newVal) => update_{child_field}(newVal),
        }}
    }}"""
            script = script[:start_pos] + new_return_block + script[ending_pos:]
    return script


def handle_existing_doc_script(script, parent_field, child_field):
    onChange_match = re.search(r"onChange\s*:\s*{", script)
    if not onChange_match:
        return script

    pos = onChange_match.end() - 1
    ending_pos = find_closing_brace_position(script, pos)
    if not ending_pos:
        return script

    onChange_content = script[onChange_match.end() : ending_pos]
    if onChange_content.strip():
        new_field = (
            f"\n            {parent_field}: (newVal) => update_{child_field}(newVal),"
        )
        script = script[:ending_pos] + new_field + "\n        " + script[ending_pos:]
    else:
        new_field = f"\n            {parent_field}: (newVal) => update_{child_field}(newVal),\n        "
        script = script[:ending_pos] + new_field + script[ending_pos:]

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
