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
    cta_row = re.search(r'<div class="cta-row">(.*?)</div>', home, re.S)
    if not cta_row:
        fail("home missing cta-row")
    cta_html = cta_row.group(1)
    if cta_html.count("btn-primary") != 1:
        fail("home cta-row must have exactly one btn-primary (Contact)")
    if 'class="btn btn-primary"' not in cta_html or ">Contact</a>" not in cta_html:
        fail("home cta-row missing primary Contact CTA")
    if cta_html.count('class="btn"') != 1:
        fail("home cta-row must keep Digital card as the only secondary .btn")
    if 'class="btn" href="' not in cta_html or "Digital card" not in cta_html:
        fail("home cta-row missing secondary Digital card .btn")
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
    if home.count("header-contact") != 1:
        fail("header Contact must appear once (sticky control, not duplicated in Menu)")
    if ".nav-menu" in home and 'class="header-contact' in home.split('class="nav-menu"')[1].split("</details>")[0]:
        fail("nav-menu must not duplicate header Contact")
    if 'class="skip-link"' not in home or 'href="#main"' not in home:
        fail("home missing skip-link to #main")
    if 'id="main"' not in home:
        fail("home missing main#main skip target")
    if 'href="/contact/"' in home and 'nav' in home:
        # primary nav must not point at /contact/ as a page
        if 'aria-label="Primary"' in home and ">Contact</a>" in home.split('aria-label="Primary"')[1].split("</nav>")[0]:
            if 'href="/contact/"' in home.split('aria-label="Primary"')[1].split("</nav>")[0]:
                fail("primary nav still links to /contact/")

    css = (DIST / "styles.css").read_text(encoding="utf-8")
    if "main.page .hero h1" not in css:
        fail("styles.css missing main.page .hero h1 (must beat main.page h1 for Fraunces)")
    if not re.search(
        r"main\.page \.hero h1\s*\{[^}]*font-family:\s*var\(--font-display\)",
        css,
        re.S,
    ):
        fail("hero h1 must set font-family: var(--font-display)")
    if not re.search(
        r"main\.page \.hero h1\s*\{[^}]*font-size:\s*var\(--text-display-hero\)",
        css,
        re.S,
    ):
        fail("hero h1 must set font-size: var(--text-display-hero)")
    if not re.search(
        r"main\.page \.hero h1\s*\{[^}]*font-weight:\s*600",
        css,
        re.S,
    ):
        fail("hero h1 must set font-weight: 600")
    if re.search(
        r"\.header-actions\s*>\s*\.header-contact\s*\{[^}]*display:\s*none",
        css,
        re.S,
    ):
        fail("header Contact must stay visible beside Menu at --bp-md (do not display:none)")
    if "scroll-behavior: auto" not in css:
        fail("styles.css missing scroll-behavior: auto for prefers-reduced-motion")
    if "repeat(3, minmax(0, 1fr))" not in css:
        fail("styles.css missing outcome-strip 3-column grid at --bp-lg")
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
        if 'class="page-search-label"' not in html:
            fail(f"{name} missing visible search label")
        if 'for="pagefind-search-input"' not in html:
            fail(f"{name} search label missing for=pagefind-search-input")
        if 'setAttribute("name", "q")' not in html:
            fail(f"{name} Pagefind input missing name attribute wiring")

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
    if "<h4>" not in credentials:
        fail("credentials issuer groups must list cert titles as h4")
    if re.search(r">https?://[^<]+<", credentials):
        fail("credentials must not print raw verify URLs as link text")

    about = (DIST / "about" / "index.html").read_text(encoding="utf-8")
    if 'class="page-with-toc"' not in about:
        fail("about missing page-with-toc layout")
    if "page-toc-sidebar" not in about:
        fail("about missing sticky sidebar TOC")
    if 'class="section-fold"' not in about:
        fail("about missing collapsible section-fold (must match portfolio/credentials)")
    for name, html in (("about", about), ("portfolio", portfolio), ("credentials", credentials)):
        if re.search(
            r'<summary class="section-fold-summary"[^>]*>\s*<h[1-6]\b',
            html,
        ):
            fail(f"{name} section-fold summary must not wrap a heading")
        if not re.search(r'<summary class="section-fold-summary" id="[^"]+">', html):
            fail(f"{name} section-fold summary missing id for TOC anchors")
        if 'class="visually-hidden"' not in html:
            fail(f"{name} section-fold missing visually-hidden heading for outline")
    if 'class="embed-fallback"' not in about and 'class="figma-open"' not in about:
        fail("about missing Figma open/fallback link")
    if "cj-link-card" in about:
        fail("about Career Journey must use editorial item-list rows, not cj-link-card")
    if 'id="selected-writing"' not in about:
        fail("about missing Selected writing section")
    if "medium.com/@kunojilym" not in about:
        fail("about missing Medium writing highlight links")

    if portfolio.count("github.com/") < 5:
        fail("portfolio missing expected public GitHub project links")
    if "<iframe" in portfolio:
        fail("portfolio must not load a live Figma iframe (white canvas on dark page)")
    if "embed-wrap" in portfolio and "embed-frame-static" not in portfolio:
        fail("portfolio Figma surface missing embed-frame-static dark preview")
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

    cj_data_path = DATA / "career-journey.yaml"
    cj_page_path = DIST / "career-journey" / "index.html"
    if cj_data_path.is_file():
        if not cj_page_path.is_file():
            fail("career-journey.yaml present but dist/career-journey/index.html missing")
        cj_html = cj_page_path.read_text(encoding="utf-8")
        if 'class="cj-page"' not in cj_html:
            fail("career-journey page missing cj-page wrapper")
        slide_count = cj_html.count('class="cj-slide ')
        if slide_count < 1:
            fail("career-journey page has no rendered slides")
        # Every <img> on this page must have a non-empty alt — the concrete,
        # enforced version of the accessibility argument for going native
        # instead of embedding the Figma deck (an iframe's internal alt
        # text isn't something this repo can inspect or fix).
        for match in re.finditer(r"<img\b[^>]*>", cj_html):
            tag = match.group(0)
            alt_match = re.search(r'alt="([^"]*)"', tag)
            if not alt_match or not alt_match.group(1).strip():
                fail(f"career-journey page has an <img> with missing/empty alt: {tag}")
        if 'src="/career-journey.js"' not in cj_html and 'src="./career-journey.js"' not in cj_html and "career-journey.js" not in cj_html:
            fail("career-journey page missing scroll-reveal script tag")

    print("test_site_build ok")


if __name__ == "__main__":
    main()
