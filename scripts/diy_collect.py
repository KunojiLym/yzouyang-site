#!/usr/bin/env python3
"""Local DIY pageview collector — appends NDJSON for Grafana/DuckDB later.

Usage:
  python scripts/diy_collect.py --port 8787 --out data/diy-events.ndjson

Point site.json analytics.diy.collect_url at http://127.0.0.1:8787/collect
(or a tunneled HTTPS URL for preview hosts).
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def cors_headers(origin: str | None, allowed: set[str]) -> dict[str, str]:
    headers = {
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Max-Age": "86400",
        "Cache-Control": "no-store",
    }
    if origin and (origin in allowed or "*" in allowed):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"
    return headers


def _to_int(value, default: int) -> int:
    """Coerce *value* to int, returning *default* for non-numeric input."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def make_handler(out_path: Path, allowed_origins: set[str], max_bytes: int):
    # ThreadingHTTPServer dispatches each request on its own thread; without
    # this lock, concurrent POSTs can interleave writes to the same NDJSON
    # file and corrupt lines.
    write_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:  # quieter default
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def _cors(self) -> dict[str, str]:
            return cors_headers(self.headers.get("Origin"), allowed_origins)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(204)
            for k, v in self._cors().items():
                self.send_header(k, v)
            self.end_headers()

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path.rstrip("/") != "/collect":
                self.send_response(404)
                for k, v in self._cors().items():
                    self.send_header(k, v)
                self.end_headers()
                return

            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > max_bytes:
                self.send_response(413 if length > max_bytes else 400)
                for k, v in self._cors().items():
                    self.send_header(k, v)
                self.end_headers()
                return

            raw = self.rfile.read(length)
            try:
                event = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self.send_response(400)
                for k, v in self._cors().items():
                    self.send_header(k, v)
                self.end_headers()
                return

            if not isinstance(event, dict) or event.get("t") != "pageview":
                self.send_response(400)
                for k, v in self._cors().items():
                    self.send_header(k, v)
                self.end_headers()
                return

            # Strip unexpected large fields; keep first-party schema only.
            clean = {
                "t": "pageview",
                "v": _to_int(event.get("v"), 1),
                "ts": str(event.get("ts") or datetime.now(timezone.utc).isoformat()),
                "path": str(event.get("path") or "")[:512],
                "host": str(event.get("host") or "")[:253],
                "title": str(event.get("title") or "")[:256],
                "ref": str(event.get("ref") or "")[:253],
                "lang": str(event.get("lang") or "")[:16],
                "tz": str(event.get("tz") or "")[:64],
                "vw": _to_int(event.get("vw"), 0),
                "vh": _to_int(event.get("vh"), 0),
                "recv_at": datetime.now(timezone.utc).isoformat(),
                "recv_ip": self.client_address[0],
            }

            out_path.parent.mkdir(parents=True, exist_ok=True)
            with write_lock, out_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(clean, separators=(",", ":")) + "\n")

            self.send_response(204)
            for k, v in self._cors().items():
                self.send_header(k, v)
            self.end_headers()

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "diy-events.ndjson",
    )
    parser.add_argument(
        "--allow-origin",
        action="append",
        default=[],
        help="Repeatable. Default: localhost origins + * for local smoke.",
    )
    parser.add_argument("--max-bytes", type=int, default=4096)
    args = parser.parse_args()

    allowed = set(args.allow_origin) or {
        "*",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    }
    handler = make_handler(args.out.resolve(), allowed, args.max_bytes)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"diy collect on http://{args.host}:{args.port}/collect -> {args.out}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
