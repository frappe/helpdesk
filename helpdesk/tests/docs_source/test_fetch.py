from unittest.mock import patch

import frappe
import requests
from frappe.tests import IntegrationTestCase

from helpdesk.docs_source.fetch import (
    DOWN_KEY,
    MAX_BYTES,
    DocsFetchError,
    fetch,
    fetch_live,
)

HOST = "docs.example.com"


def make_response(url, status=200, location=None, chunks=(b"ok",)):
    response = requests.Response()
    response.status_code = status
    response.url = url
    if location:
        response.headers["Location"] = location
    response.iter_content = lambda chunk_size=None: iter(chunks)
    return response


class TestEgress(IntegrationTestCase):
    def test_refuses_internal_address(self):
        with self.assertRaises(DocsFetchError):
            fetch("https://127.0.0.1/llms.txt", "127.0.0.1")


@patch("helpdesk.docs_source.fetch.validate_egress_url")
@patch("helpdesk.docs_source.fetch.requests.get")
class TestFetch(IntegrationTestCase):
    def setUp(self):
        frappe.cache.delete_value(DOWN_KEY)

    def test_refuses_other_host(self, get, validate):
        with self.assertRaises(DocsFetchError):
            fetch("https://evil.example/x", HOST)
        get.assert_not_called()

    def test_follows_same_host_redirect(self, get, validate):
        get.side_effect = [
            make_response(f"https://{HOST}/old", 302, "/new"),
            make_response(f"https://{HOST}/new"),
        ]
        response = fetch(f"https://{HOST}/old", HOST)
        self.assertEqual(response.url, f"https://{HOST}/new")
        self.assertEqual(validate.call_count, 2)

    def test_refuses_redirect_to_other_host(self, get, validate):
        get.return_value = make_response(f"https://{HOST}/old", 302, "https://evil.example/x")
        with self.assertRaises(DocsFetchError):
            fetch(f"https://{HOST}/old", HOST)
        self.assertEqual(get.call_count, 1)

    def test_stops_at_max_bytes(self, get, validate):
        chunk = b"x" * (MAX_BYTES // 2 + 1)
        get.return_value = make_response(f"https://{HOST}/big", chunks=[chunk, chunk])
        with self.assertRaises(DocsFetchError):
            fetch(f"https://{HOST}/big", HOST)

    def test_bad_status_raises(self, get, validate):
        get.return_value = make_response(f"https://{HOST}/x", 404)
        with self.assertRaises(DocsFetchError):
            fetch(f"https://{HOST}/x", HOST)

    def test_live_failure_skips_next_calls(self, get, validate):
        get.side_effect = requests.ConnectionError("down")
        for _ in range(2):
            with self.assertRaises(DocsFetchError):
                fetch_live(f"https://{HOST}/x", HOST)
        self.assertEqual(get.call_count, 1)
