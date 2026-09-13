#!/usr/bin/env python3
"""Contract checks against built dist/ (run after scripts/build.py)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from build import _beat_value_html, figma_embed_html, resolve_enterprise_overlay, with_base

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data"

FORBIDDEN = ("prudential.com", "u.nus.edu", "gatech.edu")
ROUTES = (
    ("index.html", "Home"),
    ("about/index.html", "About redirect"),
    ("systems/index.html", "Systems"),
    ("systems/catalogue/index.html", "Systems catalogue"),
    ("notes/index.html", "Notes"),
    ("credentials/index.html", "Credentials"),
    ("contact/index.html", "Contact redirect"),
    ("portfolio/index.html", "Portfolio redirect"),
    ("perspectives/index.html", "Perspectives redirect"),
)


def fail(msg: str) -> None:
    print(f"test_site_build error: {msg}", file=sys.stderr)
    raise SystemExit(1)


CLASS_IN_ATTR = re.compile(r'class="([^"]*)"')


def has_html_class(html: str, name: str) -> bool:
    for match in CLASS_IN_ATTR.finditer(html):
        if name in match.group(1).split():
            return True
    return False


def _rel_lum(hex_color: str) -> float:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def chan(c: int) -> float:
        x = c / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def _contrast(fg: str, bg: str) -> float:
    l1, l2 = _rel_lum(fg), _rel_lum(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _token_hex(css: str, name: str) -> str:
    match = re.search(rf"{re.escape(name)}:\s*(#[0-9a-fA-F]{{3,8}})", css)
    if not match:
        fail(f"styles.css missing hex token {name}")
    return match.group(1)


def _light_block(css: str) -> str:
    match = re.search(r'\[data-theme="light"\]\s*\{([^}]+)\}', css, re.S)
    if not match:
        fail('styles.css missing [data-theme="light"] token block')
    return match.group(1)


def assert_evidence_href_https_only() -> None:
    js = _beat_value_html(
        {"evidence": "Role write-up", "evidence_href": "javascript:alert(1)"},
        "evidence",
    )
    if "<a" in js.lower() or "javascript:" in js:
        fail("evidence_href javascript: must not render an anchor")
    http = _beat_value_html(
        {"evidence": "Role write-up", "evidence_href": "http://example.com"},
        "evidence",
    )
    if "<a" in http.lower():
        fail("evidence_href http:// must not render an anchor")
    https = _beat_value_html(
        {
            "evidence": "Role write-up",
            "evidence_href": "https://www.linkedin.com/in/yzouyang",
            "evidence_label": "LinkedIn",
        },
        "evidence",
    )
    if 'href="https://www.linkedin.com/in/yzouyang"' not in https:
        fail("https evidence_href must render an escaped HTTPS anchor")


def assert_no_empty_static_frames(html: str, label: str) -> None:
    for match in re.finditer(
        r"<a\b[^>]*embed-frame-static[^>]*>(.*?)</a>",
        html,
        re.S | re.I,
    ):
        if "<img" not in match.group(1).lower():
            fail(
                f"{label}: empty embed-frame-static is forbidden "
                "(needs a real poster <img>, not a fill-only box)"
            )


def main() -> None:
    if not DIST.is_dir():
        fail("dist/ missing — run python scripts/build.py first")
    assert_evidence_href_https_only()

    site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
    bitly = str((site.get("external") or {}).get("bitly_hub") or "")
    if not bitly:
        fail("site.external.bitly_hub required for Digital card CTA")

    ent_copy = site.get("enterprise_copy") or {}
    if not isinstance(ent_copy, dict):
        fail("site.enterprise_copy must be an object")
    for key in ent_copy:
        if " " in key or "—" in key:
            fail(f"enterprise_copy must be keyed by heading_id, not export title: {key!r}")
    pru_id = "prudential-singapore-senior-data-engineer-solutioning-architecture"
    if pru_id not in ent_copy:
        fail("enterprise_copy missing Prudential heading_id key")
    export_title = (
        "Prudential (Singapore) — Senior Data Engineer, Solutioning & Architecture"
    )
    oid, overlay = resolve_enterprise_overlay({"title": export_title}, ent_copy)
    if oid != pru_id or not overlay:
        fail("enterprise overlay must resolve from current export title via heading_id")
    display = str((ent_copy[pru_id] or {}).get("title") or "")
    oid2, overlay2 = resolve_enterprise_overlay({"title": display}, ent_copy)
    if oid2 != pru_id or not overlay2:
        fail("enterprise overlay must still resolve after export title matches display title")

    for row in site.get("home_selected") or []:
        if not str(row.get("id") or "").strip():
            fail("home_selected rows must reference a case id")
        for beat in ("problem", "role", "decision", "outcome"):
            if str(row.get(beat) or "").strip():
                fail(f"home_selected must not duplicate {beat}; compose from copy maps")

    chrome_src = (ROOT / "src" / "chrome.js").read_text(encoding="utf-8")
    if "offset = 96" in chrome_src:
        fail("TOC spy must not hardcode 96px; use --header-offset")
    if "--header-offset" not in chrome_src:
        fail("TOC spy missing --header-offset")

    for rel, label in ROUTES:
        path = DIST / rel
        if not path.is_file():
            fail(f"missing route {label}: {rel}")

    home = (DIST / "index.html").read_text(encoding="utf-8")
    if not has_html_class(home, "entrance") or not has_html_class(home, "hero"):
        fail("home missing entrance hero")
    if "entrance-atmosphere--tokens" not in home:
        fail("home missing token-based entrance atmosphere (no reference photography)")
    if 'class="current-index"' not in home:
        fail("home missing current-index")
    if 'class="index-status"' in home or ">studying<" in home:
        fail("home current-index must use topic labels, not -ing status verbs")
    if 'class="index-topic"' not in home:
        fail("home current-index missing index-topic labels")
    if "/systems/#SYS-" not in home or "/notes/#NOTE-" not in home:
        fail("home current-index must deep-link to catalogue records, not section indexes")
    if 'data-library-deck' in home or has_html_class(home, "library-slide"):
        fail("home must not ship the library slide deck")
    if not has_html_class(home, "header-search"):
        fail("home search must live in the header for instant access")
    if 'id="catalogue-search"' in home:
        fail("home must not bury catalogue search at page bottom")
    if not has_html_class(home, "home-entry-grid"):
        fail("home missing library entry grid")
    if has_html_class(home, "home-featured-systems"):
        fail("home must not ship scroll plates (use entry grid + tab shells)")
    if has_html_class(home, "home-featured-notes"):
        fail("home must not ship featured notes plate")
    if has_html_class(home, "home-contact-plate"):
        fail("home must not ship contact plate (contact lives in footer)")
    if has_html_class(home, "home-credentials-teaser"):
        fail("home must not ship credentials teaser plate")
    if not has_html_class(home, "home-route"):
        fail("home must use viewport-locked home-route shell")
    if not has_html_class(home, "home-shell"):
        fail("home must wrap hero and footer in home-shell for aligned measure")
    if 'class="system-map-stage"' in home:
        fail("home must not embed the full system map (lives on /systems/)")
    if 'id="workshop"' in home or has_html_class(home, "workshop"):
        fail("home must not ship a separate workshop/experiments slide")
    if "Homelab" in home:
        fail("home must not reference homelab until a public repo or essay exists")
    if 'class="outcome-strip"' in home:
        fail("home must not show outcome-strip in hero (outcomes live on SYS records)")
    if "professional credentials" in home:
        fail("home still shows cert-count vanity chip")
    if 'class="proof-strip"' not in home:
        fail("home missing proof-strip")
    if 'class="cta-row"' in home:
        fail("home must not ship cta-row (Systems is in the entry grid; contact is in footer)")
    hero_before_grid = home.split("home-entry-grid", 1)[0]
    if "View systems" in hero_before_grid:
        fail("home hero must not duplicate Systems button before the entry grid")
    if 'href="/contact/"' in hero_before_grid:
        fail("home hero must not ship Connect button (contact is in footer)")
    if "Specialist" in hero_before_grid:
        fail("entrance must not use vague Specialist positioning")
    if "CTO" in hero_before_grid or "CDAO" in hero_before_grid:
        fail("entrance must not claim CTO/CDAO")
    if "Building intelligible systems" not in home:
        fail("home entrance must use thesis headline")
    if 'class="portrait-chip"' in home:
        fail("home must not use hero portrait-chip")
    if 'href="/career-journey/"' in home:
        fail("home must not link to removed Career Journey route")
    if 'href="/credentials/"' not in home:
        fail("home entry grid must link to credentials")
    if 'href="/about/"' in home.split("home-entry-grid", 1)[-1]:
        fail("home entry grid must not link to removed Profile route")
    if 'class="home-philosophy"' not in home and 'class="philosophy home-philosophy"' not in home:
        fail("home must surface philosophy blockquote")
    if 'class="home-competencies"' not in home:
        fail("home must surface core competencies section")
    if 'class="home-competency-list"' not in home:
        fail("home competencies must use editorial list markup")
    if "Data Engineering Leadership" not in home:
        fail("home competencies must include export competency titles")
    if 'href="/notes/"' not in home:
        fail("home entry grid must link to notes")
    if "folio-toolbar" in home:
        fail("home must not ship an inert folio-toolbar")
    if 'class="operating-themes"' in home:
        fail("home must not ship operating-themes block")
    if "tel:" in home or "+65" in home:
        fail("home must not expose a visitor-facing phone number")
    if "PUBLIC contacts only" in home:
        fail("home must not show the visitor-facing contacts governance note")
    if 'class="nav-elsewhere"' in home:
        fail("header must not ship Elsewhere disclosure (external links live in footer)")
    header_actions = home.split('class="header-actions"', 1)[1].split("</header>", 1)[0]
    if ">Blog</a>" in header_actions:
        fail("Blog must not appear in header (footer only)")
    desktop_nav = home.split('class="site-nav site-nav-desktop"', 1)[1].split("</nav>", 1)[0]
    if "nav-elsewhere" in desktop_nav:
        fail("Elsewhere control must not sit inside primary nav")
    if ">Systems</a>" not in desktop_nav:
        fail("desktop nav missing Systems")
    if ">Notes</a>" not in desktop_nav:
        fail("desktop nav missing Notes")
    if ">Experiments</a>" in desktop_nav:
        fail("desktop nav must not link to removed workshop slide")
    if ">Connect</a>" in desktop_nav:
        fail("desktop nav must not duplicate connect")
    if ">Profile</a>" in desktop_nav:
        fail("desktop nav must not ship Profile (content absorbed into home and credentials)")
    if ">Credentials</a>" not in desktop_nav:
        fail("desktop nav missing Credentials")
    if ">Work</a>" in desktop_nav:
        fail("desktop nav must not label Systems as Work")
    if 'href="/systems/"' not in desktop_nav:
        fail("desktop nav Systems must link to /systems/")
    if 'href="/notes/"' not in desktop_nav:
        fail("desktop nav Notes must link to /notes/")
    if 'library-card' not in home:
        fail("home footer must use library-card pattern")
    if "Static migration" in home or "Phase 1 pages" in home:
        fail("home footer still has migration chrome")
    if "&copy;" not in home and "©" not in home:
        fail("home footer missing copyright")
    email = (site.get("contact") or {}).get("email") or ""
    if f"mailto:{email}" not in home:
        fail("home missing mailto")
    footer_chunk = home.split('class="library-page-footer', 1)[-1].split("</footer>", 1)[0]
    for label in ("Digital card", "Blog", "Medium", "LinkedIn", "GitHub"):
        if f">{label}</a>" not in footer_chunk:
            fail(f"home footer missing {label} link")
    if 'class="nav-menu"' not in home:
        fail("home missing mobile nav-menu")
    if 'class="site-header-wrap"' not in home:
        fail("home missing sticky site-header-wrap")
    if 'class="theme-toggle"' not in home:
        fail("home missing theme toggle")
    if home.count("data-theme-toggle") < 1:
        fail("theme toggle missing data-theme-toggle hook")
    if 'data-theme="dark"' not in home:
        fail("html must default data-theme=dark")
    boot_idx = home.find('var KEY = "yz-theme"')
    css_idx = home.find('rel="stylesheet"')
    if boot_idx == -1 or css_idx == -1 or boot_idx > css_idx:
        fail("FOUC-safe theme boot script must appear before stylesheet")
    if "application/ld+json" not in home or '"@type":"Person"' not in home:
        fail("home missing Person JSON-LD")
    if '"@type":"WebSite"' not in home:
        fail("home missing WebSite JSON-LD")
    if 'rel="canonical"' not in home:
        fail("home missing canonical URL")
    if "og:description" not in home:
        fail("home missing Open Graph description")
    headline = (site.get("person") or {}).get("headline") or ""
    home_desc = re.search(r'<meta name="description" content="([^"]+)"', home)
    if not home_desc:
        fail("home missing meta description")
    if home_desc.group(1) == headline:
        fail("home meta description must not be the raw role headline")
    if 'class="header-contact' in home:
        fail("header Contact control must not duplicate Contact")
    if 'class="skip-link"' not in home or 'href="#main"' not in home:
        fail("home missing skip-link to #main")
    if 'id="main"' not in home:
        fail("home missing main#main skip target")
    nav_chunk = home.split('aria-label="Primary"', 1)
    if len(nav_chunk) < 2:
        fail("home missing primary nav")
    primary_nav = nav_chunk[1].split("</nav>", 1)[0]
    if 'href="/about/"' in primary_nav:
        fail("primary nav must not link to removed Profile route")
    if 'href="/systems/"' not in primary_nav:
        fail("primary nav must link Systems to /systems/")

    portfolio_redirect = (DIST / "portfolio" / "index.html").read_text(encoding="utf-8")
    if "/systems/" not in portfolio_redirect:
        fail("/portfolio/ redirect must point to /systems/")
    catalogue_redirect = (DIST / "systems" / "catalogue" / "index.html").read_text(encoding="utf-8")
    if "/systems/" not in catalogue_redirect:
        fail("/systems/catalogue/ redirect must point to /systems/")
    perspectives_redirect = (DIST / "perspectives" / "index.html").read_text(encoding="utf-8")
    if "/notes/" not in perspectives_redirect:
        fail("/perspectives/ redirect must point to /notes/")

    systems = (DIST / "systems" / "index.html").read_text(encoding="utf-8")
    if not has_html_class(systems, "library-shell"):
        fail("systems page must use unified library-shell")
    if not has_html_class(systems, "library-split"):
        fail("systems page must use library-split pane layout")
    if not has_html_class(systems, "library-index"):
        fail("systems page must include full catalogue index")
    if not has_html_class(systems, "library-panel"):
        fail("systems page must render catalogue panels")
    if 'class="page-with-toc"' in systems:
        fail("systems must not use legacy scroll longform layout")
    if "Enterprise Data" not in systems:
        fail("systems index must include enterprise catalogue section")
    if 'class="library-index-group"' not in systems:
        fail("systems index must use non-clickable group headers for nested sections")
    if 'class="proof-case"' not in systems:
        fail("systems catalogue must include proof-case rows")
    proof_case_bodies = re.findall(
        r'<article class="proof-case">([\s\S]*?)</article>', systems
    )
    if any("<h3" in body for body in proof_case_bodies):
        fail("systems proof-case rows must not repeat titles in panel body")
    if 'data-panel-id="prudential-singapore-senior-data-engineer-solutioning-architecture"' not in systems:
        fail("systems index must link Prudential case panel")
    if 'data-record="SYS-01"' not in systems:
        fail("systems must embed SYS-01 record panel")
    if "NOTE-2026-005" not in systems:
        fail("systems must include NOTE-2026-005 record panel")
    if 'class="record-impact"' not in systems:
        fail("SYS-01 record must carry quantified impact lines")
    if 'related-paths-label' not in systems:
        fail("systems record panels must include related paths")
    if not has_html_class(systems, "library-strip"):
        fail("systems page must include cross-link strip")

    notes = (DIST / "notes" / "index.html").read_text(encoding="utf-8")
    credentials = (DIST / "credentials" / "index.html").read_text(encoding="utf-8")
    for label, html in (("Notes", notes), ("Credentials", credentials)):
        if not has_html_class(html, "library-shell"):
            fail(f"{label} must use unified library-shell")
        if 'class="page-with-toc"' in html:
            fail(f"{label} must not use legacy scroll longform layout")
        if not has_html_class(html, "header-search"):
            fail(f"{label} must include header search like other primary tabs")

    portfolio = systems

    css = (DIST / "styles.css").read_text(encoding="utf-8")
    if "main.page .entrance h1" not in css and "main.page .hero h1" not in css:
        fail("styles.css missing entrance/hero h1 display typography")
    if "Crimson Pro" not in css:
        fail("styles.css must load Crimson Pro display face")
    if "Source Sans 3" not in css:
        fail("styles.css must load Source Sans 3 body face")
    if not re.search(
        r"main\.page h2\s*\{[^}]*font-family:\s*var\(--font-display\)",
        css,
        re.S,
    ):
        fail("main.page h2 must use font-display for unified home/inner typography")
    if not re.search(
        r"main\.page \.(entrance|hero) h1\s*\{[^}]*font-family:\s*var\(--font-display\)",
        css,
        re.S,
    ):
        fail("entrance h1 must set font-family: var(--font-display)")
    if not re.search(
        r"main\.page \.(entrance|hero) h1\s*\{[^}]*font-size:\s*var\(--text-display-hero\)",
        css,
        re.S,
    ):
        fail("entrance h1 must set font-size: var(--text-display-hero)")
    if not re.search(
        r"main\.page \.(entrance|hero) h1\s*\{[^}]*font-weight:\s*600",
        css,
        re.S,
    ):
        fail("entrance h1 must set font-weight: 600")
    if re.search(
        r"\.header-actions\s*>\s*\.theme-toggle\s*\{[^}]*display:\s*none",
        css,
        re.S,
    ):
        fail("theme toggle must stay visible beside Menu at --bp-md (do not display:none)")
    if "scroll-behavior: auto" not in css:
        fail("styles.css missing scroll-behavior: auto for prefers-reduced-motion")
    if "repeat(3, minmax(0, 1fr))" in css and "outcome-strip" in css:
        fail("styles.css must not keep outcome-strip 3-column grid in hero")
    if "background-color: var(--bg-deep)" not in css:
        fail("styles.css missing solid background-color: var(--bg-deep)")
    if "position: sticky" not in css:
        fail("styles.css missing sticky header")
    if "--bg-elevated" not in css or "--focus-ring" not in css:
        fail("styles.css missing semantic tokens (--bg-elevated / --focus-ring)")
    if "--text-default" not in css:
        fail("styles.css missing --text-default")
    if css.count("var(--glow)") != 1:
        fail("styles.css must use a single var(--glow) layer")
    if "rgb(212 163 92 / 12%)" not in css:
        fail("styles.css dark glow token must use amber pool (12%)")
    if "rgb(212 163 92 / 10%)" not in css:
        fail("styles.css light glow must use soft amber wash (10%)")
    if "--accent-link" not in css:
        fail("styles.css missing --accent-link for light body links")
    if "--text-scale" not in css:
        fail("styles.css missing --text-scale for responsive reading sizes")
    if "transform: scale(" in css:
        fail("assembled CSS must not include scale() transforms")

    bg_deep = _token_hex(css, "--bg-deep")
    bg_mid = _token_hex(css, "--bg-mid")
    bg_elevated = _token_hex(css, "--bg-elevated")
    text_default = _token_hex(css, "--text-default")
    text_muted = _token_hex(css, "--text-muted")
    text_faint = _token_hex(css, "--text-faint")
    accent = _token_hex(css, "--accent")
    if bg_elevated.lower() != "#2a2118":
        fail(f"--bg-elevated must be walnut #2a2118, got {bg_elevated}")
    if bg_mid.lower() != "#1c1612":
        fail(f"--bg-mid must be walnut #1c1612, got {bg_mid}")
    if accent.lower() != "#c49a5a":
        fail(f"--accent brass must stay #c49a5a, got {accent}")
    pairs = (
        ("--text-default on --bg-deep", text_default, bg_deep, 4.5),
        ("--text-default on --bg-elevated", text_default, bg_elevated, 4.5),
        ("--text-muted on --bg-deep", text_muted, bg_deep, 4.5),
        ("--text-muted on --bg-elevated", text_muted, bg_elevated, 4.5),
        ("--text-faint on --bg-deep", text_faint, bg_deep, 4.5),
        ("--text-faint on --bg-elevated", text_faint, bg_elevated, 4.5),
        ("--accent on --bg-deep", accent, bg_deep, 3.0),
        ("--accent on --bg-elevated", accent, bg_elevated, 3.0),
    )
    for label, fg, bg, minimum in pairs:
        ratio = _contrast(fg, bg)
        if ratio < minimum:
            fail(f"a11y contrast {label} is {ratio:.2f}:1 (need ≥ {minimum}:1)")

    light = _light_block(css)
    light_bg = _token_hex(light, "--bg-deep")
    light_mid = _token_hex(light, "--bg-mid")
    light_elev = _token_hex(light, "--bg-elevated")
    light_strong = _token_hex(light, "--text-strong")
    light_text = _token_hex(light, "--text-default")
    light_muted = _token_hex(light, "--text-muted")
    light_link = _token_hex(light, "--accent-link")
    light_hover = _token_hex(light, "--accent-hover")
    if light_bg.lower() != "#e8dfd0":
        fail(f"light --bg-deep must be #e8dfd0, got {light_bg}")
    if light_mid.lower() != "#ddd2c0":
        fail(f"light --bg-mid must be #ddd2c0, got {light_mid}")
    if light_elev.lower() != "#f5efe4":
        fail(f"light --bg-elevated must be #f5efe4, got {light_elev}")
    if light_strong.lower() != "#171414":
        fail(f"light --text-strong must be #171414, got {light_strong}")
    if light_text.lower() != "#2a2724":
        fail(f"light --text-default must be #2A2724, got {light_text}")
    if light_muted.lower() != "#5c5548":
        fail(f"light --text-muted must be #5c5548, got {light_muted}")
    if light_link.lower() != "#6b4f10":
        fail(f"light --accent-link must be #6b4f10, got {light_link}")
    if light_hover.lower() != "#5c450e":
        fail(f"light --accent-hover must be #5c450e, got {light_hover}")
    if "#ffffff" in light.lower() or "#fff;" in light.lower():
        fail("light theme must not use pure #FFFFFF")
    light_pairs = (
        ("light --text-default on --bg-deep", light_text, light_bg, 4.5),
        ("light --text-muted on --bg-deep", light_muted, light_bg, 4.5),
        ("light --text-muted on --bg-mid", light_muted, light_mid, 4.5),
        ("light --accent-link on --bg-deep", light_link, light_bg, 4.5),
        ("light --accent-link on --bg-mid", light_link, light_mid, 4.5),
        ("light --text-default on --bg-elevated", light_text, light_elev, 4.5),
    )
    for label, fg, bg, minimum in light_pairs:
        ratio = _contrast(fg, bg)
        if ratio < minimum:
            fail(f"a11y contrast {label} is {ratio:.2f}:1 (need ≥ {minimum}:1)")

    if 'class="case-outcome"' not in portfolio:
        fail("portfolio missing case-outcome class on project rows")
    if 'class="case-tools' not in portfolio:
        fail("portfolio missing case-tools class")
    if "folio-deck" not in portfolio:
        fail("work page missing folio-deck list default")
    if "folio-toolbar" in portfolio:
        fail("work page must not ship an inert folio-toolbar")
    if "folio-toolbar" in credentials:
        fail("credentials must not ship an inert folio-toolbar")
    if ">Systems<" not in portfolio and "Systems —" not in portfolio:
        fail("systems page must title as Systems")
    if "Senior Manager, Cloud Economics and Intelligence" not in portfolio:
        fail("Prudential title must match master CV (Senior Manager, Cloud Economics…)")
    if "Senior Data Engineer, Solutioning" in portfolio:
        fail("Prudential title must not remain Senior Data Engineer")
    if 'id="skillup-mtech-capstone"' not in portfolio:
        fail("work page missing SkillUP heading id")
    if 'id="stb-data-engineer-applied-ml"' not in portfolio:
        fail("work page missing STB applied-ML enterprise case")
    if 'class="library-index-group"' not in portfolio:
        fail("systems index must use non-clickable group headers for nested sections")
    if "proof-deck" not in portfolio:
        fail("enterprise case panels must use proof-deck styling")
    if not re.search(
        r"\.section-fold--public \.case-beats dt\s*\{[^}]*color:\s*var\(--text-muted\)",
        css,
    ):
        fail("public fold dt must use --text-muted (AA on light --bg-mid)")
    if re.search(
        r"\.section-fold--public \.case-beats dt\s*\{[^}]*color:\s*var\(--text-faint\)",
        css,
    ):
        fail("public fold dt must not use --text-faint on --bg-mid")
    if "Enterprise delivery" not in portfolio:
        fail("work page missing enterprise delivery kicker")
    if "Public architectures" not in portfolio:
        fail("work page missing public-architecture kicker")
    if "summarized here" in portfolio or "Public summary on this page" in portfolio:
        fail("enterprise evidence must link out, not use a page-summary placeholder")
    if "application-level cost attribution" not in portfolio:
        fail("Prudential problem must state the FinOps attribution gap")
    if "Unity Catalog" not in portfolio or "Declarative Asset Bundles" not in portfolio:
        fail("Prudential decision must map governance tools to the governance gap")
    if 'evidence_href' not in (DATA / "site.json").read_text(encoding="utf-8"):
        fail("site.json missing evidence_href for verifiable evidence beats")
    if portfolio.count('class="proof-case"') < 3:
        fail("enterprise section must feature at least three cases")
    if not re.search(
        r'class="case-beats"[^>]*>[\s\S]*linkedin\.com/in/yzouyang',
        portfolio,
        re.I,
    ):
        fail("enterprise evidence must link to an external artifact")
    if "Technical Documentation" in portfolio:
        fail("tutorial tools must be curated to at most 5 labels")
    for match in re.finditer(r'class="case-tools[^"]*"[^>]*>([^<]+)', portfolio):
        raw = match.group(1)
        if raw.startswith("Tools:"):
            raw = raw[len("Tools:") :]
        labels = [part.strip() for part in raw.split(",") if part.strip()]
        if len(labels) > 5:
            fail(f"case-tools exceeds 5 labels: {labels}")
    if "first-party LinkedIn analytics" not in portfolio:
        fail("tutorial blurb must lead with the user outcome")
    ent_pos = portfolio.find("Enterprise Data")
    tut_pos = portfolio.find("Featured Tutorial")
    if ent_pos == -1 or tut_pos == -1 or ent_pos > tut_pos:
        fail("enterprise summaries must precede tutorial/bootcamp sections")
    if 'id="prudential-singapore-senior-data-engineer-solutioning-architecture"' not in portfolio:
        fail("portfolio missing Prudential heading id for home selected-systems links")
    if 'id="sph-media-lead-data-engineer"' not in portfolio:
        fail("portfolio missing SPH heading id for home selected-systems links")
    for name, html in (("home", home), ("portfolio", portfolio), ("credentials", credentials)):
        if 'id="search"' not in html:
            fail(f"{name} missing #search")
        if 'class="page-search-label"' not in html:
            fail(f"{name} missing visible search label")
        if 'for="pagefind-search-input"' not in html:
            fail(f"{name} search label missing for=pagefind-search-input")
        if 'setAttribute("name", "q")' not in html:
            fail(f"{name} Pagefind input missing name attribute wiring")
    for name, html in (("portfolio", portfolio), ("credentials", credentials)):
        if not has_html_class(html, "library-shell"):
            fail(f"{name} missing library-shell")
        if not has_html_class(html, "library-index"):
            fail(f"{name} missing library index")
        if 'class="page-with-toc"' in html:
            fail(f"{name} must not use legacy page-with-toc scroll layout")

    styles_dir = ROOT / "src" / "styles"
    for part in (
        "tokens.css",
        "base.css",
        "chrome.css",
        "home.css",
        "library.css",
        "components.css",
        "longform.css",
        "search.css",
        "motion.css",
    ):
        if not (styles_dir / part).is_file():
            fail(f"missing style module src/styles/{part}")
    if "--- longform.css ---" not in css:
        fail("dist/styles.css was not assembled from src/styles modules")

    if 'class="library-index-sub"' not in credentials:
        fail("credentials index missing issuer subcategory list")
    if 'class="library-index-group"' not in credentials:
        fail("credentials professional section must be a non-clickable group header")
    if 'class="credentials-featured-grid"' not in credentials:
        fail("credentials featured panel must use credential cards grid")
    if 'class="credential-card"' not in credentials:
        fail("credentials featured panel missing credential cards")
    if 'class="library-index-notes"' in credentials:
        fail("credentials sidebar footer must not include notes list")
    if 'data-panel-id="verify-credentials"' in credentials:
        fail("credentials must not include separate Verify index panel")
    if "Credly" not in credentials or "Databricks" not in credentials:
        fail("credentials must include issuer verify links in cert entries")
    if "status-badge--ongoing" not in credentials or "MTech" not in credentials:
        fail("MTech must be flagged as in progress when end date is in the future")
    if re.search(r">https?://[^<]+<", credentials):
        fail("credentials must not print raw verify URLs as link text")

    about = (DIST / "about" / "index.html").read_text(encoding="utf-8")
    home_target = with_base(site, "/")
    if home_target not in about:
        fail("about redirect must target home")
    if has_html_class(about, "library-shell"):
        fail("about must redirect to home, not ship library shell")
    if not has_html_class(credentials, "library-shell"):
        fail("credentials missing library-shell layout")
    if not has_html_class(credentials, "library-index"):
        fail("credentials missing library index")
    if 'data-panel-id="core-competencies"' in credentials:
        fail("credentials must not host core competencies (they live on home)")
    if 'data-panel-id="career-journey"' in credentials:
        fail("credentials must not host career journey panel")
    if 'class="library-index-footer"' in credentials:
        fail("credentials must not ship sidebar footer (removed with Career Journey)")
    if 'href="/career-journey/"' in credentials:
        fail("credentials must not link to removed Career Journey route")
    if credentials.count('class="credential-card"') < 8:
        fail("credentials catalogue must use credential cards throughout")
    if 'class="embed-fallback"' in credentials or 'class="figma-open"' in credentials:
        fail("credentials must not embed Figma deck chrome")

    if "bit.ly/3GGyiXF" in portfolio:
        fail("systems must not link to legacy portfolio Bitly short")
    if "<iframe" in portfolio:
        fail("portfolio must not load a live Figma iframe (white canvas on dark page)")
    if "Klook Travel Planner" in portfolio and "Figma deck" not in portfolio:
        fail("Klook row must keep the compact Figma deck .links row")
    assert_no_empty_static_frames(portfolio, "portfolio")
    assert_no_empty_static_frames(credentials, "credentials")
    if "bit.ly/4m4fqki" in credentials or "bit.ly/3GGyiXF" in credentials:
        fail("credentials must not link to legacy Bitly shorts — full catalogue lives on-site")
    if 'data-panel-id="featured-credentials"' in credentials:
        fail("credentials must not use a featured subset — full export catalogue only")
    empty_preview = figma_embed_html(
        "Klook Travel Planner Capstone",
        "https://embed.figma.com/deck/example",
        "https://www.figma.com/deck/example",
    )
    if "embed-frame-static" in empty_preview:
        fail("figma_embed_html must not emit embed-frame-static without a poster")
    if "embed-fallback" not in empty_preview:
        fail("figma_embed_html without poster must keep the compact fallback link")
    poster_preview = figma_embed_html(
        "Klook Travel Planner Capstone",
        "https://embed.figma.com/deck/example",
        "https://www.figma.com/deck/example",
        poster="/assets/klook-poster.png",
    )
    if "<img" not in poster_preview or "embed-frame-static" not in poster_preview:
        fail("figma_embed_html with poster must emit a real <img> inside embed-frame-static")
    if "aspect-ratio" in poster_preview:
        fail("poster markup must not hardcode a fill-only aspect-ratio box")
    if 'class="library-index-sub"' not in portfolio:
        fail("systems catalogue index missing nested subcategory list")

    if not has_html_class(notes, "library-shell"):
        fail("notes page must use library-shell")
    if 'data-panel-id="featured-essay"' in notes or 'id="start-here"' in notes:
        fail("notes must not use editorial bucket panels (Featured/Start here/More writing)")
    if 'data-panel-id="elsewhere"' in notes:
        fail("notes must not duplicate footer external links in the index")
    if 'data-panel-id="NOTE-' not in notes:
        fail("notes index must list individual NOTE-* catalogue entries")
    if 'class="library-index-group"' not in notes:
        fail("notes index must group essays by category")
    if "note-taxonomy" not in notes or "note-category" not in notes:
        fail("notes panels must show category taxonomy")
    if "medium.com/@kunojilym" not in notes:
        fail("notes page missing Medium writing links")
    if "notes-entry" not in notes:
        fail("notes page must render per-note entry panels")
    note_entry_bodies = re.findall(
        r'<article class="notes-entry">([\s\S]*?)</article>', notes
    )
    if any("<h2" in body for body in note_entry_bodies):
        fail("notes library panels must not duplicate titles inside entry body")
    if "grouped by category" not in notes:
        fail("notes page missing category/timeline lede")

    if not (DIST / "perspectives" / "index.html").is_file():
        fail("perspectives/index.html redirect missing")
    if DIST.joinpath("chrome.js").is_file() is False:
        fail("dist/chrome.js missing")
    if not (DIST / "work" / "index.html").is_file():
        fail("work/index.html redirect missing")

    contact_page = DIST / "contact" / "index.html"
    if not contact_page.is_file():
        fail("contact/index.html redirect missing")
    contact_html = contact_page.read_text(encoding="utf-8")
    if home_target not in contact_html:
        fail("contact redirect must target home")
    if "<h1>Connect</h1>" in contact_html:
        fail("contact must redirect to home, not ship a Connect page")
    redirects = (DIST / "_redirects").read_text(encoding="utf-8")
    if not re.search(r"/about\s+\S*/\s+301", redirects):
        fail("_redirects must 301 /about to home")
    if not re.search(r"/about/\s+\S*/\s+301", redirects):
        fail("_redirects must 301 /about/ to home")
    if not re.search(r"/contact\s+\S*/\s+301", redirects):
        fail("_redirects must 301 /contact to home")
    if not re.search(r"/contact/\s+\S*/\s+301", redirects):
        fail("_redirects must 301 /contact/ to home")

    pf = DIST / "pagefind" / "pagefind-ui.js"
    if not pf.is_file():
        fail("dist/pagefind/pagefind-ui.js missing")

    photo = site.get("person", {}).get("photo") or ""
    if photo:
        asset = DIST.joinpath(*photo.strip("/").split("/"))
        if not asset.is_file():
            fail(f"profile asset missing in dist: {photo}")

    blob = "\n".join((DIST / rel).read_text(encoding="utf-8") for rel, _ in ROUTES).lower()
    for needle in FORBIDDEN:
        if needle in blob:
            fail(f"built HTML contains forbidden domain: {needle}")

    cj_page = DIST / "career-journey" / "index.html"
    if cj_page.is_file():
        cj_html = cj_page.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' not in cj_html or home_target not in cj_html:
            fail("career-journey must redirect to home")

    print("test_site_build ok")


if __name__ == "__main__":
    main()
