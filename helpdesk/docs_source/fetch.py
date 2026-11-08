import time
from urllib.parse import urljoin

import requests
from frappe.utils.data import validate_egress_url
from urllib3.exceptions import HTTPError
from urllib3.util import parse_url

PAGE_TIMEOUT = 10
MAX_BYTES = 5 * 1024 * 1024
MAX_REDIRECTS = 3
# What a docs site may offer: pages listed, and child indexes or sitemaps followed.
MAX_CANDIDATES = 2000
MAX_CHILDREN = 5
HEADERS = {"User-Agent": "helpdesk-docs-source"}
CHUNK_SIZE = 8 * 1024


class DocsFetchError(Exception):
    def __init__(self, message, status: int | None = None, transient: bool = False):
        super().__init__(message, status, transient)
        self.status = status
        self.transient = transient

    def __str__(self) -> str:
        return self.args[0]


def fetch(url: str, host: str) -> requests.Response:
    """GET url over https, same host only, with PAGE_TIMEOUT as a total deadline."""
    deadline = time.monotonic() + PAGE_TIMEOUT
    for _ in range(MAX_REDIRECTS + 1):
        response = _get(url, host, deadline)
        if not response.is_redirect:
            _read_body(response, deadline)
            return response
        url = _redirect_url(url, response)
    raise DocsFetchError("Too many redirects")


def _get(url, host, deadline):
    # ponytail: header drip and DNS lookup are not bounded here, the worker timeout caps them.
    try:
        # Validate and send the same prepared URL, so no parser can disagree about the host.
        prepared = requests.Request("GET", url).prepare().url
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
            raise DocsFetchError(
                f"HTTP {response.status_code}", status=response.status_code
            )
        _read_capped(response, deadline)
    except (requests.RequestException, HTTPError) as e:
        response.close()
        raise _as_fetch_error(e) from e
    except Exception:
        response.close()
        raise


def _read_capped(response, deadline):
    # One recv per loop so the deadline is checked between recvs.
    body = bytearray()
    while chunk := response.raw.read1(CHUNK_SIZE, decode_content=True):
        body += chunk
        if len(body) > MAX_BYTES:
            raise DocsFetchError("Response too large")
        _remaining(deadline)
    response._content = bytes(body)
    response._content_consumed = True


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DocsFetchError("Timed out", transient=True)
    return remaining


def _as_fetch_error(e):
    transient = isinstance(
        e,
        (
            requests.ConnectionError,
            requests.Timeout,
            requests.exceptions.ChunkedEncodingError,
            HTTPError,
        ),
    )
    return DocsFetchError(str(e), transient=transient)
