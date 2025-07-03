# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketPriority(Document):
    def before_save(self):
        priority_in_sla = frappe.db.get_value(
            "HD Service Level Priority", {"priority": self.name}
        )
        if priority_in_sla:
            return
        frappe.msgprint(
            msg=_(
                "Please add this priority in the <a href='/app/hd-service-level-agreement'>required SLA documents</a>"
            ),
            title=_("Action Required"),
            indicator="orange",
        )
