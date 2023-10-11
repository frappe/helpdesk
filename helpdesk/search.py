# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import json
import re

import frappe
from frappe.utils import cstr, update_progress_bar
from redis.commands.search.field import TagField, TextField
from redis.commands.search.indexDefinition import IndexDefinition
from redis.commands.search.query import Query
from redis.exceptions import ResponseError

from helpdesk.utils import is_agent


class Search:
	unsafe_chars = re.compile(r"[\[\]{}<>+]")

	def __init__(self, index_name, prefix, schema) -> None:
		self.redis = frappe.cache()
		self.index_name = index_name
		self.prefix = prefix
		self.schema = []
		for field in schema:
			self.schema.append(frappe._dict(field))

	def create_index(self):
		index_def = IndexDefinition(
			prefix=[f"{self.redis.make_key(self.prefix).decode()}:"],
		)
		schema = []
		for field in self.schema:
			kwargs = {
				k: v
				for k, v in field.items()
				if k in ["weight", "sortable", "no_index", "no_stem"]
			}
			if field.type == "tag":
				schema.append(TagField(field.name, **kwargs))
			else:
				schema.append(TextField(field.name, **kwargs))

		self.redis.ft(self.index_name).create_index(schema, definition=index_def)
		self._index_exists = True

	def add_document(self, id, doc, payload=None):
		doc = frappe._dict(doc)
		doc_id = self.redis.make_key(f"{self.prefix}:{id}").decode()
		mapping = {}
		for field in self.schema:
			if field.name in doc:
				mapping[field.name] = cstr(doc[field.name])
		if self.index_exists():
			self.redis.ft(self.index_name).add_document(
				doc_id, payload=json.dumps(payload), replace=True, **mapping
			)

	def remove_document(self, id):
		key = self.redis.make_key(f"{self.prefix}:{id}").decode()
		if self.index_exists():
			self.redis.ft(self.index_name).delete_document(key)

	def search(
		self,
		query,
		start=0,
		page_length=50,
		sort_by=None,
		highlight=False,
		with_payloads=False,
	):
		query = self.clean_query(query)
		query = Query(query).paging(start, page_length)
		if highlight:
			query = query.highlight(tags=["<mark>", "</mark>"])
		if sort_by:
			parts = sort_by.split(" ")
			sort_field = parts[0]
			direction = parts[1] if len(parts) > 1 else "asc"
			query = query.sort_by(sort_field, asc=direction == "asc")
		if with_payloads:
			query = query.with_payloads()

		try:
			result = self.redis.ft(self.index_name).search(query)
		except ResponseError as e:
			print(e)
			return frappe._dict({"total": 0, "docs": [], "duration": 0})

		out = frappe._dict(docs=[], total=result.total, duration=result.duration)
		for doc in result.docs:
			id = doc.id.split(":", 1)[1]
			_doc = frappe._dict(doc.__dict__)
			_doc.id = id
			_doc.payload = json.loads(doc.payload) if doc.payload else None
			out.docs.append(_doc)
		return out

	def clean_query(self, query):
		query = query.strip().replace("-*", "*")
		query = self.unsafe_chars.sub(" ", query)
		query = query.strip()
		return query

	def spellcheck(self, query, **kwargs):
		return self.redis.ft(self.index_name).spellcheck(query, **kwargs)

	def drop_index(self):
		if self.index_exists():
			self.redis.ft(self.index_name).dropindex(delete_documents=True)

	def index_exists(self):
		self._index_exists = getattr(self, "_index_exists", None)
		if self._index_exists is None:
			try:
				self.redis.ft(self.index_name).info()
				self._index_exists = True
			except ResponseError:
				self._index_exists = False
		return self._index_exists


class HelpdeskSearch(Search):
	schema = [
		{"name": "name", "weight": 5},
		{"name": "subject", "weight": 2},
		{"name": "description", "weight": 1},
		{"name": "team", "type": "tag"},
		{"name": "modified", "sortable": True},
		{"name": "creation", "sortable": True},
	]

	def __init__(self):
		super().__init__("helpdesk_idx", "search_doc", self.schema)

	def build_index(self):
		self.drop_index()
		self.create_index()
		records = self.get_records()
		total = len(records)
		for i, doc in enumerate(records):
			self.index_doc(doc)
			if not hasattr(frappe.local, "request"):
				update_progress_bar("Indexing", i, total)

	def index_doc(self, doc):
		id = f"{doc.doctype}:{doc.name}"
		fields, payload = None, None
		if doc.doctype == "HD Ticket":
			fields = {
				"doctype": doc.doctype,
				"name": doc.name,
				"subject": doc.subject,
				"team": doc.agent_group,
				"modified": doc.modified,
			}
			payload = {
				"subject": doc.subject,
				"team": doc.agent_group,
			}
		if fields and payload:
			self.add_document(id, fields, payload)

	def remove_doc(self, doc):
		key = f"{doc.doctype}:{doc.name}"
		self.remove_document(key)

	def get_records(self):
		records = []
		for d in frappe.db.get_all(
			"HD Ticket",
			fields=[
				"name",
				"subject",
				"description",
				"agent_group",
				"modified",
				"creation",
			],
		):
			d.doctype = "HD Ticket"
			records.append(d)
		return records


@frappe.whitelist()
def search(query):
	if not is_agent():
		return []
	search = HelpdeskSearch()
	query = search.clean_query(query)
	query_parts = query.split(" ")
	if len(query_parts) == 1 and not query_parts[0].endswith("*"):
		query = f"{query_parts[0]}*"
	if len(query_parts) > 1:
		query = " ".join([f"%%{q}%%" for q in query_parts])
	result = search.search(query, start=0, sort_by="modified desc", with_payloads=True)
	groups = {}
	for r in result.docs:
		doctype, name = r.id.split(":")
		r.doctype = doctype
		r.name = name
		if doctype == "HD Ticket":
			groups.setdefault("Tickets", []).append(r)
	out = []
	for key in groups:
		out.append({"title": key, "items": groups[key]})
	return out


def build_index():
	frappe.cache().set_value("helpdesk_search_indexing_in_progress", True)
	search = HelpdeskSearch()
	search.build_index()
	frappe.cache().set_value("helpdesk_search_indexing_in_progress", False)


def build_index_in_background():
	if not frappe.cache().get_value("helpdesk_search_indexing_in_progress"):
		frappe.enqueue(build_index, queue="long")


def build_index_if_not_exists():
	search = HelpdeskSearch()
	if not search.index_exists():
		build_index()
