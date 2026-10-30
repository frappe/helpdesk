"""
Routes tickets raised by a genuine L1 (county officer) straight to their
own region's L2 team, instead of falling through to the generic brand-based
assignment.

Looks up the raiser's Contact record via Contact Email, then reads
Contact.custom_hd_region (a Link to HD Team, populated for the recovered
L1 officers). If found, sets doc.agent_group to that region.

Runs at before_insert, ahead of l2_raised_routing (which only acts on real
HD Agents) and assign_brand_from_email (which only sets agent_group when
it's not already set), so this takes priority for L1 raisers specifically
and is a no-op for anyone else.
"""
import frappe


def route_l1_raised_tickets(doc, method=None):
    raiser = doc.get("raised_by") or frappe.session.user or ""
    if not raiser or raiser in ("Guest", "Administrator"):
        return

    # Only for people who are NOT HD Agents (L1 officers never are, post
    # demotion) -- if they are an agent, l2_raised_routing.py already
    # decides, and we shouldn't override that.
    if frappe.db.exists("HD Agent", raiser):
        return

    contact_name = frappe.db.get_value("Contact Email", {"email_id": raiser}, "parent")
    if not contact_name:
        return

    region = frappe.db.get_value("Contact", contact_name, "custom_hd_region")
    if not region:
        return

    doc.agent_group = region

