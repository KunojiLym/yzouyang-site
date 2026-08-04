#!/usr/bin/env python3
"""Contract checks against built dist/ (run after scripts/build.py)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data"

FORBIDDEN = ("prudential.com", "u.nus.edu", "gatech.edu")
ROUTES = (
    ("index.html", "Home"),
    ("about/index.html", "About"),
    ("portfolio/index.html", "Portfolio"),
    ("credentials/index.html", "Credentials"),
    ("contact/index.html", "Contact"),
)


def fail(msg: str) -> None:
    print(f"test_site_build error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not DIST.is_dir():
        fail("dist/ missing — run python scripts/build.py first")

    site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
    bitly = str((site.get("external") or {}).get("bitly_hub") or "")
    if not bitly:
        fail("site.external.bitly_hub required for Digital card CTA")

    for rel, label in ROUTES:
        path = DIST / rel
        if not path.is_file():
            fail(f"missing route {label}: {rel}")

    home = (DIST / "index.html").read_text(encoding="utf-8")
    if 'class="proof-strip"' not in home:
        fail("home missing proof-strip")
    if "Digital card" not in home or bitly not in home:
        fail("home missing Digital card CTA / bitly_hub")
    if 'class="portrait-chip"' not in home:
        fail("home missing portrait-chip")
    if "Static migration" in home or "Phase 1 pages" in home:
        fail("home footer still has migration chrome")
    if "&copy;" not in home and "©" not in home:
        fail("home footer missing copyright")
    if f'mailto:{(site.get("contact") or {}).get("email")}' not in home:
        fail("home footer missing mailto")
    if 'class="nav-menu"' not in home:
        fail("home missing mobile nav-menu")

    css = (DIST / "styles.css").read_text(encoding="utf-8")
    if "background-color: var(--bg-deep)" not in css:
        fail("styles.css missing solid background-color: var(--bg-deep)")

    portfolio = (DIST / "portfolio" / "index.html").read_text(encoding="utf-8")
    credentials = (DIST / "credentials" / "index.html").read_text(encoding="utf-8")
    for name, html in (("portfolio", portfolio), ("credentials", credentials)):
        if 'id="search"' not in html:
            fail(f"{name} missing #search")
        if 'class="page-toc"' not in html:
            fail(f"{name} missing page-toc")

    if 'class="issuer-group"' not in credentials:
        fail("credentials missing issuer-group headings")

    about = (DIST / "about" / "index.html").read_text(encoding="utf-8")
    if 'class="embed-fallback"' not in about and 'class="figma-open"' not in about:
        fail("about missing Figma open/fallback link")

    pf = DIST / "pagefind" / "pagefind-ui.js"
    if not pf.is_file():
        fail("dist/pagefind/pagefind-ui.js missing")

    photo = site.get("person", {}).get("photo") or ""
    if photo:
        asset = DIST / photo.lstrip("/").replace("/", "\\") if sys.platform == "win32" else DIST / photo.lstrip("/")
        # normalize: photo is /assets/profile.jpg
        asset = DIST.joinpath(*photo.strip("/").split("/"))
        if not asset.is_file():
            fail(f"profile asset missing in dist: {photo}")
        if photo not in home and with_base_check(home, photo):
            pass  # may be base-path prefixed; just ensure asset exists

    blob = "\n".join(
        (DIST / rel).read_text(encoding="utf-8") for rel, _ in ROUTES
    ).lower()
    for needle in FORBIDDEN:
        if needle in blob:
            fail(f"built HTML contains forbidden domain: {needle}")

    print("test_site_build ok")


def with_base_check(home: str, photo: str) -> bool:
    return photo.rsplit("/", 1)[-1] in home


if __name__ == "__main__":
    main()
