import time
from unittest.mock import patch

import frappe
import requests
from frappe.tests import IntegrationTestCase

from helpdesk.docs_source.fetch import (
    DOWN_KEY,
    MAX_BYTES,
    MAX_REDIRECTS,
    DocsFetchError,
    fetch,
    fetch_live,
)
from helpdesk.test_utils import make_response

HOST = "docs.example.com"
URL = f"https://{HOST}/x"


@patch("helpdesk.docs_source.fetch.requests.get")
class TestEgress(IntegrationTestCase):
    def test_refuses_internal_address(self, get):
        with self.assertRaises(DocsFetchError):
            fetch("https://127.0.0.1/llms.txt", "127.0.0.1")
        get.assert_not_called()


@patch("helpdesk.docs_source.fetch.validate_egress_url")
@patch("helpdesk.docs_source.fetch.requests.get")
class TestFetch(IntegrationTestCase):
    def setUp(self):
        frappe.cache.delete_value(DOWN_KEY)
        self.addCleanup(frappe.cache.delete_value, DOWN_KEY)

    def test_refuses_other_host(self, get, validate):
        with self.assertRaises(DocsFetchError):
            fetch("https://evil.example/x", HOST)
        get.assert_not_called()

    def test_refuses_backslash_authority_trick(self, get, validate):
        with self.assertRaises(DocsFetchError):
            fetch(f"https://127.0.0.1:53660\\@{HOST}/latest", HOST)
        get.assert_not_called()

    def test_refuses_non_https(self, get, validate):
        with self.assertRaises(DocsFetchError):
            fetch(f"http://{HOST}/x", HOST)
        get.assert_not_called()

    def test_refuses_https_redirect_to_http(self, get, validate):
        get.return_value = make_response(URL, 302, f"http://{HOST}/new")
        with self.assertRaises(DocsFetchError):
            fetch(URL, HOST)
        self.assertEqual(get.call_count, 1)

    def test_malformed_urls_raise_docs_fetch_error(self, get, validate):
        with self.assertRaises(DocsFetchError):
            fetch("https://[bad/", HOST)
        get.return_value = make_response(URL, 302, "https://[bad")
        with self.assertRaises(DocsFetchError):
            fetch(URL, HOST)

    def test_follows_same_host_redirect(self, get, validate):
        get.side_effect = [
            make_response(f"https://{HOST}/old", 302, "/new"),
            make_response(f"https://{HOST}/new"),
        ]
        response = fetch(f"https://{HOST}/old", HOST)
        self.assertEqual(response.url, f"https://{HOST}/new")
        self.assertEqual(validate.call_count, 2)

    def test_refuses_redirect_to_other_host(self, get, validate):
        get.return_value = make_response(URL, 302, "https://evil.example/x")
        with self.assertRaises(DocsFetchError):
            fetch(URL, HOST)
        self.assertEqual(get.call_count, 1)

    def test_redirects_are_capped(self, get, validate):
        get.side_effect = lambda *a, **k: make_response(URL, 302, "/x")
        with self.assertRaises(DocsFetchError):
            fetch(URL, HOST)
        self.assertEqual(get.call_count, MAX_REDIRECTS + 1)

    def test_stops_at_max_bytes_and_closes(self, get, validate):
        chunk = b"x" * (MAX_BYTES // 2 + 1)
        response = make_response(URL, chunks=[chunk, chunk])
        get.return_value = response
        with patch.object(response, "close") as close, self.assertRaises(DocsFetchError):
            fetch(URL, HOST)
        close.assert_called()

    def test_non_success_status_raises(self, get, validate):
        for status, location in [(404, None), (304, None), (302, None)]:
            get.return_value = make_response(URL, status, location)
            with self.assertRaises(DocsFetchError, msg=status) as ctx:
                fetch(URL, HOST)
            self.assertEqual(ctx.exception.status, status)

    def test_timeout_is_a_total_deadline(self, get, validate):
        def slow():
            for _ in range(50):
                time.sleep(0.02)
                yield b"x"

        response = make_response(URL)
        response.iter_content = lambda chunk_size=None: slow()
        get.return_value = response
        with self.assertRaises(DocsFetchError):
            fetch(URL, HOST, timeout=0.1)

    def test_live_failure_skips_next_calls(self, get, validate):
        get.side_effect = requests.ConnectionError("down")
        for _ in range(2):
            with self.assertRaises(DocsFetchError):
                fetch_live(URL, HOST)
        self.assertEqual(get.call_count, 1)

    def test_live_trips_only_on_gateway_statuses(self, get, validate):
        for status in (404, 500):
            get.return_value = make_response(URL, status)
            with self.assertRaises(DocsFetchError):
                fetch_live(URL, HOST)
            self.assertFalse(frappe.cache.get_value(DOWN_KEY), status)
        with self.assertRaises(DocsFetchError):
            fetch_live("https://evil.example/x", HOST)
        self.assertFalse(frappe.cache.get_value(DOWN_KEY))
        get.return_value = make_response(URL, 503)
        with self.assertRaises(DocsFetchError):
            fetch_live(URL, HOST)
        self.assertTrue(frappe.cache.get_value(DOWN_KEY))
