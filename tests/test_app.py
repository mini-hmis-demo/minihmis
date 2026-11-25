"""Run with: python3 -m unittest discover -s tests"""

import json
import sys
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import minihmis  # noqa: E402


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = minihmis.make_server("127.0.0.1", 0)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, path, data=None, cookie=None):
        """Return (status, headers, body) without following redirects."""
        req = urllib.request.Request(self.base + path, method="POST" if data is not None else "GET")
        if data is not None:
            req.data = urllib.parse.urlencode(data).encode()
        if cookie:
            req.add_header("Cookie", cookie)
        try:
            resp = urllib.request.build_opener(NoRedirect).open(req)
        except urllib.error.HTTPError as err:
            resp = err
        return resp.status, resp.headers, resp.read().decode()

    def login(self):
        creds = {"username": minihmis.ADMIN_USER, "password": minihmis.ADMIN_PASSWORD}
        status, headers, _ = self.request("/login", creds)
        self.assertEqual(status, 303)
        return headers["Set-Cookie"].split(";")[0]

    def test_version_endpoint(self):
        status, _, body = self.request("/api/version")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["version"], minihmis.VERSION)

    def test_dashboard_requires_login(self):
        status, headers, _ = self.request("/dashboard")
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/login")

    def test_wrong_password_rejected(self):
        status, headers, _ = self.request("/login", {"username": "admin", "password": "nope"})
        self.assertEqual(status, 401)
        self.assertIsNone(headers["Set-Cookie"])

    def test_login_then_dashboard(self):
        status, _, body = self.request("/dashboard", cookie=self.login())
        self.assertEqual(status, 200)
        self.assertIn("Dashboard", body)


if __name__ == "__main__":
    unittest.main()
