import re

import frappe
from bs4 import BeautifulSoup
from frappe.realtime import get_website_room
from frappe.utils.telemetry import capture as _capture


def is_agent(user: str = frappe.session.user) -> bool:
	"""
	Check whether `user` is an agent

	:param user: User to check against, defaults to current user
	:return: Whether `user` is an agent
	"""
	return bool(frappe.db.exists("HD Agent", {"name": user}))


def publish_event(event: str, data: dict):
	room = get_website_room()
	frappe.publish_realtime(event, message=data, room=room, after_commit=True)


def capture_event(event: str):
	return _capture(event, "helpdesk")


def extract_mentions(html):
	if not html:
		return []
	soup = BeautifulSoup(html, "html.parser")
	mentions = []
	for d in soup.find_all("span", attrs={"class": "mention"}):
		mentions.append(frappe._dict(email=d.get("data-id")))
	return mentions


def alphanumeric_to_int(s: str) -> int | None:
	"""
	Get int from alphanumeric string, using regex
	String example: "foo-123" -> 123

	:param s: Alphanumeric string to be searched for
	:return: Integer if a number is found
	"""
	s = re.search(r"\d+", s)

	if not s:
		return

	return int(s.group(0))
