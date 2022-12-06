from bs4 import BeautifulSoup
import frappe

from pyngrok import ngrok
from frappe.utils import get_url


def extract_mentions(html):
	print(html)
	if not html:
		return []
	soup = BeautifulSoup(html, "html.parser")
	mentions = []
	for d in soup.find_all("span", attrs={"class": "mention"}):
		mentions.append(frappe._dict(email=d.get("data-id")))
	return mentions


def get_public_url(path: str = None, use_ngrok: bool = False):
	"""Returns a public accessible url of a site using ngrok."""
	if frappe.conf.developer_mode and use_ngrok:
		tunnels = ngrok.get_tunnels()
		if tunnels:
			domain = tunnels[0].public_url
		else:
			port = frappe.conf.http_port or frappe.conf.webserver_port
			domain = ngrok.connect(port)
		return "/".join(map(lambda x: x.strip("/"), [domain, path or ""]))
	return get_url(path)
