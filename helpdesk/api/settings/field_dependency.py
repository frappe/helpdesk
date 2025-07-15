import re

import frappe
from frappe import _


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

    script_doc = frappe.new_doc("HD Form Script")
    script_doc.script = add_function_to_script(
        script_doc.script, func, parent_field, child_field
    )
    print("\n\n", script_doc.script, "\n\n")

    script_doc.save()


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
        # take everything before the position, add function, take everything after the position
        script = (
            script[:insert_position] + "\n    " + func + "\n" + script[insert_position:]
        )

    # Check if script has the default return statement with actions: []
    default_return_statement = re.search(r"actions:\s*\[\s*\]", script)

    if default_return_statement:
        # Find the return statement block and replace it entirely
        return_match = re.search(r"return\s*{", script)
        if return_match:
            start_pos = return_match.start()
            # Find the closing brace of the return statement
            pos = return_match.end() - 1  # Start from the opening brace
            ending_pos = find_closing_brace_position(script, pos)

            if ending_pos:
                ending_pos += 1  # Include the closing brace

            if ending_pos:
                new_return_block = f"""return {{
        onChange: {{
            {parent_field}: (newVal) => update_{child_field}(newVal),
        }}
    }}"""
                script = script[:start_pos] + new_return_block + script[ending_pos:]
    else:
        onChange_match = re.search(r"onChange\s*:\s*{", script)
        if onChange_match:
            pos = onChange_match.end() - 1  # Start from the opening brace
            ending_pos = find_closing_brace_position(script, pos)

            if ending_pos:
                # Check if there's already content in onChange block
                onChange_content = script[onChange_match.end() : ending_pos]
                if onChange_content.strip():
                    # Add comma and new field
                    new_field = f"\n            {parent_field}: (newVal) => update_{child_field}(newVal),"
                    script = (
                        script[:ending_pos]
                        + new_field
                        + "\n        "
                        + script[ending_pos:]
                    )
                else:
                    # Empty onChange block, just add the field
                    new_field = f"\n            {parent_field}: (newVal) => update_{child_field}(newVal),\n        "
                    script = script[:ending_pos] + new_field + script[ending_pos:]
        else:
            # No onChange block exists, need to add it to the return statement
            return_match = re.search(r"return\s*{", script)
            if return_match:
                # Find the closing brace of the return statement
                pos = return_match.end() - 1
                ending_pos = find_closing_brace_position(script, pos)

                if ending_pos:
                    # Add onChange block before the closing brace
                    new_onChange_block = f",\n        onChange: {{\n            {parent_field}: (newVal) => update_{child_field}(newVal),\n        }}\n    "
                    script = (
                        script[:ending_pos] + new_onChange_block + script[ending_pos:]
                    )

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
