import time
from urllib.parse import urljoin

import frappe
import requests
from frappe.utils.data import validate_egress_url
from urllib3.util import parse_url

LIVE_TIMEOUT = 2
SYNC_TIMEOUT = 10
MAX_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 3
SKIP_SECONDS = 60
DOWN_KEY = "docs_source_down"
HEADERS = {"User-Agent": "helpdesk-docs-source"}
DOWN_STATUSES = (502, 503, 504)
CHUNK_SIZE = 8 * 1024


class DocsFetchError(Exception):
    def __init__(self, message, status: int | None = None, transient: bool = False):
        super().__init__(message)
        self.status = status
        self.transient = transient


def fetch(
    url: str, host: str, timeout: float = SYNC_TIMEOUT, params: dict | None = None
) -> requests.Response:
    """GET url over https, same host only, with `timeout` as a total deadline."""
    deadline = time.monotonic() + timeout
    for _ in range(MAX_REDIRECTS + 1):
        response = _get(url, host, deadline, params)
        if not response.is_redirect:
            _read_body(response, deadline)
            return response
        url = _redirect_url(url, response)
        params = None
    raise DocsFetchError("Too many redirects")


def fetch_live(url: str, host: str, params: dict | None = None) -> requests.Response:
    """fetch for page loads: short timeout, skips the source for a while after an outage."""
    if frappe.cache.get_value(DOWN_KEY):
        raise DocsFetchError("Docs source is down", transient=True)
    try:
        return fetch(url, host, LIVE_TIMEOUT, params)
    except DocsFetchError as e:
        if e.transient or e.status in DOWN_STATUSES:
            frappe.cache.set_value(DOWN_KEY, 1, expires_in_sec=SKIP_SECONDS)
        raise


def _get(url, host, deadline, params):
    try:
        # Validate and send the same prepared URL, so no parser can disagree about the host.
        prepared = requests.Request("GET", url, params=params).prepare().url
        parsed = parse_url(prepared)
        # https only with verify on: a DNS-rebound host fails the certificate check.
        if parsed.scheme != "https" or parsed.host != host:
            raise DocsFetchError(f"Refusing {parsed.scheme}://{parsed.host}")
        validate_egress_url(prepared)
        return requests.get(
            prepared,
            headers=HEADERS,
            timeout=_remaining(deadline),
            stream=True,
            allow_redirects=False,
            verify=True,
        )
    except (requests.RequestException, ValueError) as e:
        raise _as_fetch_error(e) from e


def _redirect_url(url, response):
    try:
        return urljoin(url, response.headers["Location"])
    except ValueError as e:
        raise DocsFetchError(str(e)) from e
    finally:
        response.close()


def _read_body(response, deadline):
    try:
        if response.status_code >= 300:
            raise DocsFetchError(f"HTTP {response.status_code}", status=response.status_code)
        body = b""
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            body += chunk
            if len(body) > MAX_BYTES:
                raise DocsFetchError("Response too large")
            _remaining(deadline)
        response._content = body
        response._content_consumed = True
    except requests.RequestException as e:
        response.close()
        raise _as_fetch_error(e) from e
    except Exception:
        response.close()
        raise


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DocsFetchError("Timed out", transient=True)
    return remaining


def _as_fetch_error(e):
    transient = isinstance(
        e, (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError)
    )
    return DocsFetchError(str(e), transient=transient)
