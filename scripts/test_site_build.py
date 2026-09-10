#!/usr/bin/env python3
"""Contract checks against built dist/ (run after scripts/build.py)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from build import figma_embed_html, resolve_enterprise_overlay

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DATA = ROOT / "data"

FORBIDDEN = ("prudential.com", "u.nus.edu", "gatech.edu")
ROUTES = (
    ("index.html", "Home"),
    ("about/index.html", "About"),
    ("portfolio/index.html", "Work"),
    ("perspectives/index.html", "Perspectives"),
    ("credentials/index.html", "Credentials"),
)


def fail(msg: str) -> None:
    print(f"test_site_build error: {msg}", file=sys.stderr)
    raise SystemExit(1)


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
        fail("home cta-row must have exactly one btn-primary (View selected work)")
    if 'class="btn btn-primary"' not in cta_html or "View selected work" not in cta_html:
        fail("home cta-row missing primary View selected work CTA")
    if cta_html.count('class="btn"') != 1:
        fail("home cta-row must keep Contact as the only secondary .btn")
    if ">Contact</a>" not in cta_html:
        fail("home cta-row missing secondary Contact .btn")
    if "Specialist" in home.split("<h1>", 1)[-1].split("</section>", 1)[0]:
        fail("hero must not use vague Specialist positioning")
    if "CTO" in home or "CDAO" in home.split("hero-copy", 1)[-1].split("</section>", 1)[0]:
        fail("hero must not claim CTO/CDAO")
    if 'class="portrait-chip"' not in home:
        fail("home missing portrait-chip")
    if 'id="contact"' not in home:
        fail("home missing #contact section")
    if 'class="selected-systems"' not in home:
        fail("home missing selected-systems strip")
    if home.find('class="selected-systems"') > home.find('id="contact"'):
        fail("selected-systems must appear before #contact")
    if home.find('class="cta-row"') > home.find('class="selected-systems"'):
        fail("selected-systems must appear after CTAs")
    selected = home.split('class="selected-systems"', 1)[1]
    if 'class="operating-themes"' in selected:
        selected = selected.split('class="operating-themes"', 1)[0]
    else:
        selected = selected.split('id="contact"', 1)[0]
    if selected.count("<li>") < 2 or selected.count("<li>") > 3:
        fail("selected-systems must have 2–3 editorial rows")
    if "Prudential" not in selected or "SPH Media" not in selected:
        fail("selected-systems must include Prudential / SPH-class enterprise cases")
    if "SkillUP" in selected:
        fail("selected-systems must not equate a capstone with enterprise delivery")
    if "Tourism Board" not in selected and "STB" not in selected:
        fail("selected-systems must include a third enterprise case (applied AI / STB)")
    if 'class="case-beats"' not in selected:
        fail("selected-systems rows must follow problem → role → decision → outcome → evidence")
    if "Tools:" not in selected:
        fail("selected-systems rows must keep tools last")
    if "/portfolio/" not in selected:
        fail("selected-systems must link through to /portfolio/")
    if "folio-toolbar" in home:
        fail("home must not ship an inert folio-toolbar")
    if "View all" in selected:
        fail("selected-systems must not ship an unwired View all control")
    if 'class="operating-themes"' not in home:
        fail("home missing operating-themes")
    if home.count("<h3>") < 4 or "Cloud economics" not in home:
        fail("home must list four operating themes")
    if "class=\"theme-note\"" not in home and "theme-note" not in home:
        fail("home missing public-architecture / mentoring contribution note")
    if "tel:" in home or "+65" in home:
        fail("home must not expose a visitor-facing phone number")
    if "PUBLIC contacts only" in home:
        fail("home must not show the visitor-facing contacts governance note")
    if 'class="nav-elsewhere"' not in home:
        fail("desktop nav missing Elsewhere disclosure")
    desktop_nav = home.split('class="site-nav site-nav-desktop"', 1)[1].split("</nav>", 1)[0]
    if "nav-elsewhere" not in desktop_nav:
        fail("Elsewhere control must live in desktop primary nav")
    if ">Blog</a>" not in desktop_nav.split("nav-elsewhere-panel", 1)[-1]:
        fail("Elsewhere panel must still contain Blog")
    if ">GitHub</a>" not in desktop_nav.split("nav-elsewhere-panel", 1)[-1]:
        fail("Elsewhere panel must contain GitHub")
    if ">Work</a>" not in desktop_nav:
        fail("desktop nav missing Work")
    if ">Perspectives</a>" not in desktop_nav:
        fail("desktop nav missing Perspectives")
    if ">Contact</a>" not in desktop_nav:
        fail("desktop nav missing Contact")
    if ">Portfolio</a>" in desktop_nav.split("nav-elsewhere", 1)[0]:
        fail("desktop nav still labels Work as Portfolio")
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
        fail("header Contact control must not duplicate Contact now that it is in primary nav")
    if 'class="skip-link"' not in home or 'href="#main"' not in home:
        fail("home missing skip-link to #main")
    if 'id="main"' not in home:
        fail("home missing main#main skip target")
    if 'href="/contact/"' in home and 'nav' in home:
        # /contact/ remains a redirect, not a primary nav href
        if 'aria-label="Primary"' in home and 'href="/contact/"' in home.split('aria-label="Primary"')[1].split("</nav>")[0]:
            fail("primary nav still links to /contact/ instead of /#contact")

    css = (DIST / "styles.css").read_text(encoding="utf-8")
    if "main.page .hero h1" not in css:
        fail("styles.css missing main.page .hero h1 (must beat main.page h1 for Fraunces)")
    if "main.page .selected-systems h2" not in css:
        fail("styles.css missing main.page .selected-systems h2 (must beat main.page h2)")
    if not re.search(
        r"main\.page \.selected-systems h2\s*\{[^}]*margin:\s*0 0 var\(--space-5\)",
        css,
        re.S,
    ):
        fail("selected-systems h2 must set margin: 0 0 var(--space-5)")
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
        r"\.header-actions\s*>\s*\.theme-toggle\s*\{[^}]*display:\s*none",
        css,
        re.S,
    ):
        fail("theme toggle must stay visible beside Menu at --bp-md (do not display:none)")
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
    if css.count("var(--glow)") != 1:
        fail("styles.css must use a single var(--glow) layer")
    if "rgb(55 90 78 / 22%)" not in css:
        fail("styles.css dark glow token must stay the desaturated boardroom value")
    if "rgb(55 90 78 / 10%)" not in css:
        fail("styles.css light glow must be a soft sage wash (10%)")
    if "--accent-link" not in css:
        fail("styles.css missing --accent-link for light body links")
    if re.search(r"\.cj-js\s+\.cj-slide[^{]*\{[^}]*scale\s*\(", css):
        fail("career journey .cj-slide must not use scale transforms")
    if "transform: scale(" in css:
        fail("assembled CSS must not include scale() transforms")
    if not re.search(
        r"@media \(prefers-reduced-motion: reduce\).*?\.cj-js \.cj-slide,"
        r".*?opacity:\s*1 !important.*?transform:\s*none !important",
        css,
        re.S,
    ):
        fail("prefers-reduced-motion must force .cj-slide opacity 1 / transform none")
    if not re.search(
        r"@media \(prefers-reduced-motion: reduce\).*?\[data-step\].*?"
        r"opacity:\s*1 !important.*?transform:\s*none !important",
        css,
        re.S,
    ):
        fail("prefers-reduced-motion must reveal all [data-step] (not animation:none alone)")

    bg_deep = _token_hex(css, "--bg-deep")
    bg_mid = _token_hex(css, "--bg-mid")
    bg_elevated = _token_hex(css, "--bg-elevated")
    text_default = _token_hex(css, "--text-default")
    text_muted = _token_hex(css, "--text-muted")
    text_faint = _token_hex(css, "--text-faint")
    accent = _token_hex(css, "--accent")
    if bg_elevated.lower() != "#1a2420":
        fail(f"--bg-elevated must be charcoal #1a2420, got {bg_elevated}")
    if bg_mid.lower() != "#15201c":
        fail(f"--bg-mid must be charcoal #15201c, got {bg_mid}")
    if accent.lower() != "#d4a35c":
        fail(f"--accent gold must stay #d4a35c, got {accent}")
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
    if light_bg.lower() != "#f4f0e8":
        fail(f"light --bg-deep must be #F4F0E8, got {light_bg}")
    if light_mid.lower() != "#ebe6dc":
        fail(f"light --bg-mid must be #EBE6DC, got {light_mid}")
    if light_elev.lower() != "#fffbf5":
        fail(f"light --bg-elevated must be #FFFBF5, got {light_elev}")
    if light_strong.lower() != "#171414":
        fail(f"light --text-strong must be #171414, got {light_strong}")
    if light_text.lower() != "#2a2724":
        fail(f"light --text-default must be #2A2724, got {light_text}")
    if light_muted.lower() != "#5c6b63":
        fail(f"light --text-muted must be #5C6B63, got {light_muted}")
    if light_link.lower() != "#856012":
        fail(f"light --accent-link must be #856012, got {light_link}")
    if light_hover.lower() != "#7a5a12":
        fail(f"light --accent-hover must be #7A5A12, got {light_hover}")
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

    portfolio = (DIST / "portfolio" / "index.html").read_text(encoding="utf-8")
    credentials = (DIST / "credentials" / "index.html").read_text(encoding="utf-8")
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
    if ">Work<" not in portfolio and "Work —" not in portfolio:
        fail("work page must title as Work")
    if "Senior Manager, Cloud Economics and Intelligence" not in portfolio:
        fail("Prudential title must match master CV (Senior Manager, Cloud Economics…)")
    if "Senior Data Engineer, Solutioning" in portfolio:
        fail("Prudential title must not remain Senior Data Engineer")
    if 'id="skillup-mtech-capstone"' not in portfolio:
        fail("work page missing SkillUP heading id")
    if 'id="stb-data-engineer-applied-ml"' not in portfolio:
        fail("work page missing STB applied-ML enterprise case")
    if "section-fold--enterprise" not in portfolio or "proof-deck" not in portfolio:
        fail("work page missing enterprise delivery fold")
    if "section-fold--public" not in portfolio:
        fail("work page missing public-architecture fold")
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
        labels = [part.strip() for part in match.group(1).removeprefix("Tools:").split(",") if part.strip()]
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
    if "/portfolio/#stb-data-engineer-applied-ml" not in home:
        fail("home selected-systems must deep-link the STB case")
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
    if 'class="verify-panel"' not in credentials:
        fail("credentials missing VERIFY panel under the lede")
    if "Credly" not in credentials or "Databricks" not in credentials:
        fail("VERIFY panel must include issuer hubs from public records")
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
        if not re.search(r'<summary class="section-fold-summary" id="[^"]+"', html):
            fail(f"{name} section-fold summary missing id for TOC anchors")
        if not re.search(
            r'<summary class="section-fold-summary"[^>]*role="heading"[^>]*aria-level="2"',
            html,
        ):
            fail(f"{name} section-fold summary must be the heading (role=heading)")
        if re.search(
            r'<h2 class="visually-hidden">',
            html,
        ):
            fail(f"{name} must not duplicate fold titles with a visually-hidden h2")
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
    if "Klook Travel Planner" in portfolio and "Figma deck" not in portfolio:
        fail("Klook row must keep the compact Figma deck .links row")
    assert_no_empty_static_frames(portfolio, "portfolio")
    assert_no_empty_static_frames(about, "about")
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
    if 'class="page-toc-sub"' not in portfolio:
        fail("portfolio TOC missing nested subcategory list")
    if 'class="section-fold"' not in portfolio or 'class="section-fold"' not in credentials:
        fail("portfolio/credentials missing collapsible section-fold")
    if 'class="page-toc-sub"' not in credentials:
        fail("credentials TOC missing issuer subcategory list")

    perspectives = DIST / "perspectives" / "index.html"
    if not perspectives.is_file():
        fail("perspectives/index.html missing")
    perspectives_html = perspectives.read_text(encoding="utf-8")
    if "Start here" not in perspectives_html:
        fail("perspectives missing start-here section")
    if "medium.com/@kunojilym" not in perspectives_html:
        fail("perspectives missing Medium writing links")
    if DIST.joinpath("chrome.js").is_file() is False:
        fail("dist/chrome.js missing")
    work_page = DIST / "work" / "index.html"
    if not work_page.is_file():
        fail("work/index.html redirect missing")

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
        if cj_html.lower().count("<h1") != 1:
            fail("career-journey page must have a single h1 (page chrome; slide titles are h2+)")

    print("test_site_build ok")


if __name__ == "__main__":
    main()
