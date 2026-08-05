#!/usr/bin/env python3
"""Contract checks against built dist/ (run after scripts/build.py)."""

from __future__ import annotations

import json
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
    if 'class="outcome-strip"' not in home:
        fail("home missing outcome-strip")
    if "professional credentials" in home:
        fail("home still shows cert-count vanity chip")
    if 'class="proof-strip"' not in home:
        fail("home missing proof-strip")
    if "Digital card" not in home or bitly not in home:
        fail("home missing Digital card CTA / bitly_hub")
    if 'class="portrait-chip"' not in home:
        fail("home missing portrait-chip")
    if 'id="contact"' not in home:
        fail("home missing #contact section")
    if "Static migration" in home or "Phase 1 pages" in home:
        fail("home footer still has migration chrome")
    if "&copy;" not in home and "©" not in home:
        fail("home footer missing copyright")
    email = (site.get("contact") or {}).get("email") or ""
    if f"mailto:{email}" not in home:
        fail("home missing mailto")
    if 'class="nav-menu"' not in home:
        fail("home missing mobile nav-menu")
    if 'class="site-header-wrap"' not in home:
        fail("home missing sticky site-header-wrap")
    if 'class="header-contact' not in home:
        fail("home missing header Contact control")
    if 'href="/contact/"' in home and 'nav' in home:
        # primary nav must not point at /contact/ as a page
        if 'aria-label="Primary"' in home and ">Contact</a>" in home.split('aria-label="Primary"')[1].split("</nav>")[0]:
            if 'href="/contact/"' in home.split('aria-label="Primary"')[1].split("</nav>")[0]:
                fail("primary nav still links to /contact/")

    css = (DIST / "styles.css").read_text(encoding="utf-8")
    if "background-color: var(--bg-deep)" not in css:
        fail("styles.css missing solid background-color: var(--bg-deep)")
    if "position: sticky" not in css:
        fail("styles.css missing sticky header")
    if "--bg-elevated" not in css or "--focus-ring" not in css:
        fail("styles.css missing semantic tokens (--bg-elevated / --focus-ring)")
    if "--text-default" not in css:
        fail("styles.css missing --text-default")

    portfolio = (DIST / "portfolio" / "index.html").read_text(encoding="utf-8")
    credentials = (DIST / "credentials" / "index.html").read_text(encoding="utf-8")
    if 'class="case-outcome"' not in portfolio:
        fail("portfolio missing case-outcome class on project rows")
    if 'class="case-tools' not in portfolio:
        fail("portfolio missing case-tools class")
    for name, html in (("portfolio", portfolio), ("credentials", credentials)):
        if 'id="search"' not in html:
            fail(f"{name} missing #search")
        if 'class="page-toc' not in html:
            fail(f"{name} missing page-toc")
        if 'class="page-with-toc"' not in html:
            fail(f"{name} missing page-with-toc layout")
        if "page-toc-sidebar" not in html:
            fail(f"{name} missing sticky sidebar TOC class")

    styles_dir = ROOT / "src" / "styles"
    for part in (
        "tokens.css",
        "base.css",
        "chrome.css",
        "home.css",
        "components.css",
        "longform.css",
        "search.css",
        "motion.css",
    ):
        if not (styles_dir / part).is_file():
            fail(f"missing style module src/styles/{part}")
    if "--- longform.css ---" not in css:
        fail("dist/styles.css was not assembled from src/styles modules")

    if 'class="issuer-group"' not in credentials:
        fail("credentials missing issuer-group headings")

    about = (DIST / "about" / "index.html").read_text(encoding="utf-8")
    if 'class="page-with-toc"' not in about:
        fail("about missing page-with-toc layout")
    if "page-toc-sidebar" not in about:
        fail("about missing sticky sidebar TOC")
    if 'class="section-fold"' not in about:
        fail("about missing collapsible section-fold (must match portfolio/credentials)")
    if 'class="embed-fallback"' not in about and 'class="figma-open"' not in about:
        fail("about missing Figma open/fallback link")
    if 'id="selected-writing"' not in about:
        fail("about missing Selected writing section")
    if "medium.com/@kunojilym" not in about:
        fail("about missing Medium writing highlight links")

    if portfolio.count("github.com/") < 5:
        fail("portfolio missing expected public GitHub project links")
    if 'class="page-toc-sub"' not in portfolio:
        fail("portfolio TOC missing nested subcategory list")
    if 'class="section-fold"' not in portfolio or 'class="section-fold"' not in credentials:
        fail("portfolio/credentials missing collapsible section-fold")
    if 'class="page-toc-sub"' not in credentials:
        fail("credentials TOC missing issuer subcategory list")

    contact_page = DIST / "contact" / "index.html"
    if not contact_page.is_file():
        fail("contact/index.html redirect missing")
    contact_html = contact_page.read_text(encoding="utf-8")
    if "#contact" not in contact_html:
        fail("contact redirect must target #contact")
    if "http-equiv" not in contact_html.lower() and "refresh" not in contact_html.lower():
        fail("contact redirect missing meta refresh")

    pf = DIST / "pagefind" / "pagefind-ui.js"
    if not pf.is_file():
        fail("dist/pagefind/pagefind-ui.js missing")

    photo = site.get("person", {}).get("photo") or ""
    if photo:
        asset = DIST.joinpath(*photo.strip("/").split("/"))
        if not asset.is_file():
            fail(f"profile asset missing in dist: {photo}")
        if "profile.jpg" not in home and "profile" not in home:
            fail("home does not reference profile photo")

    blob = "\n".join((DIST / rel).read_text(encoding="utf-8") for rel, _ in ROUTES).lower()
    for needle in FORBIDDEN:
        if needle in blob:
            fail(f"built HTML contains forbidden domain: {needle}")

    print("test_site_build ok")


if __name__ == "__main__":
    main()
