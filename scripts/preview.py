#!/usr/bin/env python3
"""Offline local UAT preview: lint → build → Pagefind → http.server.

Usage:
  python scripts/preview.py
  python scripts/preview.py --port 8080 --base-path ""
  python scripts/preview.py --base-path /yzouyang-site   # mimic GitHub Pages paths
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def run(cmd: list[str], env: dict | None = None) -> None:
    print("+", " ".join(cmd))
    merged = os.environ.copy()
    if env:
        merged.update(env)
    subprocess.run(cmd, cwd=str(ROOT), check=True, env=merged)


def resolve_npx() -> str | None:
    """Windows CreateProcess cannot run bare 'npx' (needs npx.cmd)."""
    for name in ("npx.cmd", "npx.exe", "npx"):
        found = shutil.which(name)
        if found:
            return found
    return None


def run_pagefind() -> None:
    npx = resolve_npx()
    if not npx:
        print(
            "warning: npx not found on PATH — skipping Pagefind "
            "(search UI will 404 until you install Node or pass --skip-pagefind)",
            file=sys.stderr,
        )
        return
    run([npx, "--yes", "pagefind@1.3.0", "--site", "dist"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--base-path",
        default="",
        help='URL prefix. Empty for true offline root; use /yzouyang-site to mimic Pages.',
    )
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--skip-pagefind", action="store_true")
    args = parser.parse_args()

    run([sys.executable, "scripts/lint.py"])
    # Prefer env override so empty base_path works on Windows shells.
    # build.py can run Pagefind itself, but we always skip it there and run
    # it once here instead — running both would index the same dist/ twice.
    build_cmd = [sys.executable, "scripts/build.py", "--skip-pagefind"]
    run(build_cmd, env={"SITE_BASE_PATH": args.base_path})
    if not args.skip_pagefind:
        run_pagefind()

    base = (args.base_path or "").rstrip("/")
    # Serve repository root so /yzouyang-site/... can map via a tiny handler when needed.
    if base:
        # Build output is in dist/; expose it under base path.
        class Handler(http.server.SimpleHTTPRequestHandler):
            def translate_path(self, path: str) -> str:  # noqa: N802
                from urllib.parse import unquote, urlparse

                parsed = unquote(urlparse(path).path)
                prefix = base + "/"
                if parsed == base or parsed == base + "/":
                    rel = "index.html"
                elif parsed.startswith(prefix):
                    rel = parsed[len(prefix) :]
                else:
                    return str(DIST / "__missing__")
                return str((DIST / rel).resolve())

            def log_message(self, fmt: str, *a) -> None:
                sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % a))

        handler_cls = Handler
        url = f"http://127.0.0.1:{args.port}{base}/"
        serve_dir = None
    else:
        handler_cls = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(DIST)
        )
        url = f"http://127.0.0.1:{args.port}/"
        serve_dir = DIST

    os.chdir(str(serve_dir or ROOT))
    with socketserver.ThreadingTCPServer(("127.0.0.1", args.port), handler_cls) as httpd:
        print(f"preview ready: {url}")
        print("Ctrl+C to stop")
        if not args.no_open:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
