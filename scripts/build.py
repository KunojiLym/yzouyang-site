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


def toc_html(entries: list[tuple[str, str]]) -> str:
    if not entries:
        return ""
    items = "\n".join(
        f'      <li><a href="#{esc(eid)}">{esc(label)}</a></li>' for eid, label in entries
    )
    return (
        '    <nav class="page-toc" aria-label="On this page">\n'
        "    <ul>\n"
        f"{items}\n"
        "    </ul>\n"
        "    </nav>\n"
    )


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
  <link rel="stylesheet" href="{css}" />
  <link rel="stylesheet" href="{pf_css}" />
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
  <main class="page"{pf_attr}>
{body}
  </main>
{footer_html(site)}
  <script src="{pf_js}" type="text/javascript"></script>
  <script>
    window.addEventListener("DOMContentLoaded", () => {{
      const mount = document.querySelector("#search");
      if (mount && window.PagefindUI) {{
        new PagefindUI({{ element: "#search", showSubResults: true }});
      }}
    }});
  </script>
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
    platforms = [str(p) for p in (person.get("platforms") or []) if str(p).strip()]
    certs = [c for c in (export.get("certifications") or []) if isinstance(c, dict)]
    pro_certs = [c for c in certs if str(c.get("category") or "professional") == "professional"]
    cert_count = len(pro_certs) if pro_certs else len(certs)

    proof_bits: list[str] = []
    if location:
        proof_bits.append(f"<li><strong>{esc(location)}</strong></li>")
    if cert_count:
        proof_bits.append(
            f"<li><strong>{cert_count}</strong> professional credentials</li>"
        )
    for p in platforms:
        proof_bits.append(f"<li>{esc(p)}</li>")
    proof_html = ""
    if proof_bits:
        proof_html = (
            '        <ul class="proof-strip" aria-label="Highlights">\n'
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

    journey_html = ""
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
        journey_html = f"""
    <h2 id="career-journey">Career Journey</h2>
    {link_bit}
    {embed_bit}
"""

    philosophy_html = ""
    if philosophy:
        philosophy_html = f"""
    <h2>Philosophy</h2>
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
    writing_html = ""
    if writing_rows:
        writing_html = f"""
    <h2 id="selected-writing">Selected writing</h2>
    <p class="page-lede">Thought leadership lives on Blog, Medium, and LinkedIn until the writing corpus is unified (C2b). Selected pieces:</p>
    <ul class="item-list writing-list">
{chr(10).join(writing_rows)}
    </ul>
    <p class="links">
      <a class="external" href="{esc(ext.get("blog") or "")}" target="_blank" rel="noopener noreferrer">Blog</a>
      <a class="external" href="{esc(ext.get("medium") or "")}" target="_blank" rel="noopener noreferrer">Medium</a>
      <a class="external" href="{esc(ext.get("linkedin") or "")}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
    </p>
"""

    return f"""    <h1>About</h1>
    <p class="page-lede">{esc(lede.strip())}</p>
    <h2>Core Competencies</h2>
    <ul class="competency-list">
{chr(10).join(comp_html) if comp_html else "      <li>No competencies listed.</li>"}
    </ul>
    <h2>Career Highlights</h2>
    <ul class="item-list highlight-list">
{chr(10).join(highlight_html) if highlight_html else "      <li>No highlights listed.</li>"}
    </ul>
    <p class="links"><a href="{creds}">View full credentials list</a></p>
{writing_html}{journey_html}{philosophy_html}
"""


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
    desc = esc((row.get("description") or "").strip())
    start = esc(row.get("start") or "")
    end = esc(row.get("end") or "present")
    tools = row.get("tools") or []
    tools_html = ""
    if tools:
        tools_html = f'<p class="meta">Tools: {esc(", ".join(str(t) for t in tools))}</p>'
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
    embed = row.get("embed") or ""
    embed_html = ""
    if embed:
        figma_link = next((u for u in links if "figma.com" in u.lower()), None)
        embed_html = figma_embed_html(str(row.get("name") or "Deck"), str(embed), figma_link)
    return (
        f"      <li>\n"
        f"        <h3>{name}</h3>\n"
        f'        <p class="meta">{start} – {end}</p>\n'
        f"        <p>{desc}</p>\n"
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
    toc: list[tuple[str, str]] = []
    seen_parents: set[str] = set()
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

    for section in page.get("sections") or []:
        if not isinstance(section, dict):
            continue
        sid = str(section.get("id") or "")
        rows = by_section.pop(sid, [])
        if not rows and sid != "other":
            continue
        parent = section.get("parent")
        if parent and parent not in seen_parents:
            pid = unique_id(str(parent))
            toc.append((pid, str(parent)))
            sections_html.append(f'    <h2 id="{pid}">{esc(parent)}</h2>')
            seen_parents.add(str(parent))
        title = str(section.get("title") or sid)
        hid = unique_id(title)
        toc.append((hid, title))
        sections_html.append(f'    <h3 id="{hid}">{esc(title)}</h3>')
        intro = (section.get("intro") or "").strip()
        if intro:
            sections_html.append(f'    <p class="page-lede">{esc(intro)}</p>')
        sections_html.append(
            '    <ul class="item-list">\n'
            + "\n".join(_project_item_html(r) for r in rows)
            + "\n    </ul>"
        )
        footer_link = section.get("footer_link") or ""
        if footer_link:
            sections_html.append(
                f'    <p class="links"><a href="{esc(footer_link)}" target="_blank" '
                f'rel="noopener noreferrer">{esc(section.get("footer_label") or footer_link)}</a></p>'
            )
        outro = (section.get("outro") or "").strip()
        if outro:
            sections_html.append(f"    <p><em>{esc(outro)}</em></p>")

    for sid, rows in by_section.items():
        if not rows:
            continue
        title = sid.replace("_", " ").title()
        hid = unique_id(title)
        toc.append((hid, title))
        sections_html.append(f'    <h3 id="{hid}">{esc(title)}</h3>')
        sections_html.append(
            '    <ul class="item-list">\n'
            + "\n".join(_project_item_html(r) for r in rows)
            + "\n    </ul>"
        )

    enterprise = page.get("enterprise_summaries") or {}
    if isinstance(enterprise, dict) and enterprise.get("items"):
        etitle = str(enterprise.get("title") or "Enterprise summaries")
        eid = unique_id(etitle)
        toc.append((eid, etitle))
        sections_html.append(f'    <h2 id="{eid}">{esc(etitle)}</h2>')
        for item in enterprise.get("items") or []:
            if not isinstance(item, dict):
                continue
            bullets = "\n".join(
                f"        <li>{esc(b)}</li>" for b in (item.get("bullets") or [])
            )
            sections_html.append(
                f"    <h3>{esc(item.get('title') or '')}</h3>\n"
                f'    <ul class="competency-list">\n{bullets}\n    </ul>'
            )

    verify = page.get("verify") or {}
    if isinstance(verify, dict) and verify.get("items"):
        vtitle = str(verify.get("title") or "Verify")
        vid = unique_id(vtitle)
        toc.append((vid, vtitle))
        sections_html.append(f'    <h2 id="{vid}">{esc(vtitle)}</h2>')
        vitems = []
        for item in verify.get("items") or []:
            if not isinstance(item, dict):
                continue
            href = item.get("href") or "#"
            if str(href).startswith("/"):
                href = with_base(site, href)
            external = not str(item.get("href") or "").startswith("/")
            attrs = f' href="{esc(href)}"'
            if external:
                attrs += ' target="_blank" rel="noopener noreferrer"'
            vitems.append(f"      <li><a{attrs}>{esc(item.get('label') or href)}</a></li>")
        sections_html.append(
            '    <ul class="competency-list">\n' + "\n".join(vitems) + "\n    </ul>"
        )
        note = (verify.get("note") or "").strip()
        if note:
            sections_html.append(f"    <p><em>{esc(note)}</em></p>")

    body = "\n".join(sections_html) if sections_html else "    <p>No PUBLIC projects in export.</p>"
    return f"""    <h1>Portfolio</h1>
    <p class="page-lede">{esc(lede)} Short link: <a href="{short}" target="_blank" rel="noopener noreferrer">{short}</a></p>
{toc_html(toc)}    <div id="search"></div>
{body}
"""


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


def _certs_by_issuer_html(rows: list[dict]) -> list[str]:
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        issuer = str(row.get("issuer") or "Other").strip() or "Other"
        grouped.setdefault(issuer, []).append(row)
    out: list[str] = []
    for issuer, group in grouped.items():
        out.append(f'    <h3 class="issuer-group">{esc(issuer)}</h3>')
        out.append(
            '    <ul class="item-list">\n'
            + "\n".join(_cert_item_html(r) for r in group)
            + "\n    </ul>"
        )
    return out


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
    toc: list[tuple[str, str]] = []
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
            toc.append((hid, title))
            blocks.append(f'    <h2 id="{hid}">{esc(title)}</h2>')
            blocks.append(
                '    <ul class="item-list">\n'
                + "\n".join(_edu_item_html(r) for r in rows)
                + "\n    </ul>"
            )
        else:
            rows = ordered(certs_by_cat.pop(sid, []), order.get(sid))
            if not rows:
                continue
            hid = unique_id(title)
            toc.append((hid, title))
            blocks.append(f'    <h2 id="{hid}">{esc(title)}</h2>')
            if sid == "professional":
                blocks.extend(_certs_by_issuer_html(rows))
            else:
                blocks.append(
                    '    <ul class="item-list">\n'
                    + "\n".join(_cert_item_html(r) for r in rows)
                    + "\n    </ul>"
                )

    for sid, rows in list(certs_by_cat.items()):
        if rows:
            title = sid.replace("_", " ").title()
            hid = unique_id(title)
            toc.append((hid, title))
            blocks.append(f'    <h2 id="{hid}">{esc(title)}</h2>')
            blocks.append(
                '    <ul class="item-list">\n'
                + "\n".join(_cert_item_html(r) for r in rows)
                + "\n    </ul>"
            )
    for sid, rows in list(edu_by_cat.items()):
        if rows:
            title = sid.replace("_", " ").title()
            hid = unique_id(title)
            toc.append((hid, title))
            blocks.append(f'    <h2 id="{hid}">{esc(title)}</h2>')
            blocks.append(
                '    <ul class="item-list">\n'
                + "\n".join(_edu_item_html(r) for r in rows)
                + "\n    </ul>"
            )

    notes = page.get("notes") or []
    if notes:
        hid = unique_id("Notes")
        toc.append((hid, "Notes"))
        blocks.append(f'    <h2 id="{hid}">Notes</h2>')
        blocks.append(
            '    <ul class="competency-list">\n'
            + "\n".join(f"      <li>{esc(n)}</li>" for n in notes)
            + "\n    </ul>"
        )

    body = "\n".join(blocks) if blocks else "    <p>No PUBLIC credentials in export.</p>"
    return f"""    <h1>Credentials &amp; Verifications</h1>
    <p class="page-lede">{esc(lede)} Short link: <a href="{short}" target="_blank" rel="noopener noreferrer">{short}</a></p>
{toc_html(toc)}    <div id="search"></div>
{body}
"""


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

    shutil.copyfile(SRC / "styles.css", DIST / "styles.css")
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
