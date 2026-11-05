from urllib.parse import urljoin, urlparse

import frappe
import requests
from frappe.utils.data import validate_egress_url

LIVE_TIMEOUT = 2
SYNC_TIMEOUT = 10
MAX_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 3
SKIP_SECONDS = 60
DOWN_KEY = "docs_source_down"
HEADERS = {"User-Agent": "helpdesk-docs-source"}


class DocsFetchError(Exception):
    pass


def fetch(
    url: str, host: str, timeout: int = SYNC_TIMEOUT, params: dict | None = None
) -> requests.Response:
    """GET url, same host only, no internal addresses, body capped at MAX_BYTES."""
    for _ in range(MAX_REDIRECTS + 1):
        response = _get(url, host, timeout, params)
        if not response.is_redirect:
            _check_response(response)
            return response
        url = urljoin(url, response.headers.get("Location", ""))
        params = None
    raise DocsFetchError("Too many redirects")


def fetch_live(url: str, host: str, params: dict | None = None) -> requests.Response:
    """fetch for page loads: short timeout, skips the source for a while after a failure."""
    if frappe.cache.get_value(DOWN_KEY):
        raise DocsFetchError("Docs source is down")
    try:
        return fetch(url, host, LIVE_TIMEOUT, params)
    except DocsFetchError:
        frappe.cache.set_value(DOWN_KEY, 1, expires_in_sec=SKIP_SECONDS)
        raise


def _get(url, host, timeout, params):
    if urlparse(url).hostname != host:
        raise DocsFetchError(f"Refusing host {urlparse(url).hostname}")
    try:
        validate_egress_url(url)
        return requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=timeout,
            stream=True,
            allow_redirects=False,
        )
    except (requests.RequestException, ValueError) as e:
        raise DocsFetchError(str(e)) from e


def _check_response(response):
    try:
        response.raise_for_status()
        _read_capped(response)
    except requests.RequestException as e:
        raise DocsFetchError(str(e)) from e


def _read_capped(response):
    body = b""
    for chunk in response.iter_content(chunk_size=64 * 1024):
        body += chunk
        if len(body) > MAX_BYTES:
            raise DocsFetchError("Response too large")
    response._content = body
    response._content_consumed = True
