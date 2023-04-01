# Copyright (c) 2017, Frappe and Contributors
# License: GNU General Public License v3. See license.txt


import frappe


def execute():
	for category in frappe.get_all("Category", pluck="name"):
		category_doc = frappe.get_doc("Category", category)
		category_doc.route = category_doc.get_page_route()
		category_doc.save()

	for article in frappe.get_all("Article", pluck="name"):
		article_doc = frappe.get_doc("Article", article)
		article_doc.route = article_doc.get_page_route()
		article_doc.save()
