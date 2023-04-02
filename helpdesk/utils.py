from bs4 import BeautifulSoup
import frappe
import re


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
