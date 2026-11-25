"""MiniHMIS -- a deliberately tiny, FAKE health information system.

DEMO ONLY. This app exists to demonstrate a security pre-disclosure
workflow. It contains no real health data and no code from any real HMIS.
It has no dependencies beyond the Python standard library.
"""

import html
import json
import os
import secrets
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

VERSION = (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip()

ADMIN_USER = os.environ.get("MINIHMIS_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("MINIHMIS_ADMIN_PASSWORD", "demo-password")
SITE_NAME = os.environ.get("MINIHMIS_SITE_NAME", "MiniHMIS Demo Instance")

SESSION_COOKIE = "minihmis_session"
SESSIONS = {}  # token -> username (in memory; lost on restart, fine for a demo)

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - MiniHMIS</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;background:#f4f6f8;color:#1c2733}}
.banner{{background:#b45309;color:#fff;text-align:center;padding:6px;font-size:14px}}
header{{background:#14532d;color:#fff;padding:14px 24px;display:flex;justify-content:space-between;align-items:center}}
header span{{opacity:.8;font-size:14px}}
main{{max-width:760px;margin:32px auto;background:#fff;padding:24px 28px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.12)}}
input{{display:block;margin:6px 0 14px;padding:8px;width:260px;font-size:15px}}
button{{padding:8px 18px;font-size:15px;background:#14532d;color:#fff;border:0;border-radius:4px;cursor:pointer}}
table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #dde3e8;padding:8px;text-align:left}}
.error{{color:#b91c1c}}
</style></head><body>
<div class="banner">DEMO SOFTWARE - not a real health system - fictional data only</div>
<header><strong>MiniHMIS</strong><span>{site} &middot; v{version}</span></header>
<main>{body}</main>
</body></html>"""

LOGIN_FORM = """<h1>Sign in</h1>
{error}
<form method="post" action="/login">
<label>Username<input name="username" autofocus></label>
<label>Password<input name="password" type="password"></label>
<button type="submit">Sign in</button>
</form>"""


# Entirely fictional districts and numbers.
REPORTS = [
    {"district": "Northvale", "facilities_reporting": 42, "facilities_total": 45, "anc_first_visits": 1310},
    {"district": "Lakeshore", "facilities_reporting": 28, "facilities_total": 31, "anc_first_visits": 874},
    {"district": "Highridge", "facilities_reporting": 17, "facilities_total": 24, "anc_first_visits": 402},
    {"district": "Eastmoor", "facilities_reporting": 36, "facilities_total": 36, "anc_first_visits": 1128},
]


def dashboard_body(user):
    rows = "".join(
        "<tr><td>%s</td><td>%d / %d</td><td>%d</td></tr>"
        % (html.escape(r["district"]), r["facilities_reporting"], r["facilities_total"], r["anc_first_visits"])
        for r in REPORTS
    )
    return (
        "<h1>Dashboard</h1><p>Signed in as <strong>%s</strong>.</p>"
        "<h2>Monthly reporting (fictional data)</h2>"
        "<table><tr><th>District</th><th>Facilities reporting</th><th>ANC first visits</th></tr>%s</table><br>"
        '<form method="post" action="/logout"><button type="submit">Sign out</button></form>'
    ) % (html.escape(user), rows)


class Handler(BaseHTTPRequestHandler):
    server_version = "MiniHMIS/" + VERSION

    # -- helpers ---------------------------------------------------------
    def current_user(self):
        jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
        morsel = jar.get(SESSION_COOKIE)
        return SESSIONS.get(morsel.value) if morsel else None

    def send(self, status, body, content_type, extra_headers=()):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for name, value in extra_headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def send_page(self, status, title, body, extra_headers=()):
        page = PAGE.format(title=title, site=html.escape(SITE_NAME), version=VERSION, body=body)
        self.send(status, page, "text/html; charset=utf-8", extra_headers)

    def send_json(self, status, payload, extra_headers=()):
        self.send(status, json.dumps(payload) + "\n", "application/json", extra_headers)

    def redirect(self, location, extra_headers=()):
        self.send(303, "", "text/plain", [("Location", location)] + list(extra_headers))

    def start_session(self, user):
        token = secrets.token_urlsafe(32)
        SESSIONS[token] = user
        return ("Set-Cookie", "%s=%s; Path=/; HttpOnly; SameSite=Lax" % (SESSION_COOKIE, token))

    def read_form(self):
        length = int(self.headers.get("Content-Length") or 0)
        fields = parse_qs(self.rfile.read(length).decode("utf-8", "replace"))
        return {k: v[0] for k, v in fields.items()}

    # -- routes ----------------------------------------------------------
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        user = self.current_user()
        if path == "/":
            self.redirect("/dashboard" if user else "/login")
        elif path == "/login":
            self.send_page(200, "Sign in", LOGIN_FORM.format(error=""))
        elif path == "/dashboard":
            if not user:
                self.redirect("/login")
            else:
                self.send_page(200, "Dashboard", dashboard_body(user))
        elif path == "/api/version":
            self.send_json(200, {"name": "MiniHMIS", "version": VERSION, "demo": True})
        elif path == "/api/health":
            self.send_json(200, {"status": "ok"})
        elif path == "/api/reports":
            if not user:
                self.send_json(401, {"error": "sign in required"})
            else:
                self.send_json(200, {"reports": REPORTS})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/login":
            form = self.read_form()
            if secrets.compare_digest(form.get("username", ""), ADMIN_USER) and secrets.compare_digest(
                form.get("password", ""), ADMIN_PASSWORD
            ):
                self.redirect("/dashboard", [self.start_session(ADMIN_USER)])
            else:
                error = '<p class="error">Wrong username or password.</p>'
                self.send_page(401, "Sign in", LOGIN_FORM.format(error=error))
        elif path == "/logout":
            jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
            if SESSION_COOKIE in jar:
                SESSIONS.pop(jar[SESSION_COOKIE].value, None)
            expired = "%s=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0" % SESSION_COOKIE
            self.redirect("/login", [("Set-Cookie", expired)])
        elif path == "/api/demo-bypass-login":
            # DEMO VULNERABILITY (intentional, artificial): signs anyone in as
            # the administrator without a password. This is the dummy bug the
            # pre-disclosure demo reports, fixes and patches.
            self.send_json(
                200,
                {"ok": True, "user": ADMIN_USER, "note": "demo bypass - intentional fake bug"},
                [self.start_session(ADMIN_USER)],
            )
        else:
            self.send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


def make_server(host="0.0.0.0", port=8080):
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print("MiniHMIS %s (DEMO) listening on :%d" % (VERSION, port), flush=True)
    make_server(port=port).serve_forever()
