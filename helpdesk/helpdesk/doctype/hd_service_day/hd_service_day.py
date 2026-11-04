# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

# import frappe
from frappe.model.document import Document


class HDServiceDay(Document):
    def __setup__(self) -> None:
        # Frappe v15 fills empty Time fields with the current time on insert
        self.dont_update_if_missing = ["break_start", "break_end"]
