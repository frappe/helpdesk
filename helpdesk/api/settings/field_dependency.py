# import re

import frappe
from frappe import _


@frappe.whitelist()
def create_field_dependency(parent_field, child_field, parent_child_mapping):
    frappe.has_permission("HD Form Script", "create", throw=True)
    if not parent_field or not child_field or not parent_child_mapping:
        frappe.throw(
            _("Parent field, child field, and parent-child mapping are required.")
        )
    print("\n\n", parent_field, "\n\n")
    print("\n\n", child_field, "\n\n")
    print("\n\n", parent_child_mapping, "\n\n")
    script = generate_on_change_function(
        parent_child_mapping=frappe.parse_json(parent_child_mapping),
        parent_field=parent_field,
        child_field=child_field,
    )
    print("\n\n", script, "\n\n")
    pass


def generate_on_change_function(parent_child_mapping, parent_field, child_field):
    script = f"function update_{parent_field}(value){{\n"
    for parent, children in parent_child_mapping.items():
        # replace '' with ""
        options = ",".join([f'"{child}"' for child in children])
        script += f'    if(value=="{parent}"){{\n'
        script += f"        options = [{options}]\n"
        script += f'        applyFilters("{child_field}",options)\n'
        script += "    }}\n"
    script += "}\n"
    return script
