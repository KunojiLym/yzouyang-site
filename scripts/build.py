#!/usr/bin/env python3
"""Build static Phase 1 pages from data/export_public.json + data/site.json."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"
SRC = ROOT / "src"


def normalize_base(base: object) -> str:
    text = ("" if base is None else str(base)).strip()
    if not text or text == "/":
        return ""
    return "/" + text.strip("/")


def with_base(site: dict, path: str) -> str:
    """Prefix site-root paths with base_path (for GitHub project Pages)."""
    if not path or path.startswith(("http://", "https://", "#", "mailto:", "tel:")):
        return path
    base = normalize_base(site.get("base_path", ""))
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def esc(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return s.strip("-") or "section"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def urls_from_bullets(bullets: list | None) -> list[str]:
    out: list[str] = []
    for item in bullets or []:
        if isinstance(item, str) and item.startswith("http"):
            out.append(item)
    return out


def primary_and_short(urls: list[str]) -> tuple[str | None, str | None]:
    primary = None
    short = None
    for url in urls:
        if "bit.ly" in url and short is None:
            short = url
        elif primary is None:
            primary = url
    if primary is None and short:
        primary = short
        short = None
    return primary, short


def resolve_npx() -> str | None:
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
            "(search UI will 404 until Node is available or re-run without --skip-pagefind)",
            file=sys.stderr,
        )
        return
    cmd = [npx, "--yes", "pagefind@1.3.0", "--site", "dist"]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=str(ROOT), check=True)


def nav_html(site: dict, active: str, *, grouped: bool = False) -> str:
    parts: list[str] = []
    external_started = False
    for item in site.get("nav") or []:
        label = esc(item.get("label", ""))
        raw_href = str(item.get("href", "#"))
        external = bool(item.get("external"))
        if grouped and external and not external_started:
            parts.append('<p class="nav-group-label">Elsewhere</p>')
            external_started = True
        href = esc(raw_href if external else with_base(site, raw_href))
        classes = []
        if external:
            classes.append("external")
        attrs = f' href="{href}"'
        if classes:
            attrs += f' class="{" ".join(classes)}"'
        if external:
            attrs += ' target="_blank" rel="noopener noreferrer"'
        if not external and item.get("label") == active:
            attrs += ' aria-current="page"'
        parts.append(f"<a{attrs}>{label}</a>")
    return "\n      ".join(parts)


STYLE_PARTS = (
    "tokens.css",
    "base.css",
    "chrome.css",
    "home.css",
    "components.css",
    "longform.css",
    "search.css",
    "motion.css",
)


def assemble_styles() -> str:
    """Concatenate src/styles/*.css into a single stylesheet for dist/."""
    styles_dir = SRC / "styles"
    chunks: list[str] = [
        "/* Assembled by scripts/build.py from src/styles/ — do not edit dist copy */\n"
    ]
    for name in STYLE_PARTS:
        path = styles_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"missing style module: {path}")
        chunks.append(f"\n/* --- {name} --- */\n")
        chunks.append(path.read_text(encoding="utf-8").rstrip() + "\n")
    return "".join(chunks)


def toc_html(entries: list[dict], *, sidebar: bool = False) -> str:
    """Render on-this-page nav. entries: {id, label, children?} trees."""
    if not entries:
        return ""

    def render_list(nodes: list[dict], *, nested: bool = False) -> str:
        cls = ' class="page-toc-sub"' if nested else ""
        lines = [f"    <ul{cls}>"]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            eid = str(node.get("id") or "")
            label = str(node.get("label") or eid)
            if not eid:
                continue
            kids = node.get("children") or []
            child_html = ""
            if kids:
                child_html = "\n" + render_list(kids, nested=True)
            lines.append(
                f'      <li><a href="#{esc(eid)}">{esc(label)}</a>{child_html}</li>'
            )
        lines.append("    </ul>")
        return "\n".join(lines)

    classes = "page-toc page-toc-sidebar" if sidebar else "page-toc"
    label = (
        '    <p class="page-toc-label">On this page</p>\n' if sidebar else ""
    )
    return (
        f'    <nav class="{classes}" aria-label="On this page">\n'
        f"{label}"
        f"{render_list(entries)}\n"
        "    </nav>\n"
    )


def longform_page(
    *,
    title: str,
    lede_html: str,
    toc: list[dict],
    body: str,
    search: bool = True,
) -> str:
    """Long-page shell: sticky sidebar TOC + main column (design-system longform)."""
    search_html = '        <div id="search"></div>\n' if search else ""
    return f"""    <div class="page-with-toc">
{toc_html(toc, sidebar=True)}      <div class="page-main">
        <h1>{title}</h1>
        {lede_html}
{search_html}{body}
      </div>
    </div>
"""


def section_fold_open(section_id: str, heading: str, *, level: str = "h2") -> str:
    """Start a collapsible long-form section (default open)."""
    tag = "h2" if level == "h2" else "h3"
    return (
        f'    <details class="section-fold" open>\n'
        f'      <summary class="section-fold-summary">'
        f'<{tag} id="{esc(section_id)}">{heading}</{tag}></summary>\n'
        f'      <div class="section-fold-body">\n'
    )


def section_fold_close() -> str:
    return "      </div>\n    </details>\n"


def figma_embed_html(
    title: str,
    embed: str,
    link: str | None = None,
    *,
    link_label: str = "Open deck",
    tall: bool = False,
) -> str:
    frame_class = "embed-frame embed-frame-tall" if tall else "embed-frame"
    fallback = ""
    if link:
        fallback = (
            f'<a class="embed-fallback" href="{esc(link)}" target="_blank" '
            f'rel="noopener noreferrer"><strong>{esc(link_label)}</strong>'
            f" — opens in Figma if the embed does not load</a>"
        )
    return f"""
      <div class="embed-wrap">
        {fallback}
        <div class="{frame_class}">
          <iframe
            title="{esc(title)}"
            src="{esc(embed)}"
            allowfullscreen
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
          ></iframe>
        </div>
      </div>"""


def analytics_head(site: dict) -> str:
    """Optional GA4 + Jetpack Stats (continuity with live WP)."""
    analytics = site.get("analytics") or {}
    chunks: list[str] = []

    ga_id = (analytics.get("ga_measurement_id") or "").strip()
    if ga_id:
        gid = esc(ga_id)
        chunks.append(
            f"""  <script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{ dataLayer.push(arguments); }}
    gtag('js', new Date());
    gtag('config', '{gid}', {{ anonymize_ip: true }});
  </script>"""
        )

    return "\n".join(chunks)


def analytics_body(site: dict, active: str) -> str:
    analytics = site.get("analytics") or {}
    chunks: list[str] = []

    jetpack = analytics.get("jetpack") or {}
    if jetpack.get("enabled"):
        blog_id = esc(str(jetpack.get("blog_id") or ""))
        if blog_id:
            pages = jetpack.get("pages") or {}
            post_id = esc(str(pages.get(active, "0")))
            tz = esc(str(jetpack.get("timezone", "8")))
            script = esc(str(jetpack.get("script") or "https://stats.wp.com/e-202632.js"))
            chunks.append(
                f"""  <script>
    window._stq = window._stq || [];
    window._stq.push([
      "view",
      {{
        v: "ext",
        blog: "{blog_id}",
        post: "{post_id}",
        tz: "{tz}",
        srv: window.location.hostname,
        j: "1:16.0.1"
      }}
    ]);
    window._stq.push(["clickTrackerInit", "{blog_id}", "{post_id}"]);
  </script>
  <script defer src="{script}"></script>"""
            )

    diy = analytics.get("diy") or {}
    if diy.get("enabled"):
        collect = esc(str(diy.get("collect_url") or "").strip())
        honor = "true" if diy.get("honor_dnt", True) else "false"
        track_src = esc(with_base(site, "/track.js"))
        chunks.append(
            f'  <script defer src="{track_src}" data-collect-url="{collect}" '
            f'data-honor-dnt="{honor}"></script>'
        )

    return "\n".join(chunks)


def footer_html(site: dict) -> str:
    person = site["person"]
    contact = site["contact"]
    ext = site["external"]
    year = date.today().year
    return f"""  <footer class="site-footer">
    <p>&copy; {year} {esc(person.get("full_name") or "yzouyang")}</p>
    <p class="footer-links">
      <a href="mailto:{esc(contact.get("email") or "")}">{esc(contact.get("email") or "")}</a>
      <a class="external" href="{esc(ext.get("linkedin") or "")}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
      <a class="external" href="{esc(ext.get("medium") or "")}" target="_blank" rel="noopener noreferrer">Medium</a>
      <a class="external" href="{esc(ext.get("blog") or "")}" target="_blank" rel="noopener noreferrer">Blog</a>
    </p>
  </footer>"""


def layout(site: dict, title: str, active: str, body: str, *, pagefind: bool = False) -> str:
    person = site["person"]
    brand = esc(person.get("brand", "yzouyang"))
    page_title = f"{esc(title)} — {brand}"
    pf_attr = " data-pagefind-body" if pagefind else ""
    head_analytics = analytics_head(site)
    body_analytics = analytics_body(site, active)
    css = esc(with_base(site, "/styles.css"))
    pf_css = esc(with_base(site, "/pagefind/pagefind-ui.css"))
    pf_js = esc(with_base(site, "/pagefind/pagefind-ui.js"))
    home = esc(with_base(site, "/"))
    contact_href = esc(with_base(site, "/#contact"))
    desktop_nav = nav_html(site, active)
    mobile_nav = nav_html(site, active, grouped=True)
    pf_css_tag = f'\n  <link rel="stylesheet" href="{pf_css}" />' if pagefind else ""
    pf_script = (
        f"""
  <script src="{pf_js}" type="text/javascript"></script>
  <script>
    window.addEventListener("DOMContentLoaded", () => {{
      const mount = document.querySelector("#search");
      if (mount && window.PagefindUI) {{
        new PagefindUI({{ element: "#search", showSubResults: true }});
      }}
    }});
  </script>"""
        if pagefind
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title}</title>
  <meta name="description" content="{esc(person.get('headline', ''))}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Sora:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="{css}" />{pf_css_tag}
{head_analytics}
</head>
<body>
  <div class="site-header-wrap">
  <header class="site-header">
    <p class="brand"><a href="{home}">{brand}</a></p>
    <div class="header-actions">
      <nav class="site-nav site-nav-desktop" aria-label="Primary">
        {desktop_nav}
      </nav>
      <a class="header-contact btn btn-primary" href="{contact_href}">Contact</a>
      <details class="nav-menu">
        <summary>Menu</summary>
        <nav class="site-nav" aria-label="Primary">
        {mobile_nav}
        </nav>
        <a class="header-contact btn btn-primary" href="{contact_href}">Contact</a>
      </details>
    </div>
  </header>
  </div>
  <main class="page" aria-label="{esc(title)}"{pf_attr}>
{body}
  </main>
{footer_html(site)}{pf_script}
{body_analytics}
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")


def build_home(site: dict, export: dict) -> str:
    person = site["person"]
    photo = person.get("photo") or ""
    location = str(person.get("location") or "").strip()
    platforms = [str(p) for p in (person.get("platforms") or []) if str(p).strip()][:4]

    outcome_bits: list[str] = []
    for row in (site.get("outcomes") or [])[:3]:
        if not isinstance(row, dict):
            continue
        metric = str(row.get("metric") or "").strip()
        label = str(row.get("label") or "").strip()
        if not metric or not label:
            continue
        outcome_bits.append(
            f"<li><span class=\"metric\">{esc(metric)}</span>"
            f"<span class=\"label\">{esc(label)}</span></li>"
        )
    outcome_html = ""
    if outcome_bits:
        outcome_html = (
            '        <ul class="outcome-strip" aria-label="Selected outcomes">\n'
            + "\n".join(f"          {b}" for b in outcome_bits)
            + "\n        </ul>"
        )

    proof_bits: list[str] = []
    if location:
        proof_bits.append(f"<li><strong>{esc(location)}</strong></li>")
    for p in platforms:
        proof_bits.append(f"<li>{esc(p)}</li>")
    proof_html = ""
    if proof_bits:
        proof_html = (
            '        <ul class="proof-strip" aria-label="Location and platforms">\n'
            + "\n".join(f"          {b}" for b in proof_bits)
            + "\n        </ul>"
        )

    chip = " · ".join(
        x for x in (str(person.get("headline") or "").strip(), location) if x
    )
    chip_html = f'<p class="portrait-chip">{esc(chip)}</p>' if chip else ""

    photo_html = ""
    if photo:
        src = esc(with_base(site, str(photo)))
        alt = esc(person.get("photo_alt") or person.get("full_name") or "Profile photo")
        photo_html = f"""
      <div class="hero-visual">
        <img class="hero-photo" src="{src}" alt="{alt}" width="720" height="935" decoding="async" fetchpriority="high" />
        {chip_html}
      </div>"""

    card = esc(site.get("external", {}).get("bitly_hub") or "#")
    contact = site["contact"]
    ext = site["external"]
    contact_href = esc(with_base(site, "/#contact"))
    contact_section = f"""
    <section id="contact" class="contact-section">
      <h2>Contact</h2>
      <p class="page-lede">{esc(contact.get("note", ""))}</p>
      <ul class="item-list">
        <li>
          <h3>Email</h3>
          <p><a href="mailto:{esc(contact["email"])}">{esc(contact["email"])}</a></p>
        </li>
        <li>
          <h3>Phone</h3>
          <p><a href="tel:{esc(contact["phone"].replace(" ", ""))}">{esc(contact["phone"])}</a></p>
        </li>
        <li>
          <h3>Elsewhere</h3>
          <p class="links">
            <a class="external" href="{esc(ext["linkedin"])}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
            <a class="external" href="{esc(ext["medium"])}" target="_blank" rel="noopener noreferrer">Medium</a>
            <a class="external" href="{esc(ext["github"])}" target="_blank" rel="noopener noreferrer">GitHub</a>
            <a class="external" href="{esc(ext["blog"])}" target="_blank" rel="noopener noreferrer">Blog (WordPress)</a>
          </p>
        </li>
      </ul>
    </section>
"""
    return f"""    <section class="hero">
      <div class="hero-copy">
        <h1>{esc(person['full_name'])}</h1>
        <p class="subtitle">{esc(person['headline'])}</p>
        <p class="lede">{esc(person['tagline'])}</p>
{outcome_html}
{proof_html}
        <div class="cta-row">
          <a class="btn btn-primary" href="{contact_href}">Contact</a>
          <a class="btn" href="{card}" target="_blank" rel="noopener noreferrer">Digital card</a>
          <a class="btn" href="{esc(with_base(site, '/about/'))}">About</a>
          <a class="btn" href="{esc(with_base(site, '/portfolio/'))}">Portfolio</a>
        </div>
      </div>{photo_html}
    </section>
{contact_section}
"""


def build_about(site: dict, export: dict) -> str:
    about = export.get("about") if isinstance(export.get("about"), dict) else None
    if not about:
        about = site.get("about") or {}

    lede = about.get("lede") or (site.get("about") or {}).get("lede") or ""
    philosophy = (about.get("philosophy") or "").strip()
    competencies = about.get("competencies") or []
    highlights = about.get("career_highlights") or []
    journey = about.get("career_journey") or {}

    comp_html = []
    for row in competencies:
        if not isinstance(row, dict):
            continue
        comp_html.append(
            f"      <li><strong>{esc(row.get('title') or '')}</strong> — "
            f"{esc((row.get('body') or '').strip())}</li>"
        )
    if not comp_html:
        for b in (site.get("about") or {}).get("bullets") or []:
            comp_html.append(f"      <li>{esc(b)}</li>")

    highlight_html = []
    for row in highlights:
        if not isinstance(row, dict):
            continue
        link = row.get("link") or ""
        link_html = ""
        if link:
            href = with_base(site, link) if str(link).startswith("/") else link
            label = esc(row.get("link_label") or "Learn more")
            link_html = (
                f'<p class="links"><a href="{esc(href)}"'
                + (
                    ' target="_blank" rel="noopener noreferrer"'
                    if not str(link).startswith("/")
                    else ""
                )
                + f">{label}</a></p>"
            )
        highlight_html.append(
            f"      <li>\n"
            f"        <h3>{esc(row.get('title') or '')}</h3>\n"
            f"        <p>{esc((row.get('body') or '').strip())}</p>\n"
            f"        {link_html}\n"
            f"      </li>"
        )

    journey_inner = ""
    if isinstance(journey, dict) and (journey.get("embed") or journey.get("link")):
        title = journey.get("title") or "Career Journey"
        link = journey.get("link") or ""
        embed = journey.get("embed") or ""
        link_label = journey.get("link_label") or "Open deck"
        link_bit = ""
        if link:
            link_bit = (
                f'<p class="links"><a class="figma-open" href="{esc(link)}" target="_blank" '
                f'rel="noopener noreferrer">{esc(link_label)}</a></p>'
            )
        embed_bit = ""
        if embed:
            embed_bit = figma_embed_html(
                str(title), str(embed), str(link) if link else None, link_label=str(link_label), tall=True
            )
        journey_inner = f"{link_bit}\n{embed_bit}"

    philosophy_inner = ""
    if philosophy:
        philosophy_inner = f"""
      <blockquote class="philosophy">
        <p>{esc(philosophy)}</p>
      </blockquote>
"""

    creds = esc(with_base(site, "/credentials/"))
    ext = site.get("external") or {}
    writing_rows = []
    for row in site.get("writing_highlights") or []:
        if not isinstance(row, dict):
            continue
        title = (row.get("title") or "").strip()
        url = (row.get("url") or "").strip()
        if not title or not url:
            continue
        venue = esc(row.get("venue") or "Article")
        date = esc(row.get("date") or "")
        meta = " · ".join(x for x in (venue, date) if x)
        writing_rows.append(
            f"      <li>\n"
            f'        <h3><a class="external" href="{esc(url)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(title)}</a></h3>\n'
            f'        <p class="meta">{meta}</p>\n'
            f"      </li>"
        )

    toc: list[dict] = [
        {"id": "core-competencies", "label": "Core Competencies", "children": []},
        {"id": "career-highlights", "label": "Career Highlights", "children": []},
    ]
    parts: list[str] = [
        section_fold_open("core-competencies", "Core Competencies", level="h2"),
        '      <ul class="competency-list">\n'
        + (chr(10).join(comp_html) if comp_html else "      <li>No competencies listed.</li>")
        + "\n      </ul>",
        section_fold_close(),
        section_fold_open("career-highlights", "Career Highlights", level="h2"),
        '      <ul class="item-list highlight-list">\n'
        + (
            chr(10).join(highlight_html)
            if highlight_html
            else "      <li>No highlights listed.</li>"
        )
        + "\n      </ul>",
        f'      <p class="links"><a href="{creds}">View full credentials list</a></p>',
        section_fold_close(),
    ]
    if writing_rows:
        toc.append({"id": "selected-writing", "label": "Selected writing", "children": []})
        parts.extend(
            [
                section_fold_open("selected-writing", "Selected writing", level="h2"),
                '      <p class="page-lede">Thought leadership lives on Blog, Medium, and LinkedIn '
                "until the writing corpus is unified (C2b). Selected pieces:</p>",
                '      <ul class="item-list writing-list">\n'
                + chr(10).join(writing_rows)
                + "\n      </ul>",
                '      <p class="links">\n'
                f'        <a class="external" href="{esc(ext.get("blog") or "")}" target="_blank" '
                'rel="noopener noreferrer">Blog</a>\n'
                f'        <a class="external" href="{esc(ext.get("medium") or "")}" target="_blank" '
                'rel="noopener noreferrer">Medium</a>\n'
                f'        <a class="external" href="{esc(ext.get("linkedin") or "")}" target="_blank" '
                'rel="noopener noreferrer">LinkedIn</a>\n'
                "      </p>",
                section_fold_close(),
            ]
        )
    if journey_inner:
        toc.append({"id": "career-journey", "label": "Career Journey", "children": []})
        parts.extend(
            [
                section_fold_open("career-journey", "Career Journey", level="h2"),
                journey_inner,
                section_fold_close(),
            ]
        )
    if philosophy_inner:
        toc.append({"id": "philosophy", "label": "Philosophy", "children": []})
        parts.extend(
            [
                section_fold_open("philosophy", "Philosophy", level="h2"),
                philosophy_inner,
                section_fold_close(),
            ]
        )

    body = "\n".join(parts)
    lede_html = f'<p class="page-lede">{esc(lede.strip())}</p>'
    return longform_page(
        title="About",
        lede_html=lede_html,
        toc=toc,
        body=body,
        search=False,
    )


def _link_label(url: str) -> str:
    u = url.lower()
    if "github.com" in u:
        return "GitHub"
    if "medium.com" in u or "towardsdatascience.com" in u:
        return "Article"
    if "figma.com" in u:
        return "Figma deck"
    if "yzouyang.com" in u:
        return "Article archive"
    if "bit.ly" in u:
        return url
    return "Link"


def _project_item_html(row: dict) -> str:
    name = esc(row.get("name") or row.get("id") or "Project")
    # Outcome → scope → tools. Export may only have description (outcome stand-in).
    outcome = str(row.get("outcome") or row.get("impact") or row.get("description") or "").strip()
    scope = str(row.get("scope") or row.get("context") or "").strip()
    if scope and scope == outcome:
        scope = ""
    start = esc(row.get("start") or "")
    end = esc(row.get("end") or "present")
    tools = row.get("tools") or []
    tools_html = ""
    if tools:
        tools_html = (
            f'<p class="case-tools meta">Tools: '
            f'{esc(", ".join(str(t) for t in tools))}</p>'
        )
    outcome_html = f'<p class="case-outcome">{esc(outcome)}</p>' if outcome else ""
    scope_html = f"<p>{esc(scope)}</p>" if scope else ""
    links = urls_from_bullets(row.get("bullets"))
    link_html = ""
    if links:
        link_html = (
            '<p class="links">'
            + " · ".join(
                f'<a class="external" href="{esc(u)}" target="_blank" rel="noopener noreferrer">'
                f"{esc(_link_label(u))}</a>"
                for u in links
            )
            + "</p>"
        )
    embed = row.get("embed") or ""
    embed_html = ""
    if embed:
        figma_link = next((u for u in links if "figma.com" in u.lower()), None)
        embed_html = figma_embed_html(str(row.get("name") or "Deck"), str(embed), figma_link)
    return (
        f"      <li>\n"
        f"        <h3>{name}</h3>\n"
        f'        <p class="meta">{start} – {end}</p>\n'
        f"        {outcome_html}\n"
        f"        {scope_html}\n"
        f"        {tools_html}\n"
        f"        {link_html}\n"
        f"        {embed_html}\n"
        f"      </li>"
    )


def build_portfolio(site: dict, export: dict) -> str:
    short = esc(site["external"].get("portfolio_short", ""))
    page = export.get("portfolio") if isinstance(export.get("portfolio"), dict) else {}
    lede = (page.get("lede") or "Selected PUBLIC projects.").strip()
    projects = [p for p in (export.get("projects") or []) if isinstance(p, dict)]
    by_section: dict[str, list] = {}
    for p in projects:
        by_section.setdefault(str(p.get("section") or "other"), []).append(p)

    sections_html: list[str] = []
    toc: list[dict] = []
    seen_parents: set[str] = set()
    parent_nodes: dict[str, dict] = {}
    used_ids: set[str] = set()
    fold_open = False

    def unique_id(label: str) -> str:
        base = slugify(label)
        eid = base
        n = 2
        while eid in used_ids:
            eid = f"{base}-{n}"
            n += 1
        used_ids.add(eid)
        return eid

    def close_fold() -> None:
        nonlocal fold_open
        if fold_open:
            sections_html.append(section_fold_close())
            fold_open = False

    for section in page.get("sections") or []:
        if not isinstance(section, dict):
            continue
        sid = str(section.get("id") or "")
        rows = by_section.pop(sid, [])
        if not rows and sid != "other":
            continue
        parent = section.get("parent")
        title = str(section.get("title") or sid)
        hid = unique_id(title)
        child_node = {"id": hid, "label": title, "children": []}

        if parent:
            parent_key = str(parent)
            if parent_key not in seen_parents:
                close_fold()
                pid = unique_id(parent_key)
                parent_node = {"id": pid, "label": parent_key, "children": []}
                toc.append(parent_node)
                parent_nodes[parent_key] = parent_node
                sections_html.append(section_fold_open(pid, esc(parent_key), level="h2"))
                fold_open = True
                seen_parents.add(parent_key)
            parent_nodes[parent_key]["children"].append(child_node)
            sections_html.append(f'      <h3 id="{hid}">{esc(title)}</h3>')
        else:
            close_fold()
            toc.append(child_node)
            sections_html.append(section_fold_open(hid, esc(title), level="h2"))
            fold_open = True

        intro = (section.get("intro") or "").strip()
        if intro:
            sections_html.append(f'      <p class="page-lede">{esc(intro)}</p>')
        sections_html.append(
            '      <ul class="item-list">\n'
            + "\n".join(_project_item_html(r) for r in rows)
            + "\n      </ul>"
        )
        footer_link = section.get("footer_link") or ""
        if footer_link:
            sections_html.append(
                f'      <p class="links"><a class="external" href="{esc(footer_link)}" target="_blank" '
                f'rel="noopener noreferrer">{esc(section.get("footer_label") or footer_link)}</a></p>'
            )
        outro = (section.get("outro") or "").strip()
        if outro:
            sections_html.append(f"      <p><em>{esc(outro)}</em></p>")
        if not parent:
            close_fold()

    for sid, rows in by_section.items():
        if not rows:
            continue
        close_fold()
        title = sid.replace("_", " ").title()
        hid = unique_id(title)
        toc.append({"id": hid, "label": title, "children": []})
        sections_html.append(section_fold_open(hid, esc(title), level="h2"))
        fold_open = True
        sections_html.append(
            '      <ul class="item-list">\n'
            + "\n".join(_project_item_html(r) for r in rows)
            + "\n      </ul>"
        )
        close_fold()

    enterprise = page.get("enterprise_summaries") or {}
    if isinstance(enterprise, dict) and enterprise.get("items"):
        close_fold()
        etitle = str(enterprise.get("title") or "Enterprise summaries")
        eid = unique_id(etitle)
        ent_node = {"id": eid, "label": etitle, "children": []}
        toc.append(ent_node)
        sections_html.append(section_fold_open(eid, esc(etitle), level="h2"))
        fold_open = True
        for item in enterprise.get("items") or []:
            if not isinstance(item, dict):
                continue
            item_title = str(item.get("title") or "")
            item_id = unique_id(item_title) if item_title else ""
            if item_id:
                ent_node["children"].append(
                    {"id": item_id, "label": item_title, "children": []}
                )
            bullets = "\n".join(
                f"        <li>{esc(b)}</li>" for b in (item.get("bullets") or [])
            )
            id_attr = f' id="{item_id}"' if item_id else ""
            sections_html.append(
                f"      <h3{id_attr}>{esc(item_title)}</h3>\n"
                f'      <ul class="competency-list">\n{bullets}\n      </ul>'
            )
        close_fold()

    verify = page.get("verify") or {}
    if isinstance(verify, dict) and verify.get("items"):
        close_fold()
        vtitle = str(verify.get("title") or "Verify")
        vid = unique_id(vtitle)
        toc.append({"id": vid, "label": vtitle, "children": []})
        sections_html.append(section_fold_open(vid, esc(vtitle), level="h2"))
        fold_open = True
        vitems = []
        for item in verify.get("items") or []:
            if not isinstance(item, dict):
                continue
            href = item.get("href") or "#"
            if str(href).startswith("/"):
                href = with_base(site, href)
            external = not str(item.get("href") or "").startswith("/")
            attrs = f' href="{esc(href)}"'
            cls = ' class="external"' if external else ""
            if external:
                attrs += ' target="_blank" rel="noopener noreferrer"'
            vitems.append(
                f"      <li><a{cls}{attrs}>{esc(item.get('label') or href)}</a></li>"
            )
        sections_html.append(
            '      <ul class="competency-list">\n' + "\n".join(vitems) + "\n      </ul>"
        )
        note = (verify.get("note") or "").strip()
        if note:
            sections_html.append(f"      <p><em>{esc(note)}</em></p>")
        close_fold()

    close_fold()
    body = "\n".join(sections_html) if sections_html else "    <p>No PUBLIC projects in export.</p>"
    lede_html = (
        f'<p class="page-lede">{esc(lede)} Short link: '
        f'<a href="{short}" target="_blank" rel="noopener noreferrer">{short}</a></p>'
    )
    return longform_page(title="Portfolio", lede_html=lede_html, toc=toc, body=body)


def _cert_item_html(row: dict) -> str:
    name = esc(row.get("name") or "")
    issuer = esc(row.get("issuer") or "")
    issued = esc(row.get("issued") or "")
    expires = esc(row.get("expires") or "")
    primary, bitly = primary_and_short(urls_from_bullets(row.get("bullets")))
    links = []
    if primary:
        links.append(
            f'<a href="{esc(primary)}" target="_blank" rel="noopener noreferrer">Verify</a>'
        )
    if bitly:
        links.append(
            f'<a href="{esc(bitly)}" target="_blank" rel="noopener noreferrer">{esc(bitly)}</a>'
        )
    link_html = f'<p class="links">{" · ".join(links)}</p>' if links else ""
    validity = f"issued {issued}" if issued else ""
    if expires:
        validity += f" · expires {expires}" if validity else f"expires {expires}"
    return (
        f"      <li>\n"
        f"        <h3>{name}</h3>\n"
        f'        <p class="meta">{issuer}'
        + (f" · {validity}" if validity else "")
        + "</p>\n"
        f"        {link_html}\n"
        f"      </li>"
    )


def _edu_item_html(row: dict) -> str:
    cred = esc(row.get("credential") or "")
    inst = esc(row.get("institution") or "")
    start = esc(row.get("start") or "")
    end = esc(row.get("end") or "")
    period = " – ".join(x for x in (start, end or "present") if x)
    links = urls_from_bullets(row.get("bullets"))
    link_html = ""
    if links:
        link_html = (
            '<p class="links">'
            + " · ".join(
                f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(_link_label(u))}</a>'
                for u in links
            )
            + "</p>"
        )
    return (
        f"      <li>\n"
        f"        <h3>{cred}</h3>\n"
        f'        <p class="meta">{inst}'
        + (f" · {period}" if period else "")
        + "</p>\n"
        f"        {link_html}\n"
        f"      </li>"
    )


def _certs_by_issuer_html(
    rows: list[dict], unique_id
) -> tuple[list[str], list[dict]]:
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        issuer = str(row.get("issuer") or "Other").strip() or "Other"
        grouped.setdefault(issuer, []).append(row)
    out: list[str] = []
    children: list[dict] = []
    for issuer, group in grouped.items():
        iid = unique_id(issuer)
        children.append({"id": iid, "label": issuer, "children": []})
        out.append(f'      <h3 class="issuer-group" id="{iid}">{esc(issuer)}</h3>')
        out.append(
            '      <ul class="item-list">\n'
            + "\n".join(_cert_item_html(r) for r in group)
            + "\n      </ul>"
        )
    return out, children


def build_credentials(site: dict, export: dict) -> str:
    short = esc(site["external"].get("credentials_short", ""))
    page = export.get("credentials") if isinstance(export.get("credentials"), dict) else {}
    lede = (page.get("lede") or "PUBLIC certifications and qualifications.").strip()
    order = page.get("order") or {}
    certs = [c for c in (export.get("certifications") or []) if isinstance(c, dict)]
    education = [e for e in (export.get("education") or []) if isinstance(e, dict)]

    certs_by_cat: dict[str, list] = {}
    for c in certs:
        certs_by_cat.setdefault(str(c.get("category") or "professional"), []).append(c)

    edu_by_cat: dict[str, list] = {}
    for e in education:
        edu_by_cat.setdefault(str(e.get("category") or "academic"), []).append(e)

    def ordered(rows: list, ids: list | None, id_key: str = "id") -> list:
        if not ids:
            return rows
        index = {str(r.get(id_key)): r for r in rows}
        out = [index[i] for i in ids if i in index]
        seen = set(ids)
        out.extend(r for r in rows if str(r.get(id_key)) not in seen)
        return out

    blocks: list[str] = []
    toc: list[dict] = []
    used_ids: set[str] = set()

    def unique_id(label: str) -> str:
        base = slugify(label)
        eid = base
        n = 2
        while eid in used_ids:
            eid = f"{base}-{n}"
            n += 1
        used_ids.add(eid)
        return eid

    for section in page.get("sections") or [
        {"id": "professional", "title": "Professional Certifications"},
        {"id": "leadership", "title": "Leadership & Professional Programs"},
        {"id": "academic", "title": "Academic Qualifications"},
        {"id": "training", "title": "Additional Training & Bootcamps"},
    ]:
        if not isinstance(section, dict):
            continue
        sid = str(section.get("id") or "")
        title = str(section.get("title") or sid)
        if sid in ("academic", "training"):
            rows = ordered(edu_by_cat.pop(sid, []), order.get(sid))
            if not rows:
                continue
            hid = unique_id(title)
            toc.append({"id": hid, "label": title, "children": []})
            blocks.append(section_fold_open(hid, esc(title), level="h2"))
            blocks.append(
                '      <ul class="item-list">\n'
                + "\n".join(_edu_item_html(r) for r in rows)
                + "\n      </ul>"
            )
            blocks.append(section_fold_close())
        else:
            rows = ordered(certs_by_cat.pop(sid, []), order.get(sid))
            if not rows:
                continue
            hid = unique_id(title)
            node = {"id": hid, "label": title, "children": []}
            toc.append(node)
            blocks.append(section_fold_open(hid, esc(title), level="h2"))
            if sid == "professional":
                html_parts, children = _certs_by_issuer_html(rows, unique_id)
                node["children"] = children
                blocks.extend(html_parts)
            else:
                blocks.append(
                    '      <ul class="item-list">\n'
                    + "\n".join(_cert_item_html(r) for r in rows)
                    + "\n      </ul>"
                )
            blocks.append(section_fold_close())

    for sid, rows in list(certs_by_cat.items()):
        if rows:
            title = sid.replace("_", " ").title()
            hid = unique_id(title)
            toc.append({"id": hid, "label": title, "children": []})
            blocks.append(section_fold_open(hid, esc(title), level="h2"))
            blocks.append(
                '      <ul class="item-list">\n'
                + "\n".join(_cert_item_html(r) for r in rows)
                + "\n      </ul>"
            )
            blocks.append(section_fold_close())
    for sid, rows in list(edu_by_cat.items()):
        if rows:
            title = sid.replace("_", " ").title()
            hid = unique_id(title)
            toc.append({"id": hid, "label": title, "children": []})
            blocks.append(section_fold_open(hid, esc(title), level="h2"))
            blocks.append(
                '      <ul class="item-list">\n'
                + "\n".join(_edu_item_html(r) for r in rows)
                + "\n      </ul>"
            )
            blocks.append(section_fold_close())

    notes = page.get("notes") or []
    if notes:
        hid = unique_id("Notes")
        toc.append({"id": hid, "label": "Notes", "children": []})
        blocks.append(section_fold_open(hid, "Notes", level="h2"))
        blocks.append(
            '      <ul class="competency-list">\n'
            + "\n".join(f"      <li>{esc(n)}</li>" for n in notes)
            + "\n      </ul>"
        )
        blocks.append(section_fold_close())

    body = "\n".join(blocks) if blocks else "    <p>No PUBLIC credentials in export.</p>"
    lede_html = (
        f'<p class="page-lede">{esc(lede)} Short link: '
        f'<a href="{short}" target="_blank" rel="noopener noreferrer">{short}</a></p>'
    )
    return longform_page(
        title="Credentials &amp; Verifications",
        lede_html=lede_html,
        toc=toc,
        body=body,
    )


def build_contact_redirect(site: dict) -> str:
    """Standalone redirect for /contact/ → Home#contact (bookmark / WP parity)."""
    target = with_base(site, "/#contact")
    brand = esc((site.get("person") or {}).get("brand", "yzouyang"))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Contact — {brand}</title>
  <meta http-equiv="refresh" content="0;url={esc(target)}" />
  <link rel="canonical" href="{esc(target)}" />
</head>
<body>
  <p>Contact details are on the <a href="{esc(target)}">home page</a>.</p>
</body>
</html>
"""


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-path",
        default=None,
        help="Site root prefix for GitHub project Pages (e.g. /yzouyang-site). "
        "Overrides site.json and SITE_BASE_PATH.",
    )
    parser.add_argument(
        "--skip-pagefind",
        action="store_true",
        help="Skip Pagefind indexing (search UI will be incomplete).",
    )
    args = parser.parse_args()

    site = load_json(DATA / "site.json")
    if args.base_path is not None:
        site["base_path"] = args.base_path
    elif os.environ.get("SITE_BASE_PATH") is not None:
        site["base_path"] = os.environ["SITE_BASE_PATH"]
    site["base_path"] = normalize_base(site.get("base_path", ""))

    export = load_json(DATA / "export_public.json")
    if DIST.exists():
        # On Windows, a running preview server may lock the dist directory itself.
        for child in DIST.iterdir():
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                try:
                    child.unlink()
                except OSError:
                    pass
    DIST.mkdir(parents=True, exist_ok=True)

    pages = [
        ("index.html", "Home", "Home", build_home(site, export), False),
        ("about/index.html", "About", "About", build_about(site, export), False),
        ("portfolio/index.html", "Portfolio", "Portfolio", build_portfolio(site, export), True),
        (
            "credentials/index.html",
            "Credentials",
            "Credentials",
            build_credentials(site, export),
            True,
        ),
    ]
    for rel, title, active, body, pf in pages:
        write(DIST / rel, layout(site, title, active, body, pagefind=pf))

    write(DIST / "contact" / "index.html", build_contact_redirect(site))

    write(DIST / "styles.css", assemble_styles())
    assets_src = ROOT / "assets"
    if assets_src.is_dir():
        shutil.copytree(assets_src, DIST / "assets", dirs_exist_ok=True)
    diy = (site.get("analytics") or {}).get("diy") or {}
    if diy.get("enabled") and (SRC / "track.js").is_file():
        shutil.copyfile(SRC / "track.js", DIST / "track.js")
    (DIST / "data").mkdir(exist_ok=True)
    shutil.copyfile(DATA / "export_public.json", DIST / "data" / "export_public.json")
    site_out = dict(site)
    write(DIST / "data" / "site.json", json.dumps(site_out, indent=2) + "\n")

    base = site["base_path"]
    redirects = f"""{base}/about {base}/about/ 301
{base}/portfolio {base}/portfolio/ 301
{base}/credentials {base}/credentials/ 301
{base}/contact {base}/ 302
{base}/contact/ {base}/ 302
"""
    write(DIST / "_redirects", redirects)

    print(f"built {len(pages)} pages + contact redirect -> {DIST} (base_path={base or '/'})")

    if not args.skip_pagefind:
        run_pagefind()


if __name__ == "__main__":
    main()
