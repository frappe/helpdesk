"""Tasky permission rules — non-PM roles see only assigned tasks on ERPNext Task."""

import frappe


def task_permission_query(user=None):
    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return None

    is_pm = frappe.db.exists("Project User", {"user": user})
    if is_pm:
        return None

    return f'`tabTask`.`_assign` LIKE "%{user}%"'


def has_task_permission(doc, ptype=None, user=None):
    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return True

    is_pm = frappe.db.exists("Project User", {"user": user})
    if is_pm:
        return True

    assigned = doc.get("_assign") or ""
    return user in assigned
