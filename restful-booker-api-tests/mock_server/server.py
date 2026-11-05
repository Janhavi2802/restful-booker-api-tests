"""Offline mock of the Restful-Booker API (standard library only).

Mirrors the real service's behaviour, including its quirks, so the suite runs
without internet and gives repeatable results:
  * POST /auth with bad credentials -> 200 {"reason": "Bad credentials"}
  * PUT/PATCH/DELETE without a valid token -> 403 Forbidden
  * DELETE success -> 201 Created
  * POST /booking with missing fields -> 500 Internal Server Error
  * GET /ping -> 201 Created

Run standalone:  python -m mock_server.server   (listens on 127.0.0.1:5001)
"""
import json
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

USERNAME, PASSWORD = "admin", "password123"
REQUIRED = ("firstname", "lastname", "totalprice", "depositpaid", "bookingdates")


class _Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.bookings: dict[int, dict] = {}
        self.tokens: set[str] = set()
        self.next_id = 1
        self.add({
            "firstname": "Sally", "lastname": "Brown", "totalprice": 111,
            "depositpaid": True,
            "bookingdates": {"checkin": "2026-01-01", "checkout": "2026-01-05"},
            "additionalneeds": "Breakfast",
        })

    def add(self, booking: dict) -> int:
        with self.lock:
            booking_id = self.next_id
            self.bookings[booking_id] = booking
            self.next_id += 1
            return booking_id


STORE = _Store()


def _is_valid(booking) -> bool:
    if not isinstance(booking, dict) or any(k not in booking for k in REQUIRED):
        return False
    dates = booking["bookingdates"]
    return isinstance(dates, dict) and "checkin" in dates and "checkout" in dates


def _clean(booking: dict) -> dict:
    allowed = REQUIRED + ("additionalneeds",)
    out = {k: booking[k] for k in allowed if k in booking}
    if isinstance(out.get("totalprice"), float):
        out["totalprice"] = int(out["totalprice"])
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "MockRestfulBooker/1.0"

    def log_message(self, *args):  # keep test output quiet
        pass

    # ---------- helpers ----------
    def _send(self, status: int, body=None, text: str | None = None):
        if text is not None:
            payload, ctype = text.encode(), "text/plain; charset=utf-8"
        else:
            payload, ctype = json.dumps(body).encode(), "application/json; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json_body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw or b"null")
        except json.JSONDecodeError:
            return None

    def _authorized(self) -> bool:
        cookie = self.headers.get("Cookie", "")
        match = re.search(r"token=([^;]+)", cookie)
        if match and match.group(1) in STORE.tokens:
            return True
        basic = self.headers.get("Authorization", "")
        return basic == "Basic YWRtaW46cGFzc3dvcmQxMjM="  # admin:password123

    def _booking_id(self, path):
        match = re.fullmatch(r"/booking/([^/]+)", path)
        return match.group(1) if match else None

    # ---------- routes ----------
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/ping":
            return self._send(201, text="Created")
        if url.path == "/booking":
            filters = {k: v[0] for k, v in parse_qs(url.query).items()}
            ids = [
                {"bookingid": bid}
                for bid, b in STORE.bookings.items()
                if all(str(b.get(k)) == v for k, v in filters.items()
                       if k in ("firstname", "lastname"))
            ]
            return self._send(200, ids)
        raw_id = self._booking_id(url.path)
        if raw_id is not None:
            if raw_id.isdigit() and int(raw_id) in STORE.bookings:
                return self._send(200, STORE.bookings[int(raw_id)])
            return self._send(404, text="Not Found")
        self._send(404, text="Not Found")

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._json_body()
        if path == "/auth":
            if (isinstance(body, dict) and body.get("username") == USERNAME
                    and body.get("password") == PASSWORD):
                token = secrets.token_hex(8)
                STORE.tokens.add(token)
                return self._send(200, {"token": token})
            return self._send(200, {"reason": "Bad credentials"})
        if path == "/booking":
            if not _is_valid(body):
                return self._send(500, text="Internal Server Error")
            booking = _clean(body)
            return self._send(200, {"bookingid": STORE.add(booking), "booking": booking})
        self._send(404, text="Not Found")

    def do_PUT(self):
        raw_id = self._booking_id(urlparse(self.path).path)
        if not self._authorized():
            return self._send(403, text="Forbidden")
        if raw_id is None or not raw_id.isdigit() or int(raw_id) not in STORE.bookings:
            return self._send(405, text="Method Not Allowed")
        body = self._json_body()
        if not _is_valid(body):
            return self._send(400, text="Bad Request")
        STORE.bookings[int(raw_id)] = _clean(body)
        self._send(200, STORE.bookings[int(raw_id)])

    def do_PATCH(self):
        raw_id = self._booking_id(urlparse(self.path).path)
        if not self._authorized():
            return self._send(403, text="Forbidden")
        if raw_id is None or not raw_id.isdigit() or int(raw_id) not in STORE.bookings:
            return self._send(405, text="Method Not Allowed")
        body = self._json_body() or {}
        booking = STORE.bookings[int(raw_id)]
        booking.update(_clean({**booking, **body}))
        self._send(200, booking)

    def do_DELETE(self):
        raw_id = self._booking_id(urlparse(self.path).path)
        if not self._authorized():
            return self._send(403, text="Forbidden")
        if raw_id is None or not raw_id.isdigit() or int(raw_id) not in STORE.bookings:
            return self._send(405, text="Method Not Allowed")
        del STORE.bookings[int(raw_id)]
        self._send(201, text="Created")


def start_in_background(host="127.0.0.1", port=5001) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == "__main__":
    print("Mock Restful-Booker running on http://127.0.0.1:5001  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", 5001), Handler).serve_forever()
