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
    # print("\n\n", parent_field, "\n\n")
    # print("\n\n", child_field, "\n\n")
    # print("\n\n", parent_child_mapping, "\n\n")
    func = generate_on_change_function(
        parent_child_mapping=frappe.parse_json(parent_child_mapping),
        parent_field=parent_field,
        child_field=child_field,
    )

    script_doc = frappe.new_doc("HD Form Script")
    script_doc.script = add_function_to_script(
        script_doc.script, func, parent_field, child_field
    )

    # script_doc.save()


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
    # one more line here
    script += "\n"
    return script


def add_function_to_script(script, func, parent_field, child_field):
    # print('\n\n',script,'\n\n')
    # print('\n\n',func,'\n\n')
    # print('\n\n',parent_field,'\n\n')
    # print('\n\n',child_field,'\n\n')
    # Add function above the return statement
    match = re.search(r"return\s*{", script)
    if match:
        insert_position = match.start()
        print("\n\n", match.start(), "\n\n")
        # take evertything before the position, add function, take everythin after the position
        script = script[:insert_position] + "\n    " + func + script[insert_position:]

    return script
