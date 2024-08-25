# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
import frappe

# from frappe import _


# nosemgrep
def setup_complete(args=None):

    email = args.get("email") or frappe.session.user
    if not email:
        return
    # Create first Agent for the user
    new_user = frappe.db.get_list(
        "User", filters={"email": email}, limit=1, pluck="name"
    )
    if not new_user:
        return
    new_user = new_user[0]
    new_agent = frappe.new_doc("HD Agent")
    new_agent.user = new_user
    new_agent.insert(ignore_if_duplicate=True)
