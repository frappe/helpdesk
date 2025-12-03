# Copyright (c) 2025, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDDashboard(Document):
    pass


@frappe.whitelist()
def get_default_agent_dashboard():
    return '[{"chart":"recently_assigned_tickets","layout":{"x":17,"y":25,"w":17,"h":27,"i":"0.5901090349104408","minW":16,"minH":27,"maxH":27,"moved":false}},{"chart":"recent_feedback","layout":{"x":34,"y":25,"w":16,"h":27,"i":"0.2090867593567277","minW":16,"minH":27,"maxW":27,"maxH":27,"moved":false}},{"chart":"avg_time_metrics","layout":{"x":0,"y":0,"w":50,"h":25,"i":"0.9444757118289221","moved":false,"minW":18,"minH":24,"maxH":44}},{"chart":"upcoming_sla_violations","layout":{"x":0,"y":52,"w":50,"h":25,"i":"0.644411970698438","moved":false,"minW":25,"minH":25,"maxH":25}},{"chart":"pending_tickets","layout":{"x":0,"y":77,"w":50,"h":24,"i":"0.12878740671098265","moved":false,"minW":25,"minH":24,"maxH":24}},{"chart":"avg_resolution_time","layout":{"x":0,"y":43,"w":17,"h":9,"i":"0.17044916608149618","moved":false,"minW":14,"minH":9,"maxH":9}},{"chart":"avg_first_response_time","layout":{"x":0,"y":34,"w":17,"h":9,"i":"0.408504238844829","moved":false,"minW":14,"minH":9,"maxH":9}},{"chart":"agent_tickets","layout":{"x":0,"y":25,"w":17,"h":9,"i":"0.38621973888392136","moved":false,"minW":14,"minH":9,"maxH":9}}]'
