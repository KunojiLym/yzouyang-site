#!/usr/bin/env python3
"""Smoke-test DIY collector: POST a pageview and expect NDJSON append."""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "diy-events-smoke.ndjson"
PORT = 8799


def main() -> None:
    if OUT.exists():
        OUT.unlink()

    proc = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts" / "diy_collect.py"),
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
            "--out",
            str(OUT),
            "--allow-origin",
            "*",
        ],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(0.4)
        body = json.dumps(
            {
                "t": "pageview",
                "v": 1,
                "ts": "2026-08-04T14:00:00Z",
                "path": "/about/",
                "host": "127.0.0.1",
                "title": "About — smoke",
                "ref": "example.com",
                "lang": "en",
                "tz": "Asia/Singapore",
                "vw": 1280,
                "vh": 720,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/collect",
            data=body,
            headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:8080"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status not in (200, 204):
                raise SystemExit(f"unexpected status {resp.status}")

        lines = OUT.read_text(encoding="utf-8").strip().splitlines()
        if len(lines) != 1:
            raise SystemExit(f"expected 1 ndjson line, got {len(lines)}")
        row = json.loads(lines[0])
        if row.get("path") != "/about/" or row.get("t") != "pageview":
            raise SystemExit(f"bad row: {row}")
        print("diy collect smoke ok")
    except urllib.error.URLError as e:
        err = (proc.stderr.read() if proc.stderr else b"").decode("utf-8", "replace")
        raise SystemExit(f"collect request failed: {e}\n{err}") from e
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
        if OUT.exists():
            OUT.unlink()


if __name__ == "__main__":
    main()
