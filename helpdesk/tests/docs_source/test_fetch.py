import gzip
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

import requests
from frappe.tests import IntegrationTestCase

from helpdesk.docs_source.fetch import (
    MAX_BYTES,
    MAX_REDIRECTS,
    DocsFetchError,
    _read_capped,
    fetch,
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
        with (
            patch.object(response, "close") as close,
            self.assertRaises(DocsFetchError),
        ):
            fetch(URL, HOST)
        close.assert_called()

    def test_non_success_status_raises(self, get, validate):
        for status, location in [(404, None), (304, None), (302, None)]:
            get.return_value = make_response(URL, status, location)
            with self.assertRaises(DocsFetchError, msg=status) as ctx:
                fetch(URL, HOST)
            self.assertEqual(ctx.exception.status, status)


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/gzip":
            body = gzip.compress(b"hello docs" * 100)
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(200)
        self.send_header("Content-Length", "100")
        self.end_headers()
        try:
            for _ in range(100):
                self.wfile.write(b"x")
                self.wfile.flush()
                time.sleep(0.05)
        except OSError:
            pass


class TestReadCapped(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.server = HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.addClassCleanup(cls.server.server_close)
        cls.addClassCleanup(cls.server.shutdown)

    def get(self, path):
        url = f"http://127.0.0.1:{self.server.server_port}{path}"
        return requests.get(url, stream=True, timeout=2)

    def test_slow_body_stops_at_deadline(self):
        started = time.monotonic()
        with self.assertRaises(DocsFetchError):
            _read_capped(self.get("/drip"), time.monotonic() + 0.3)
        self.assertLess(time.monotonic() - started, 0.8)

    def test_gzip_body_is_decoded(self):
        response = self.get("/gzip")
        _read_capped(response, time.monotonic() + 1)
        self.assertEqual(response.content, b"hello docs" * 100)
