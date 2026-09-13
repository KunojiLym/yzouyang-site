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

import yaml  # PyYAML — declared in pyproject.toml; run `uv sync` first.

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


def _merge_preview_drafts(export: dict) -> dict:
    """Operator-only: include PRIVATE_ONLY writing rows when previewing drafts."""
    pc_root = os.environ.get("PREVIEW_INCLUDE_DRAFTS")
    if not pc_root:
        return export
    data_dir = Path(pc_root) / "people" / "yingzhao" / "data"
    yaml_path = data_dir / "writing.yaml"
    if not yaml_path.is_file():
        return export
    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    rows = list(export.get("writing") or [])
    existing = {str(r.get("id")) for r in rows if isinstance(r, dict)}
    for raw in doc.get("writing") or []:
        if not isinstance(raw, dict):
            continue
        if str(raw.get("visibility_policy") or "").upper() != "PRIVATE_ONLY":
            continue
        row = {k: v for k, v in raw.items() if k != "visibility_policy"}
        row["preview_draft"] = True
        body_file = raw.get("body_file")
        if isinstance(body_file, str) and body_file.strip():
            path = data_dir / body_file.strip()
            if path.is_file():
                row["body_md"] = path.read_text(encoding="utf-8")
        note_id = str(row.get("id") or "")
        if note_id and note_id not in existing:
            rows.append(row)
            existing.add(note_id)
    merged = dict(export)
    merged["writing"] = rows
    return merged


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


MAX_CASE_TOOLS = 5
CASE_BEAT_KEYS = (
    ("problem", "Problem"),
    ("role", "Role"),
    ("decision", "Decision"),
    ("outcome", "Outcome"),
    ("evidence", "Evidence"),
)
THEME_BOOT_SCRIPT = """<script>
(function () {
  var KEY = "yz-theme";
  var theme = "dark";
  try {
    var stored = localStorage.getItem(KEY);
    if (stored === "light" || stored === "dark") {
      theme = stored;
    } else if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) {
      theme = "light";
    }
  } catch (e) {}
  document.documentElement.setAttribute("data-theme", theme);
  var readingKey = "yz-reading-size";
  var reading = "default";
  try {
    var storedReading = localStorage.getItem(readingKey);
    if (storedReading === "large" || storedReading === "xlarge") {
      reading = storedReading;
    }
  } catch (e) {}
  if (reading !== "default") {
    document.documentElement.setAttribute("data-reading-size", reading);
  }
})();
</script>"""


def _nav_anchor_html(site: dict, item: dict, active: str) -> str:
    label = esc(item.get("label", ""))
    raw_href = str(item.get("href", "#"))
    external = bool(item.get("external"))
    if external:
        href = esc(raw_href)
    elif raw_href.startswith("/#"):
        href = esc(with_base(site, raw_href))
    elif raw_href.startswith("#"):
        href = esc(with_base(site, "/") + raw_href)
    else:
        href = esc(with_base(site, raw_href))
    classes = []
    if external:
        classes.append("external")
    attrs = f' href="{href}"'
    if classes:
        attrs += f' class="{" ".join(classes)}"'
    if external:
        attrs += ' target="_blank" rel="noopener noreferrer"'
    elif not raw_href.startswith(("/#", "#")) and item.get("label") == active:
        attrs += ' aria-current="page"'
    return f"<a{attrs}>{label}</a>"


def nav_html(site: dict, active: str) -> str:
    """Primary dossier links. External writing/profiles live in the site footer."""
    primary, _external = _nav_link_groups(site, active)
    return "\n      ".join(primary)


def _footer_links_html(site: dict, active: str = "") -> str:
    contact = site["contact"]
    ext = site.get("external") or {}
    _primary, external = _nav_link_groups(site, active)
    email = esc(contact.get("email") or "")
    parts = [f'<a href="mailto:{email}">{email}</a>']
    card = str(ext.get("bitly_hub") or "").strip()
    if card:
        parts.append(
            f'<a class="external" href="{esc(card)}" target="_blank" '
            f'rel="noopener noreferrer">Digital card</a>'
        )
    parts.extend(external)
    return "\n      ".join(parts)


def _nav_link_groups(site: dict, active: str) -> tuple[list[str], list[str]]:
    primary: list[str] = []
    external_links: list[str] = []
    for item in site.get("nav") or []:
        if not isinstance(item, dict):
            continue
        markup = _nav_anchor_html(site, item, active)
        if item.get("footer_only") or item.get("external"):
            external_links.append(markup)
        else:
            primary.append(markup)
    return primary, external_links


STYLE_PARTS = (
    "tokens.css",
    "base.css",
    "chrome.css",
    "home.css",
    "library.css",
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


def public_origin(site: dict) -> str:
    return str(site.get("public_origin") or "https://www.yzouyang.com").rstrip("/")


def canonical_url(site: dict, path: str) -> str:
    origin = public_origin(site)
    if not path or path == "/" or path == "/index.html":
        return origin + "/"
    rel = path.replace("index.html", "")
    if not rel.startswith("/"):
        rel = "/" + rel
    return origin + rel


def page_description(site: dict, active: str, title: str) -> str:
    meta = site.get("page_meta") if isinstance(site.get("page_meta"), dict) else {}
    for key in (active, title):
        text = str(meta.get(key) or "").strip()
        if text:
            return text
    return str((site.get("person") or {}).get("tagline") or "").strip()


def person_json_ld(site: dict) -> str:
    person = site.get("person") or {}
    ext = site.get("external") or {}
    contact = site.get("contact") or {}
    same_as = [
        str(ext.get(k) or "").strip()
        for k in ("linkedin", "github", "medium", "blog")
        if str(ext.get(k) or "").strip()
    ]
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": person.get("full_name") or "Yingzhao Ouyang",
        "url": public_origin(site) + "/",
        "jobTitle": person.get("headline") or "",
        "email": contact.get("email") or "",
        "image": canonical_url(site, str(person.get("photo") or "/assets/profile.jpg")),
        "sameAs": same_as,
    }
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    return f'  <script type="application/ld+json">{payload}</script>'


def website_json_ld(site: dict) -> str:
    origin = public_origin(site)
    person = site.get("person") or {}
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": person.get("brand") or "yzouyang",
        "url": origin + "/",
        "description": str((site.get("page_meta") or {}).get("Home") or "").strip(),
    }
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    return f'  <script type="application/ld+json">{payload}</script>'


def article_json_ld(site: dict, row: dict, note_id: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": str(row.get("title") or "").strip(),
        "url": str(row.get("url") or "").strip(),
        "identifier": note_id,
        "datePublished": str(row.get("date") or "").strip() or None,
        "author": {
            "@type": "Person",
            "name": (site.get("person") or {}).get("full_name") or "Yingzhao Ouyang",
        },
    }
    data = {k: v for k, v in data.items() if v}
    payload = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    return f'  <script type="application/ld+json">{payload}</script>'


def _beat_value_html(row: dict, key: str) -> str:
    val = str(row.get(key) or "").strip()
    if key != "evidence":
        return esc(val)
    href = str(row.get("evidence_href") or "").strip()
    label = str(row.get("evidence_label") or "").strip()
    if not href:
        return esc(val)
    link = (
        f'<a class="external" href="{esc(href)}" target="_blank" '
        f'rel="noopener noreferrer">{esc(label or _link_label(href))}</a>'
    )
    if val:
        return f"{esc(val)} {link}"
    return link


def case_beats_html(row: dict, indent: str = "          ") -> str:
    parts: list[str] = []
    for key, label in CASE_BEAT_KEYS:
        html = _beat_value_html(row, key)
        if not html:
            continue
        parts.append(f"{indent}  <div><dt>{esc(label)}</dt><dd>{html}</dd></div>")
    if len(parts) < 2:
        return ""
    inner = "\n".join(parts)
    return f'{indent}<dl class="case-beats">\n{inner}\n{indent}</dl>\n'


def verify_panel_html(site: dict) -> str:
    block = site.get("credentials_verify") if isinstance(site.get("credentials_verify"), dict) else {}
    items = [i for i in (block.get("items") or []) if isinstance(i, dict)]
    if not items:
        return ""
    lede = str(block.get("lede") or "").strip()
    links = []
    for item in items:
        label = str(item.get("label") or "").strip()
        href = str(item.get("href") or "").strip()
        if not label or not href:
            continue
        abs_href = href if href.startswith("http") else with_base(site, href)
        links.append(
            f'<a class="external" href="{esc(abs_href)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(label)}</a>'
        )
    if not links:
        return ""
    lede_html = f"        <p>{esc(lede)}</p>\n" if lede else ""
    return (
        '      <aside class="verify-panel" aria-label="Verify credentials">\n'
        '        <p class="verify-label">Verify</p>\n'
        f"{lede_html}"
        f'        <p class="links">{" · ".join(links)}</p>\n'
        "      </aside>\n"
    )


def writing_items_html(rows: list[dict], *, featured: dict | None = None) -> list[str]:
    out: list[str] = []
    for row, note_id in _unique_note_catalog_ids(rows):
        title = (row.get("title") or "").strip()
        url = (row.get("url") or "").strip()
        if not title or not url:
            continue
        venue = esc(row.get("venue") or "Article")
        date_s = esc(row.get("date") or "")
        teaser = str(row.get("teaser") or "").strip()
        meta = " · ".join(x for x in (note_id, venue, date_s) if x)
        dek_html = ""
        if featured is row or row.get("start_here"):
            if teaser:
                dek_html = f'        <p class="note-dek">{esc(teaser)}</p>\n'
        out.append(
            f"      <li>\n"
            f'        <p class="catalogue-line meta">{meta}</p>\n'
            f'        <h3><a class="external" href="{esc(url)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(title)}</a></h3>\n'
            f"{dek_html}"
            f"      </li>"
        )
    return out


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
        '    <p class="page-toc-label">In this record</p>\n' if sidebar else ""
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
    extra_lede: str = "",
) -> str:
    """Legacy long-page shell (redirect stubs only)."""
    search_html = (
        '        <div class="page-search">\n'
        '          <label class="page-search-label" for="pagefind-search-input">'
        "Search the catalogue</label>\n"
        '          <div id="search"></div>\n'
        "        </div>\n"
        if search
        else ""
    )
    return f"""    <div class="page-with-toc">
{toc_html(toc, sidebar=True)}      <div class="page-main">
        <h1>{title}</h1>
        {lede_html}
{extra_lede}{search_html}{body}
      </div>
    </div>
"""


def library_index_html(
    entries: list[dict], *, label: str = "In this record", footer_html: str = ""
) -> str:
    """Left-column index for the library shell (button list, not in-page anchors)."""

    def render_list(nodes: list[dict], *, nested: bool = False) -> str:
        cls = "library-index-sub" if nested else "library-index-list"
        lines = [f'          <ul class="{cls}" role="list">']
        for node in nodes:
            if not isinstance(node, dict):
                continue
            panel_id = str(node.get("id") or "").strip()
            text = str(node.get("label") or panel_id).strip()
            if not panel_id:
                continue
            kids = node.get("children") or []
            child_html = "\n" + render_list(kids, nested=True) if kids else ""
            if kids:
                lines.append(
                    f'            <li class="library-index-group" data-panel-group-id="{esc(panel_id)}">\n'
                    f'              <span class="library-index-text library-index-group-label">{esc(text)}</span>'
                    f"{child_html}\n"
                    "            </li>"
                )
            else:
                lines.append(
                    f'            <li data-panel-id="{esc(panel_id)}" tabindex="0" role="button">\n'
                    f'              <span class="library-index-text">{esc(text)}</span>\n'
                    "            </li>"
                )
        lines.append("          </ul>")
        return "\n".join(lines)

    if not entries:
        return (
            '        <nav class="library-index" aria-label="In this record">\n'
            f'          <p class="library-index-label">{esc(label)}</p>\n'
            "        </nav>"
        )
    footer_block = (
        f"\n          <footer class=\"library-index-footer\">\n{footer_html}\n          </footer>"
        if footer_html.strip()
        else ""
    )
    return (
        '        <nav class="library-index" aria-label="In this record">\n'
        f'          <p class="library-index-label">{esc(label)}</p>\n'
        f"{render_list(entries)}{footer_block}\n"
        "        </nav>"
    )


def library_panel_html(
    panel_id: str,
    heading: str,
    body: str,
    *,
    level: str = "h2",
    hidden: bool = True,
    extra_attrs: str = "",
) -> str:
    tag = level if level in ("h2", "h3", "h4") else "h2"
    hidden_attr = " hidden" if hidden else ""
    return (
        f'        <article class="library-panel" data-panel-id="{esc(panel_id)}"{hidden_attr}'
        f"{extra_attrs}>\n"
        f'          <header class="library-panel-header">\n'
        f'            <{tag} class="library-panel-title">{heading}</{tag}>\n'
        f"          </header>\n"
        f'          <div class="library-panel-body">\n'
        f"{body}\n"
        f"          </div>\n"
        f"        </article>"
    )


def library_section_panel(
    section_id: str,
    heading: str,
    inner_html: str,
    *,
    level: str = "h2",
    variant: str = "",
    kicker: str = "",
) -> str:
    body = (
        section_fold_open(section_id, esc(heading), level=level, variant=variant, kicker=kicker)
        + inner_html
        + section_fold_close()
    )
    return library_panel_html(section_id, heading, body, level=level)


def _library_strip_html(site: dict, *, active: str) -> str:
    routes = (
        ("Systems", "/systems/", "systems"),
        ("Notes", "/notes/", "notes"),
        ("Credentials", "/credentials/", "credentials"),
    )
    links: list[str] = []
    for label, path, key in routes:
        if key == active:
            continue
        href = esc(with_base(site, path))
        links.append(f'<a href="{href}">{label}</a>')
    if not links:
        return ""
    return (
        '      <footer class="library-strip">\n'
        '        <p class="library-strip-copy meta">'
        '<span class="library-strip-label">Related paths</span> '
        + " · ".join(links)
        + "</p>\n"
        "      </footer>"
    )


def library_shell(
    *,
    site: dict,
    title: str,
    overview_html: str,
    toc: list[dict],
    panels: list[str],
    strip_html: str = "",
    record_panels_html: str = "",
    index_footer_html: str = "",
) -> str:
    index = library_index_html(toc, footer_html=index_footer_html)
    panels_block = "\n".join(panels)
    overview_block = (
        f'          <div class="library-overview">\n{overview_html}\n          </div>\n'
        if overview_html.strip()
        else ""
    )
    record_block = record_panels_html or ""
    strip_block = strip_html or ""
    page_footer = footer_html(site, compact=True)
    return (
        f'    <div class="library-shell" id="library-shell">\n'
        f'      <h1 class="visually-hidden">{title}</h1>\n'
        f'      <div class="library-frame">\n'
        f'        <div class="library-split" id="library-split">\n'
        f"{index}\n"
        f'          <div class="library-pane" aria-live="polite">\n'
        f'            <div class="library-pane-toolbar">\n'
        f'              <button type="button" class="library-back" hidden>Back to index</button>\n'
        f"            </div>\n"
        f"{overview_block}"
        f'            <div class="library-panels">\n'
        f"{panels_block}\n"
        f"{record_block}\n"
        f"            </div>\n"
        f"          </div>\n"
        f"        </div>\n"
        f"{strip_block}\n"
        f"      </div>\n"
        f"{page_footer}\n"
        f"    </div>\n"
    )


def section_fold_open(
    section_id: str,
    heading: str,
    *,
    level: str = "h2",
    variant: str = "",
    kicker: str = "",
) -> str:
    """Start a collapsible long-form section (default open).

    Summary is the visible section title. Nested h2/h3 inside <summary>
    breaks disclosure semantics, so the summary carries role=heading
    instead of a second, visually-hidden heading that duplicated the title.
    """
    aria_level = "2" if level == "h2" else "3"
    extra = f" section-fold--{variant}" if variant else ""
    kicker_html = (
        f'        <p class="section-kicker">{esc(kicker)}</p>\n' if kicker else ""
    )
    return (
        f'    <details class="section-fold{extra}" open>\n'
        f'      <summary class="section-fold-summary" id="{esc(section_id)}" '
        f'role="heading" aria-level="{aria_level}">'
        f"{heading}</summary>\n"
        f'      <div class="section-fold-body">\n'
        f"{kicker_html}"
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
    poster: str | None = None,
    include_fallback: bool = True,
) -> str:
    """Compact Figma link, plus an optional real poster image (no live iframe).

    Figma's embed canvas paints white and blows out the charcoal page.
    Empty ``.embed-frame-static`` fill boxes are forbidden — a static frame
    is emitted only when ``poster`` is a real image src. Policy: site-builder
    (fallback / ``.links`` must remain usable; embeds are not primary proof).
    """
    href = (link or embed or "").strip()
    poster_src = (poster or "").strip()
    bits: list[str] = []
    if include_fallback and href:
        bits.append(
            f'<a class="embed-fallback" href="{esc(href)}" target="_blank" '
            f'rel="noopener noreferrer"><strong>{esc(link_label)}</strong>'
            f" — opens in Figma</a>"
        )
    if poster_src and href:
        frame_class = "embed-frame embed-frame-static"
        if tall:
            frame_class += " embed-frame-tall"
        bits.append(
            f'<a class="{frame_class}" href="{esc(href)}" target="_blank" '
            f'rel="noopener noreferrer">'
            f'<img src="{esc(poster_src)}" alt="{esc(title)}"></a>'
        )
    if not bits:
        return ""
    inner = "\n        ".join(bits)
    return f"""
      <div class="embed-wrap">
        {inner}
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


def _footer_meta_html(site: dict) -> str:
    person = site["person"]
    location = str(person.get("location") or "").strip()
    focus = ""
    export = site.get("_export") or {}
    for row in _compose_current_index_rows(site, export):
        if not isinstance(row, dict):
            continue
        if _current_index_topic(row) == "systems":
            focus = str(row.get("label") or "").strip()
            break
    meta_bits = [x for x in (location, focus) if x]
    meta_line = " · ".join(meta_bits)
    return f'    <p class="library-card-meta">{esc(meta_line)}</p>\n' if meta_line else ""


def footer_html(site: dict, *, compact: bool = False, active: str = "") -> str:
    person = site["person"]
    year = date.today().year
    meta_html = _footer_meta_html(site)
    footer_links = _footer_links_html(site, active)
    footer_class = "library-page-footer library-card" if compact else "site-footer library-card"
    return f"""  <footer class="{footer_class}">
{meta_html}    <p>&copy; {year} {esc(person.get("full_name") or "yzouyang")}</p>
    <p class="footer-links">
      {footer_links}
    </p>
  </footer>"""


def layout(
    site: dict,
    title: str,
    active: str,
    body: str,
    *,
    pagefind: bool = False,
    path: str = "/",
    deck_mode: bool = False,
    header_search: bool = False,
    library_route: bool = False,
    home_route: bool = False,
    extra_head: str = "",
) -> str:
    person = site["person"]
    brand = esc(person.get("brand", "yzouyang"))
    page_title = f"{esc(title)} — {brand}"
    description = esc(page_description(site, active, title))
    canonical = esc(canonical_url(site, path))
    og_image = esc(canonical_url(site, str(person.get("photo") or "/assets/profile.jpg")))
    pf_attr = " data-pagefind-body" if pagefind else ""
    head_analytics = analytics_head(site)
    body_analytics = analytics_body(site, active)
    css = esc(with_base(site, "/styles.css"))
    chrome_js = esc(with_base(site, "/chrome.js"))
    pf_css = esc(with_base(site, "/pagefind/pagefind-ui.css"))
    pf_js = esc(with_base(site, "/pagefind/pagefind-ui.js"))
    home = esc(with_base(site, "/"))
    desktop_nav = nav_html(site, active)
    mobile_nav = nav_html(site, active)
    header_search_html = _header_search_html() if header_search else ""
    use_pagefind_ui = pagefind or header_search
    page_class = (
        "page library-route"
        if library_route
        else (
            "page home-route"
            if home_route
            else ("page library-deck-page" if deck_mode else "page")
        )
    )
    body_class = ' class="library-deck-body"' if deck_mode else ""
    pf_css_tag = f'\n  <link rel="stylesheet" href="{pf_css}" />' if use_pagefind_ui else ""
    pf_script = (
        f"""
  <script src="{pf_js}" type="text/javascript"></script>
  <script>
    window.addEventListener("DOMContentLoaded", () => {{
      const mount = document.querySelector("#search");
      if (mount && window.PagefindUI) {{
        new PagefindUI({{ element: "#search", showSubResults: true }});
        const input = mount.querySelector(".pagefind-ui__search-input");
        if (input) {{
          input.id = "pagefind-search-input";
          input.setAttribute("name", "q");
        }}
      }}
    }});
  </script>"""
        if use_pagefind_ui
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title}</title>
  <meta name="description" content="{description}" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:title" content="{page_title}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{og_image}" />
  <meta name="twitter:card" content="summary" />
{THEME_BOOT_SCRIPT}
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600;700&display=swap" rel="stylesheet" />{pf_css_tag}
  <link rel="stylesheet" href="{css}" />
{person_json_ld(site)}
{extra_head}
{head_analytics}
</head>
<body{body_class}>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="site-header-wrap">
  <header class="site-header">
    <p class="brand"><a href="{home}">{brand}</a></p>
    <div class="header-actions">
      <nav class="site-nav site-nav-desktop" aria-label="Primary">
        {desktop_nav}
      </nav>
{header_search_html}
      <button type="button" class="theme-toggle reading-size-toggle" data-reading-size-toggle aria-pressed="false" aria-label="Text size: standard. Click to make text larger.">
        <span class="reading-size-steps" aria-hidden="true">
          <span class="reading-size-step is-active" data-step="default">A</span>
          <span class="reading-size-step" data-step="large">A</span>
          <span class="reading-size-step" data-step="xlarge">A</span>
        </span>
      </button>
      <button type="button" class="theme-toggle" data-theme-toggle aria-pressed="false" aria-label="Theme: dark">
        <span class="theme-toggle-label">Dark</span>
      </button>
      <details class="nav-menu">
        <summary>Menu</summary>
        <nav class="site-nav" aria-label="Primary">
        {mobile_nav}
        </nav>
      </details>
    </div>
  </header>
  </div>
  <main id="main" class="{page_class}" aria-label="{esc(title)}"{pf_attr}>
{body}
  </main>
{footer_html(site) if not (library_route or home_route) else ""}{pf_script}
  <script src="{chrome_js}" defer></script>
{body_analytics}
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("\r\n", "\n"), encoding="utf-8")


def _curated_tools(tools: object) -> list[str]:
    out: list[str] = []
    if not isinstance(tools, list):
        return out
    for item in tools:
        label = str(item).strip()
        if not label:
            continue
        out.append(label)
        if len(out) >= MAX_CASE_TOOLS:
            break
    return out


def _merge_project_copy(row: dict, copy_map: dict) -> dict:
    merged = dict(row)
    override = copy_map.get(str(row.get("id") or ""))
    if isinstance(override, dict):
        for key in (
            "outcome",
            "scope",
            "tools",
            "description",
            "poster",
            "problem",
            "role",
            "decision",
            "evidence",
            "evidence_href",
            "evidence_label",
        ):
            if override.get(key):
                merged[key] = override[key]
    merged["tools"] = _curated_tools(merged.get("tools"))
    return merged


def case_copy_by_id(site: dict, case_id: str) -> dict:
    """Beats live in enterprise_copy / project_copy, keyed by stable heading id."""
    if not case_id:
        return {}
    ent = site.get("enterprise_copy") if isinstance(site.get("enterprise_copy"), dict) else {}
    overlay = ent.get(case_id)
    if isinstance(overlay, dict):
        return overlay
    projects = site.get("project_copy") if isinstance(site.get("project_copy"), dict) else {}
    overlay = projects.get(case_id)
    return overlay if isinstance(overlay, dict) else {}


def compose_home_selected_row(site: dict, row: dict) -> dict:
    """Home titles/tools compose from shared case copy; beats are not re-authored."""
    case_id = str(row.get("id") or "").strip()
    source = case_copy_by_id(site, case_id)
    composed: dict = {}
    if case_id:
        composed["id"] = case_id
    for key in (
        "problem",
        "role",
        "decision",
        "outcome",
        "evidence",
        "evidence_href",
        "evidence_label",
        "tools",
    ):
        if source.get(key):
            composed[key] = source[key]
    for key in ("title", "evidence", "evidence_href", "evidence_label", "tools", "record_id", "domains"):
        if row.get(key):
            composed[key] = row[key]
    href = str(row.get("href") or "").strip()
    if not href and case_id:
        href = f"/systems/#{case_id}"
    if href:
        composed["href"] = href
    return composed


def resolve_enterprise_overlay(item: dict, ent_copy: dict) -> tuple[str, dict]:
    """Match an export enterprise row to overlay copy keyed by heading_id."""
    if not isinstance(ent_copy, dict):
        ent_copy = {}
    item_title = str(item.get("title") or "").strip()
    slug = slugify(item_title) if item_title else ""
    if slug and isinstance(ent_copy.get(slug), dict):
        return slug, ent_copy[slug]
    for key, overlay in ent_copy.items():
        if not isinstance(overlay, dict):
            continue
        display = str(overlay.get("title") or "").strip()
        if display and display == item_title:
            return str(key), overlay
        pinned = str(overlay.get("heading_id") or "").strip()
        if pinned and pinned == slug:
            return pinned, overlay
    return slug, {}


def _atmosphere_slot(site: dict, key: str) -> dict:
    block = site.get("atmosphere") if isinstance(site.get("atmosphere"), dict) else {}
    row = block.get(key)
    return row if isinstance(row, dict) else {}


def _atmosphere_figure_html(
    site: dict,
    key: str,
    *,
    figure_class: str = "atmosphere-figure",
    loading: str = "lazy",
    fetchpriority: str | None = None,
) -> str:
    row = _atmosphere_slot(site, key)
    src_path = str(row.get("src") or "").strip()
    if not src_path:
        return ""
    src = esc(with_base(site, src_path))
    alt = esc(str(row.get("alt") or "Atmosphere still"))
    credit = esc(str(row.get("credit") or "Atmosphere still"))
    width = int(row.get("width") or 0) or None
    height = int(row.get("height") or 0) or None
    obj_pos = esc(str(row.get("object_position") or "center center"))
    wh = ""
    if width and height:
        wh = f' width="{width}" height="{height}"'
    fp = f' fetchpriority="{fetchpriority}"' if fetchpriority else ""
    loading_attr = f' loading="{loading}"' if loading else ""
    return (
        f'      <figure class="{figure_class}">\n'
        f'        <img src="{src}" alt="{alt}"{wh} decoding="async"{loading_attr}{fp} '
        f'style="object-position: {obj_pos}" />\n'
        f'        <figcaption class="meta">{credit}</figcaption>\n'
        f"      </figure>"
    )


def _note_catalog_id(row: dict, index: int = 0) -> str:
    custom = str(row.get("id") or row.get("record_id") or "").strip()
    if custom.startswith("NOTE-"):
        return custom
    if custom:
        return custom
    date_s = str(row.get("date") or "").strip()
    if len(date_s) >= 7:
        parts = date_s.split("-")
        if len(parts) >= 2:
            return f"NOTE-{parts[0]}-{parts[1].zfill(3)}"
    return f"NOTE-2026-{index + 1:03d}"


def _writing_rows(export: dict) -> list[dict]:
    """Normalize export `writing` records for site builders."""
    rows: list[dict] = []
    for raw in export.get("writing") or []:
        if not isinstance(raw, dict):
            continue
        syndication = raw.get("syndication") if isinstance(raw.get("syndication"), dict) else {}
        medium = str(syndication.get("medium") or "").strip() or None
        linkedin = str(syndication.get("linkedin") or "").strip() or None
        discuss_url = linkedin or medium or ""
        venue = "LinkedIn" if linkedin and not medium else ("Medium" if medium else "Article")
        rows.append(
            {
                "id": raw.get("id"),
                "record_id": raw.get("id"),
                "title": raw.get("title"),
                "teaser": str(raw.get("teaser") or raw.get("summary") or "").strip(),
                "date": raw.get("date"),
                "category": raw.get("category"),
                "series": raw.get("series"),
                "start_here": bool(raw.get("start_here")),
                "body_md": raw.get("body_md"),
                "syndication": syndication,
                "aliases": raw.get("aliases") or [],
                "url": discuss_url,
                "venue": venue,
                "canonical": raw.get("canonical"),
            }
        )
    return rows


def _writing_discussion_link(row: dict) -> tuple[str, str]:
    synd = row.get("syndication") if isinstance(row.get("syndication"), dict) else {}
    linkedin = str(synd.get("linkedin") or "").strip()
    medium = str(synd.get("medium") or "").strip()
    if linkedin:
        return linkedin, "Discuss on LinkedIn"
    if medium:
        return medium, "Discuss on Medium"
    url = str(row.get("url") or "").strip()
    venue = str(row.get("venue") or "Article")
    return url, f"Read on {venue}"


def _writing_also_links(row: dict) -> list[tuple[str, str]]:
    synd = row.get("syndication") if isinstance(row.get("syndication"), dict) else {}
    linkedin = str(synd.get("linkedin") or "").strip()
    medium = str(synd.get("medium") or "").strip()
    discuss_url, _ = _writing_discussion_link(row)
    links: list[tuple[str, str]] = []
    if medium and medium != discuss_url:
        links.append((medium, "Also on Medium"))
    if linkedin and linkedin != discuss_url:
        links.append((linkedin, "Also on LinkedIn"))
    return links


def _note_href(site: dict, note_id: str) -> str:
    return with_base(site, f"/notes/#{note_id}")


def _note_asset_href(site: dict, note_id: str, rel_path: str) -> str:
    cleaned = rel_path.strip().replace("\\", "/")
    if cleaned.startswith("assets/"):
        cleaned = cleaned[len("assets/") :]
    return with_base(site, f"/assets/notes/{note_id}/{cleaned}")


def _inline_markdown(text: str, *, note_id: str, site: dict) -> str:
    safe = esc(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"\*(.+?)\*", r"<em>\1</em>", safe)
    safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)

    def link_repl(match: re.Match[str]) -> str:
        label, href = match.group(1), match.group(2).strip()
        if href.startswith("assets/"):
            path = _note_asset_href(site, note_id, href)
            return f'<a href="{esc(path)}">{label}</a>'
        if href.startswith(("http://", "https://")):
            return (
                f'<a class="external" href="{esc(href)}" target="_blank" '
                f'rel="noopener noreferrer">{label}</a>'
            )
        return f'<a href="{esc(with_base(site, href))}">{label}</a>'

    safe = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, safe)

    def img_repl(match: re.Match[str]) -> str:
        alt, src = match.group(1), match.group(2).strip()
        if src.startswith("assets/"):
            path = _note_asset_href(site, note_id, src)
        elif src.startswith(("http://", "https://")):
            path = esc(src)
        else:
            path = esc(with_base(site, src))
        return f'<img src="{path}" alt="{esc(alt)}" loading="lazy" />'

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img_repl, safe)


def _markdown_to_html(md: str, *, note_id: str, site: dict) -> str:
    if not str(md or "").strip():
        return ""
    out: list[str] = []
    in_code = False
    in_list = False
    para: list[str] = []

    def flush_para() -> None:
        nonlocal in_list, para
        if para:
            joined = " ".join(para).strip()
            if joined:
                out.append(f"<p>{_inline_markdown(joined, note_id=note_id, site=site)}</p>")
            para = []
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw_line in md.splitlines():
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            flush_para()
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            continue
        if in_code:
            out.append(esc(raw_line) + "\n")
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            flush_para()
            raw_level = len(heading.group(1))
            level = 3 if raw_level <= 2 else min(raw_level, 4)
            out.append(
                f"<h{level}>{_inline_markdown(heading.group(2), note_id=note_id, site=site)}</h{level}>"
            )
            continue
        if line.strip().startswith("- "):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(
                f"<li>{_inline_markdown(line.strip()[2:], note_id=note_id, site=site)}</li>"
            )
            continue
        if not line.strip():
            flush_para()
            continue
        para.append(line.strip())
    flush_para()
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def _writing_links_html(site: dict, row: dict) -> str:
    links: list[str] = []
    discuss_url, discuss_label = _writing_discussion_link(row)
    if discuss_url.startswith("http"):
        links.append(
            f'<a class="external map-record-read" href="{esc(discuss_url)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(discuss_label)}</a>'
        )
    for href, label in _writing_also_links(row):
        links.append(
            f'<a class="external" href="{esc(href)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(label)}</a>'
        )
    if not links:
        return ""
    return f'        <p class="links">{" · ".join(links)}</p>\n'


def _unique_note_catalog_ids(rows: list[dict]) -> list[tuple[dict, str]]:
    """Assign stable NOTE-* ids; bump suffix when two essays would collide."""
    used: set[str] = set()
    out: list[tuple[dict, str]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        base = _note_catalog_id(row, idx)
        note_id = base
        bump = 2
        while note_id in used:
            note_id = f"{base}-{bump}"
            bump += 1
        used.add(note_id)
        out.append((row, note_id))
    return out


RECORD_KIND_ROUTE = {
    "sys": "/systems/",
    "lab": "/systems/",
    "note": "/notes/",
}

HASH_ROUTE_ALIASES = {
    "system-map": "/systems/",
    "selected-systems": "/systems/",
    "workshop": "/systems/",
    "reading-room": "/notes/",
    "profile": "/",
    "contact": "/",
    "credentials": "/credentials/",
}


def _route_for_slide(slide_id: str) -> str:
    return HASH_ROUTE_ALIASES.get(slide_id, f"/#{slide_id}")


def _slide_id_for_record(record_id: str, kind: str | None = None) -> str:
    if kind == "note":
        return "reading-room"
    return "system-map"


def _home_slide_for_path(path: str) -> str | None:
    raw = path.split("#")[0].strip()
    if not raw.startswith("/"):
        return None
    normalized = raw.rstrip("/").lower() or "/"
    routes = {
        "/systems": "system-map",
        "/portfolio": "system-map",
        "/work": "system-map",
        "/about": None,
        "/credentials": "credentials",
        "/notes": "reading-room",
        "/perspectives": "reading-room",
        "/contact": None,
    }
    return routes.get(normalized)


def _internal_route_link(
    site: dict,
    slide_id: str,
    label: str,
    *,
    record_id: str | None = None,
    link_class: str = "route-link",
) -> str:
    route = _route_for_slide(slide_id)
    href = with_base(site, route)
    if record_id and slide_id == "system-map":
        href = with_base(site, f"/systems/#{record_id}")
    classes = link_class.strip()
    return f'<a class="{esc(classes)}" href="{esc(href)}">{esc(label)}</a>'


def _home_slide_link(site: dict, slide_id: str, label: str, **kwargs) -> str:
    """Backward-compatible alias for map panel footer links."""
    return _internal_route_link(site, slide_id, label, **kwargs)


CURRENT_INDEX_TOPICS = {
    "notes": "Notes",
    "systems": "Systems",
}
CURRENT_INDEX_STATUS_LEGACY = {
    "studying": "notes",
    "building": "systems",
    "writing": "notes",
}


def _current_index_topic(row: dict) -> str:
    topic = str(row.get("topic") or "").strip().lower()
    if topic in CURRENT_INDEX_TOPICS:
        return topic
    status = str(row.get("status") or "").strip().lower()
    return CURRENT_INDEX_STATUS_LEGACY.get(status, "")


def _current_index_topic_label(topic: str) -> str:
    return CURRENT_INDEX_TOPICS.get(topic, "")


def _short_title(title: str, *, max_len: int = 72) -> str:
    text = str(title or "").strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rsplit(" ", 1)[0]
    return (cut or text[: max_len - 1]).rstrip() + "…"


def _weekly_rotation_index(count: int, salt: str) -> int:
    if count <= 1:
        return 0
    year, week, _ = date.today().isocalendar()
    bucket = year * 100 + week
    offset = sum(ord(ch) for ch in salt)
    return (bucket + offset) % count


def _home_highlights_rotation(site: dict) -> str:
    config = site.get("home_highlights")
    if not isinstance(config, dict):
        return "weekly"
    mode = str(config.get("rotation") or "weekly").strip().lower()
    return mode if mode in {"weekly", "pinned"} else "weekly"


def _compose_current_index_rows(site: dict, export: dict) -> list[dict]:
    """Build home highlight lines — weekly rotation from catalog pools by default."""
    if _home_highlights_rotation(site) == "pinned":
        return [r for r in (site.get("current_index") or []) if isinstance(r, dict)][:2]

    systems_pool: list[dict] = []
    for raw in site.get("home_selected") or []:
        if not isinstance(raw, dict):
            continue
        composed = compose_home_selected_row(site, raw)
        record_id = str(composed.get("record_id") or raw.get("record_id") or "").strip()
        title = str(composed.get("title") or "").strip()
        if record_id and title:
            systems_pool.append(
                {
                    "topic": "systems",
                    "label": title,
                    "href": f"/systems/#{record_id}",
                }
            )

    writing = _writing_rows(export)
    assigned = _unique_note_catalog_ids(writing)
    notes_pool: list[dict] = []
    for row, note_id in assigned:
        title = str(row.get("title") or "").strip()
        teaser = str(row.get("teaser") or "").strip()
        note_label = teaser or _short_title(title)
        if note_id and note_label:
            notes_pool.append(
                {
                    "topic": "notes",
                    "label": note_label,
                    "href": f"/notes/#{note_id}",
                }
            )

    rows: list[dict] = []
    if systems_pool:
        rows.append(systems_pool[_weekly_rotation_index(len(systems_pool), "systems")])
    if notes_pool:
        rows.append(notes_pool[_weekly_rotation_index(len(notes_pool), "notes")])
    return rows[:2]


def _current_index_link_html(site: dict, href: str, label: str) -> str:
    if href.startswith("http"):
        link = esc(href)
        return (
            f'<a class="external" href="{link}" target="_blank" '
            f'rel="noopener noreferrer">{label}</a>'
        )
    if href.startswith("/"):
        link = esc(with_base(site, href))
        return f'<a class="route-link" href="{link}">{label}</a>'
    return label


def _current_index_html(site: dict, export: dict) -> str:
    rows = _compose_current_index_rows(site, export)
    if not rows:
        return ""
    items: list[str] = []
    for row in rows:
        topic = _current_index_topic(row)
        topic_label = _current_index_topic_label(topic)
        label = esc(str(row.get("label") or "").strip())
        href = str(row.get("href") or "").strip()
        if not topic_label or not label or not href:
            continue
        label_html = _current_index_link_html(site, href, label)
        items.append(
            f"          <li><span class=\"index-topic\">{esc(topic_label)}</span>"
            f"<span class=\"index-entry\">{label_html}</span></li>"
        )
    if not items:
        return ""
    return (
        '        <ul class="current-index" aria-label="Selected highlights">\n'
        + "\n".join(items)
        + "\n        </ul>"
    )


def _map_label_tspans(x: int, y: int, label: str) -> str:
    """Wrap a domain label into up to two SVG lines below a node."""
    max_chars = 20
    words = label.split()
    lines: list[str] = []
    line: list[str] = []
    for word in words:
        candidate = " ".join(line + [word])
        if len(candidate) > max_chars and line:
            lines.append(" ".join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(" ".join(line))
    if len(lines) == 2 and len(lines[1]) <= 4:
        merged = f"{lines[0]} {lines[1]}"
        if len(merged) <= max_chars + 6:
            lines = [merged]
    lines = lines[:2]
    tspans = []
    for idx, chunk in enumerate(lines):
        dy = "0" if idx == 0 else "1.05em"
        tspans.append(f'<tspan x="{x}" dy="{dy}">{esc(chunk)}</tspan>')
    return (
        f'<text class="map-node-label" text-anchor="middle" x="{x}" y="{y + 20}">'
        + "".join(tspans)
        + "</text>"
    )


def _domain_target_section(domain: dict) -> str:
    explicit = str(domain.get("target") or "").strip()
    if explicit:
        return explicit
    related = [str(r).strip() for r in (domain.get("related") or []) if str(r).strip()]
    has_sys = any(r.startswith("SYS-") for r in related)
    has_lab = any(r.startswith("LAB-") for r in related)
    has_note = any(r.startswith("NOTE-") for r in related)
    if has_lab and not has_sys:
        return "system-map"
    if has_note and not has_sys and not has_lab:
        return "reading-room"
    return "system-map"


def _domain_target_label(target: str) -> str:
    labels = {
        "system-map": "View full catalogue",
        "selected-systems": "View full catalogue",
        "reading-room": "View notes",
        "profile": "View profile",
        "credentials": "View credentials",
        "contact": "Connect",
    }
    return labels.get(target, "Open section")


def _map_record_lookup(site: dict, export: dict | None = None) -> dict[str, dict]:
    export = export if export is not None else (site.get("_export") or {})
    lookup: dict[str, dict] = {}
    for row in site.get("home_selected") or []:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("record_id") or "").strip()
        if rid:
            lookup[rid] = {
                "kind": "sys",
                "title": str(row.get("title") or "").strip(),
                "href": with_base(site, str(row.get("href") or "/systems/")),
            }
    for row in site.get("workshop") or []:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("record_id") or "").strip()
        if not rid:
            continue
        href = str(row.get("href") or "").strip()
        if href.startswith("/"):
            href = with_base(site, href)
        lookup[rid] = {
            "kind": "lab",
            "title": str(row.get("title") or "").strip(),
            "href": href,
            "summary": str(row.get("constraint") or "").strip(),
            "category": str(row.get("category") or "").strip(),
        }
    for idx, row in enumerate(_writing_rows(export)):
        if not isinstance(row, dict):
            continue
        rid = _note_catalog_id(row, idx)
        venue = str(row.get("venue") or "Article").strip()
        date_s = str(row.get("date") or "").strip()
        lookup[rid] = {
            "kind": "note",
            "title": str(row.get("title") or "").strip(),
            "href": _note_href(site, rid),
            "summary": str(row.get("teaser") or "").strip(),
            "venue": venue,
            "date": date_s,
            "category": _note_category(row),
            "series": _note_series(row),
        }
    return lookup


def _map_record_read_link(href: str, kind: str) -> str:
    if kind == "note":
        label = "Read note"
    elif kind == "lab":
        label = "View project"
    else:
        label = "Open record"
    if href.startswith("http"):
        return (
            f'<a class="external map-record-read" href="{esc(href)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(label)}</a>'
        )
    return f'<a class="map-record-read" href="{esc(href)}">{esc(label)}</a>'


def _map_record_panel_body(site: dict, record_id: str, meta: dict, *, omit_title: bool = False) -> str:
    kind = str(meta.get("kind") or "record")
    title = str(meta.get("title") or record_id).strip()
    if kind == "sys":
        row = next(
            (
                compose_home_selected_row(site, r)
                for r in (site.get("home_selected") or [])
                if isinstance(r, dict)
                and str(r.get("record_id") or "").strip() == record_id
            ),
            None,
        )
        if not row:
            return ""
        return (
            '          <div class="system-map-record-body">\n'
            + _system_record_panel_body(site, row, omit_title=omit_title)
            + "          </div>"
        )

    id_html = f'            <p class="record-id">{esc(record_id)}</p>\n'
    title_html = (
        ""
        if omit_title
        else f'            <h3 class="system-map-record-title">{esc(title)}</h3>\n'
    )
    summary = str(meta.get("summary") or "").strip()
    summary_html = (
        f'            <p class="record-context">{esc(summary)}</p>\n' if summary else ""
    )
    extra_html = ""
    if kind == "note":
        venue = str(meta.get("venue") or "").strip()
        date_s = str(meta.get("date") or "").strip()
        meta_line = " · ".join(x for x in (venue, date_s) if x)
        if meta_line:
            extra_html = f'            <p class="catalogue-line meta">{esc(meta_line)}</p>\n'
    elif kind == "lab":
        category = str(meta.get("category") or "").strip()
        if category:
            extra_html = f'            <p class="record-domains">{esc(category)}</p>\n'
    href = str(meta.get("href") or "").strip()
    link_html = (
        f'            <p class="links">{_map_record_read_link(href, kind)}</p>\n'
        if href
        else ""
    )
    return (
        '          <div class="system-map-record-body">\n'
        f"{id_html}"
        f"{title_html}"
        f"{summary_html}"
        f"{extra_html}"
        f"{link_html}"
        "          </div>"
    )


def _record_domain_key(domains: list[dict], record_id: str) -> str:
    for domain in domains:
        related = [str(r).strip() for r in (domain.get("related") or []) if str(r).strip()]
        if record_id in related:
            return str(domain.get("id") or "").strip()
    return ""


def _system_record_domain_key(record_id: str) -> str:
    if record_id == "SYS-01":
        return "finops"
    if record_id == "SYS-03":
        return "ai-architecture"
    return "data-platforms"


def _system_record_panel_body(site: dict, row: dict, *, omit_title: bool = False) -> str:
    record_id = str(row.get("record_id") or "").strip()
    title = str(row.get("title") or "").strip()
    problem = str(row.get("problem") or "").strip()
    domains = row.get("domains") or []
    domain_line = " · ".join(str(d).strip() for d in domains if str(d).strip())
    methods = _curated_tools(row.get("tools"))
    methods_line = ", ".join(methods) if methods else ""
    impact = _record_impact_html(site, record_id).strip()
    if impact:
        impact = impact.replace("          ", "            ", 1)
    parts: list[str] = []
    if record_id:
        parts.append(f'            <p class="record-id">{esc(record_id)}</p>')
    if not omit_title:
        parts.append(f'            <h3 class="system-map-record-title">{esc(title)}</h3>')
    if problem:
        parts.append(f'            <p class="record-context">{esc(problem)}</p>')
    if domain_line:
        parts.append(f'            <p class="record-domains">{esc(domain_line)}</p>')
    if methods_line:
        parts.append(
            f'            <p class="record-methods meta">Components: {esc(methods_line)}</p>'
        )
    if impact:
        parts.append(impact)
    return "\n".join(parts) + "\n"


def _map_record_panels_html(site: dict, domains: list[dict]) -> str:
    lookup = _map_record_lookup(site)
    referenced: list[str] = []
    seen: set[str] = set()
    for domain in domains[:6]:
        for record_id in domain.get("related") or []:
            rid = str(record_id).strip()
            if rid and rid not in seen:
                seen.add(rid)
                referenced.append(rid)
    panels: list[str] = []
    for record_id in referenced:
        meta = lookup.get(record_id)
        if not meta or not meta.get("title"):
            continue
        body = _map_record_panel_body(site, record_id, meta)
        if not body:
            continue
        domain_key = _record_domain_key(domains, record_id) or _system_record_domain_key(record_id)
        related_html = _related_paths_html(site, record_id, domain_key, domains)
        panels.append(
            f'          <article class="system-map-record-panel" data-record="{esc(record_id)}" '
            f'data-kind="{esc(str(meta.get("kind") or "record"))}" '
            f'data-domain="{esc(domain_key)}" hidden>\n'
            '            <button type="button" class="map-record-back" '
            'data-record-back>Back to domain</button>\n'
            f"{body}"
            f"{related_html}"
            "          </article>"
        )
    if not panels:
        return ""
    return (
        '          <div class="system-map-record-panels">\n'
        + "\n".join(panels)
        + "\n          </div>"
    )


def _map_detail_record_item(site: dict, record_id: str, meta: dict) -> str:
    title = str(meta.get("title") or record_id).strip()
    kind = str(meta.get("kind") or "record")
    href = str(meta.get("href") or "").strip()
    kind_label = {"sys": "System", "lab": "Experiment", "note": "Note"}.get(kind, "Record")
    if kind in ("sys", "note", "lab"):
        control = (
            f'<button type="button" class="map-record-select" '
            f'data-record-select="{esc(record_id)}">{esc(title)}</button>'
        )
    elif href.startswith("http"):
        control = (
            f'<a class="external" href="{esc(href)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(title)}</a>'
        )
    else:
        slide = _slide_id_for_record(record_id, kind)
        control = _home_slide_link(site, slide, title, record_id=record_id)
    return (
        f'            <li data-record="{esc(record_id)}" data-kind="{esc(kind)}">\n'
        f'              <span class="map-detail-kind meta">{esc(kind_label)}</span>\n'
        f'              <p class="record-id">{esc(record_id)}</p>\n'
        f"              <p>{control}</p>\n"
        f"            </li>"
    )


def _map_domain_index_html(domains: list[dict], *, explorer: bool = False) -> str:
    items: list[str] = []
    for domain in domains[:6]:
        did = str(domain.get("id") or "").strip()
        label = str(domain.get("label") or did)
        summary = str(domain.get("summary") or "").strip()
        related = [str(r).strip() for r in (domain.get("related") or []) if str(r).strip()]
        rel_attr = " ".join(related)
        target = _domain_target_section(domain)
        summary_html = ""
        if summary and not explorer:
            summary_html = (
                f'            <p class="domain-index-summary">{esc(summary)}</p>\n'
            )
        items.append(
            f'          <li data-domain="{esc(did)}" data-related="{esc(rel_attr)}" '
            f'data-target="{esc(target)}">\n'
            f'            <span class="domain-index-label">{esc(label)}</span>\n'
            f"{summary_html}"
            f"          </li>"
        )
    if not items:
        return ""
    lede_html = ""
    if not explorer:
        lede_html = (
            '          <p class="system-map-detail-lede">Select a domain to view representative '
            "systems and notes.</p>\n"
        )
    return (
        '        <div class="system-map-domain-index">\n'
        f"{lede_html}"
        '          <ul class="system-map-domain-index-list" role="list">\n'
        + "\n".join(items)
        + "\n          </ul>\n"
        "        </div>"
    )


def _map_detail_panels_only_html(site: dict, domains: list[dict]) -> str:
    lookup = _map_record_lookup(site)
    panels: list[str] = []
    for domain in domains[:6]:
        did = str(domain.get("id") or "").strip()
        label = str(domain.get("label") or did)
        summary = str(domain.get("summary") or "").strip()
        related = [str(r).strip() for r in (domain.get("related") or []) if str(r).strip()]
        rel_attr = " ".join(related)
        target = _domain_target_section(domain)
        target_label = _domain_target_label(target)
        items: list[str] = []
        for record_id in related:
            meta = lookup.get(record_id)
            if meta and meta.get("title"):
                items.append(_map_detail_record_item(site, record_id, meta))
        if not items:
            continue
        summary_html = (
            f'            <p class="system-map-detail-summary">{esc(summary)}</p>\n'
            if summary
            else ""
        )
        footer_html = ""
        if target not in ("system-map", "selected-systems"):
            footer_html = (
                f'            <p class="links">{_home_slide_link(site, target, target_label)}</p>\n'
            )
        panels.append(
            f'          <article class="system-map-detail-panel" data-domain="{esc(did)}" '
            f'data-related="{esc(rel_attr)}" data-target="{esc(target)}" hidden>\n'
            f'            <h3 class="system-map-detail-title">{esc(label)}</h3>\n'
            f"{summary_html}"
            f'            <ul class="map-detail-records">\n'
            + "\n".join(items)
            + "\n            </ul>\n"
            f"{footer_html}"
            "          </article>"
        )
    return "\n".join(panels)


def _map_detail_panels_html(site: dict, domains: list[dict]) -> str:
    panels = _map_detail_panels_only_html(site, domains)
    if not panels:
        return ""
    index_html = _map_domain_index_html(domains[:6])
    record_panels_html = _map_record_panels_html(site, domains[:6])
    return (
        '        <aside class="system-map-detail" aria-live="polite">\n'
        f"{index_html}\n"
        '          <div class="system-map-detail-panels">\n'
        + panels
        + "\n          </div>\n"
        f"{record_panels_html}\n"
        "        </aside>"
    )


def _systems_explorer_html(site: dict) -> str:
    """Viewport split-pane: domains (left) · record pane (right) · browse strip (bottom)."""
    domains = [d for d in (site.get("system_map") or []) if isinstance(d, dict)]
    if len(domains) < 4:
        return ""
    domain_nav = _map_domain_index_html(domains[:6], explorer=True)
    detail_panels = _map_detail_panels_only_html(site, domains[:6])
    record_panels = _map_record_panels_html(site, domains[:6])
    catalogue_href = esc(with_base(site, "/systems/catalogue/"))
    notes_href = esc(with_base(site, "/notes/"))
    credentials_href = esc(with_base(site, "/credentials/"))
    return (
        '    <div class="systems-shell">\n'
        '      <h1 class="visually-hidden">Systems</h1>\n'
        '      <div class="systems-split system-map-section" id="system-map">\n'
        f'        <nav class="systems-domains" aria-label="Domains">\n{domain_nav}\n'
        "        </nav>\n"
        '        <div class="systems-pane system-map-detail" aria-live="polite">\n'
        '          <p class="systems-pane-lede">Select a domain to view representative '
        "systems and notes.</p>\n"
        '          <div class="system-map-detail-panels">\n'
        f"{detail_panels}\n"
        "          </div>\n"
        f"{record_panels}\n"
        "        </div>\n"
        "      </div>\n"
        '      <footer class="systems-strip">\n'
        '        <p class="systems-strip-copy meta">'
        '<span class="systems-strip-label">Related paths</span> '
        f'<a href="{catalogue_href}">Browse full catalogue</a> · '
        f'<a href="{notes_href}">Notes</a> · '
        f'<a href="{credentials_href}">Credentials</a></p>\n'
        "      </footer>\n"
        "    </div>\n"
    )


def _header_search_html() -> str:
    return (
        '      <div class="header-search page-search">\n'
        '        <label class="page-search-label" for="pagefind-search-input">'
        "Search catalogue</label>\n"
        '        <div id="search"></div>\n'
        "      </div>"
    )


def _system_map_html(site: dict, *, on_systems_page: bool = False) -> str:
    domains = [d for d in (site.get("system_map") or []) if isinstance(d, dict)]
    if len(domains) < 4:
        return ""
    nodes_svg: list[str] = []
    positions = [
        (80, 40),
        (220, 40),
        (360, 40),
        (80, 120),
        (220, 120),
        (360, 120),
    ]
    for idx, domain in enumerate(domains[:6]):
        did = str(domain.get("id") or f"domain-{idx}")
        label = str(domain.get("label") or did)
        x, y = positions[idx] if idx < len(positions) else (220, 80)
        nodes_svg.append(
            f'          <g class="map-node" data-domain="{esc(did)}" tabindex="0" '
            f'role="button" aria-label="{esc(label)}">'
            f'<circle cx="{x}" cy="{y}" r="6" />'
            f"{_map_label_tspans(x, y, label)}"
            f'<title>{esc(label)}</title></g>'
        )
    lines = [
        '          <line x1="80" y1="40" x2="220" y2="40" />',
        '          <line x1="220" y1="40" x2="360" y2="40" />',
        '          <line x1="80" y1="120" x2="220" y2="120" />',
        '          <line x1="220" y1="120" x2="360" y2="120" />',
        '          <line x1="140" y1="40" x2="140" y2="120" />',
        '          <line x1="280" y1="40" x2="280" y2="120" />',
    ]
    detail_html = _map_detail_panels_html(site, domains[:6])
    map_svg = (
        '        <svg class="system-map-svg" viewBox="0 0 440 200" role="img" '
        'aria-label="Principal domains and their connections">\n'
        + "\n".join(lines)
        + "\n"
        + "\n".join(nodes_svg)
        + "\n        </svg>"
    )
    stage_parts = [
        '      <div class="system-map-stage">\n'
        '        <div class="system-map-panel">\n'
        + map_svg
        + "\n        </div>",
    ]
    if detail_html:
        stage_parts.append(detail_html)
    stage_parts.append("      </div>")
    stage_inner = "\n".join(stage_parts)
    section_class = "systems-explorer system-map-section" if on_systems_page else "home-plate home-systems-teaser"
    heading = "Domain map" if on_systems_page else "Featured systems"
    return (
        f'    <section id="system-map" class="{section_class}" '
        f'aria-labelledby="system-map-heading">\n'
        f'      <h2 id="system-map-heading">{heading}</h2>\n'
        f"{stage_inner}\n"
        "    </section>\n"
    )


def _record_impact_html(site: dict, record_id: str) -> str:
    if record_id != "SYS-01":
        return ""
    bits: list[str] = []
    for row in (site.get("outcomes") or [])[:3]:
        if not isinstance(row, dict):
            continue
        metric = str(row.get("metric") or "").strip()
        label = str(row.get("label") or "").strip()
        if metric and label:
            bits.append(f"{metric} — {label}")
    if not bits:
        return ""
    return f'          <p class="record-impact">{esc("; ".join(bits))}</p>\n'


def _selected_systems_html(site: dict) -> str:
    """Deprecated: system records now live in system-map side panels."""
    return ""


def _reading_room_html(site: dict, export: dict) -> str:
    rows = _writing_rows(export)
    start = [r for r in rows if r.get("start_here")]
    rest = [r for r in rows if not r.get("start_here")]
    if not start:
        start, rest = rows[:1], rows[1:]
    if not start and not rest:
        return ""
    featured = start[0] if start else None
    featured_html = ""
    if featured:
        note_id = _note_catalog_id(featured, 0)
        title = esc(str(featured.get("title") or ""))
        href = esc(_note_href(site, note_id))
        date_s = esc(str(featured.get("date") or ""))
        meta = " · ".join(x for x in (note_id, date_s) if x)
        featured_html = (
            '      <article class="reading-featured" '
            f'data-record="{esc(note_id)}">\n'
            f'        <p class="catalogue-line meta">{meta}</p>\n'
            f'        <h3><a class="route-link" href="{href}">{title}</a></h3>\n'
            "      </article>\n"
        )
    compact_rows: list[str] = []
    for idx, row in enumerate(rest[:6], start=1):
        note_id = _note_catalog_id(row, idx)
        title = esc(str(row.get("title") or ""))
        href = esc(_note_href(site, note_id))
        date_s = esc(str(row.get("date") or ""))
        meta = " · ".join(x for x in (note_id, date_s) if x)
        compact_rows.append(
            f'        <li data-record="{esc(note_id)}">\n'
            f'          <a class="route-link" href="{href}">{title}</a>\n'
            f'          <span class="catalogue-line meta">{meta}</span>\n'
            f"        </li>"
        )
    compact_html = ""
    if compact_rows:
        compact_html = (
            '      <ul class="reading-index">\n'
            + "\n".join(compact_rows)
            + "\n      </ul>\n"
        )
    layout = f"{featured_html}{compact_html}"
    return (
        '    <section id="reading-room" class="library-slide reading-room" aria-labelledby="reading-room-heading">\n'
        '      <h2 id="reading-room-heading">Reading room</h2>\n'
        f"{layout}\n"
        "    </section>\n"
    )


def _operating_themes_html(site: dict) -> str:
    return ""


def _related_paths_html(
    site: dict, record_id: str, domain_key: str, domains: list[dict]
) -> str:
    lookup = _map_record_lookup(site)
    links: list[str] = []
    domain = next(
        (d for d in domains if str(d.get("id") or "").strip() == domain_key),
        None,
    )
    for rid in (domain or {}).get("related") or []:
        rid_s = str(rid).strip()
        if not rid_s or rid_s == record_id:
            continue
        meta = lookup.get(rid_s)
        if not meta or not meta.get("title"):
            continue
        label = str(meta.get("title") or rid_s)
        href = esc(with_base(site, f"/systems/#{rid_s}"))
        links.append(f'<a href="{href}">{esc(label)}</a>')
    links.append(_internal_route_link(site, "credentials", "Credentials"))
    links.append(_internal_route_link(site, "reading-room", "Notes"))
    if not links:
        return ""
    return (
        '            <p class="related-paths meta"><span class="related-paths-label">'
        f'Related</span> {" · ".join(links)}</p>\n'
    )


def _home_featured_systems_html(site: dict) -> str:
    rows: list[dict] = []
    for raw in site.get("home_selected") or []:
        if isinstance(raw, dict):
            rows.append(compose_home_selected_row(site, raw))
    if not rows:
        return ""
    cards: list[str] = []
    for row in rows[:3]:
        record_id = str(row.get("record_id") or "").strip()
        title = esc(str(row.get("title") or ""))
        problem = str(row.get("problem") or "").strip()
        context = esc(problem[:200] + ("…" if len(problem) > 200 else "")) if problem else ""
        href = esc(with_base(site, f"/systems/#{record_id}"))
        id_line = f'          <p class="record-id">{esc(record_id)}</p>\n' if record_id else ""
        context_line = f'          <p class="record-context">{context}</p>\n' if context else ""
        cards.append(
            f'        <article class="home-system-card" data-record="{esc(record_id)}">\n'
            f"{id_line}"
            f'          <h3><a href="{href}">{title}</a></h3>\n'
            f"{context_line}"
            f"        </article>"
        )
    systems_href = esc(with_base(site, "/systems/"))
    return (
        '    <section class="home-plate home-featured-systems" aria-labelledby="home-systems-heading">\n'
        '      <h2 id="home-systems-heading">Featured systems</h2>\n'
        '      <div class="home-system-cards">\n'
        + "\n".join(cards)
        + "\n      </div>\n"
        f'      <p class="links"><a href="{systems_href}">View all systems</a></p>\n'
        "    </section>\n"
    )


def _home_featured_notes_html(site: dict, export: dict) -> str:
    rows = _writing_rows(export)
    if not rows:
        return ""
    assigned = _unique_note_catalog_ids(rows)
    start = [(r, nid) for r, nid in assigned if r.get("start_here")]
    rest = [(r, nid) for r, nid in assigned if not r.get("start_here")]
    if not start:
        start, rest = assigned[:1], assigned[1:]
    featured_row, featured_id = start[0] if start else assigned[0]
    featured_title = esc(str(featured_row.get("title") or ""))
    featured_href = esc(_note_href(site, featured_id))
    featured_date = esc(str(featured_row.get("date") or ""))
    featured_dek = esc(str(featured_row.get("teaser") or "").strip())
    featured_meta = " · ".join(x for x in (featured_id, featured_date) if x)
    dek_html = f'        <p class="note-dek">{featured_dek}</p>\n' if featured_dek else ""
    featured_html = (
        '      <article class="reading-featured home-note-featured">\n'
        f'        <p class="catalogue-line meta">{featured_meta}</p>\n'
        f'        <h3><a class="route-link" href="{featured_href}">{featured_title}</a></h3>\n'
        f"{dek_html}"
        "      </article>\n"
    )
    compact_rows: list[str] = []
    for row, note_id in rest[:2]:
        title = esc(str(row.get("title") or ""))
        href = esc(_note_href(site, note_id))
        date_s = esc(str(row.get("date") or ""))
        meta = " · ".join(x for x in (note_id, date_s) if x)
        compact_rows.append(
            f'        <li data-record="{esc(note_id)}">\n'
            f'          <a class="route-link" href="{href}">{title}</a>\n'
            f'          <span class="catalogue-line meta">{meta}</span>\n'
            f"        </li>"
        )
    compact_html = ""
    if compact_rows:
        compact_html = (
            '      <ul class="reading-index home-notes-recent">\n'
            + "\n".join(compact_rows)
            + "\n      </ul>\n"
        )
    notes_href = esc(with_base(site, "/notes/"))
    return (
        '    <section class="home-plate home-featured-notes" aria-labelledby="home-notes-heading">\n'
        '      <h2 id="home-notes-heading">Notes</h2>\n'
        f"{featured_html}"
        f"{compact_html}"
        f'      <p class="links"><a href="{notes_href}">Browse notes index</a></p>\n'
        "    </section>\n"
    )


def _credentials_teaser_html(site: dict, export: dict) -> str:
    certs = [c for c in (export.get("certifications") or []) if isinstance(c, dict)]
    education = [e for e in (export.get("education") or []) if isinstance(e, dict)]
    if not certs and not education:
        return ""
    cert_count = len(certs)
    edu_count = len(education)
    summary_bits = []
    if cert_count:
        summary_bits.append(f"{cert_count} certification{'s' if cert_count != 1 else ''}")
    if edu_count:
        summary_bits.append(f"{edu_count} academic record{'s' if edu_count != 1 else ''}")
    summary = " · ".join(summary_bits)
    verify = verify_panel_html(site).replace("      ", "      ", 1)
    page = export.get("credentials") if isinstance(export.get("credentials"), dict) else {}
    order = page.get("order") or {}
    prof_ids = order.get("professional") or []
    cert_index = {str(c.get("id")): c for c in certs}
    featured = [cert_index[i] for i in prof_ids if i in cert_index][:4]
    if not featured:
        featured = certs[:4]
    preview_items: list[str] = []
    for row in featured:
        name = str(row.get("name") or "").strip()
        issuer = str(row.get("issuer") or "").strip()
        if not name:
            continue
        preview_items.append(
            "            <li>\n"
            f'              <span class="credentials-preview-name">{esc(name)}</span>\n'
            f'              <span class="credentials-preview-issuer meta">{esc(issuer)}</span>\n'
            "            </li>"
        )
    preview_html = ""
    if preview_items:
        preview_html = (
            '      <ul class="credentials-preview">\n'
            + "\n".join(preview_items)
            + "\n      </ul>\n"
        )
    edu_bits: list[str] = []
    for row in education[:3]:
        cred = str(row.get("credential") or "").strip()
        if cred:
            edu_bits.append(cred)
    edu_html = ""
    if edu_bits:
        edu_html = (
            f'      <p class="credentials-edu-preview meta">{esc(" · ".join(edu_bits))}</p>\n'
        )
    creds_href = esc(with_base(site, "/credentials/"))
    browse_html = (
        f'      <p class="links"><a href="{creds_href}">Browse full credentials catalogue</a></p>\n'
    )
    return (
        '    <section class="home-plate home-credentials-teaser" '
        'aria-labelledby="credentials-heading">\n'
        '      <h2 id="credentials-heading">Professional record</h2>\n'
        f'      <p class="record-context">Featured credentials from a catalogue of '
        f'{esc(summary)}.</p>\n'
        f"{preview_html}"
        f"{edu_html}"
        f"{verify}"
        f"{browse_html}"
        "    </section>\n"
    )


def _home_entry_grid_html(site: dict) -> str:
    routes = (
        ("Systems", "/systems/", "Case studies and architecture records"),
        ("Notes", "/notes/", "Publication index with NOTE-* IDs"),
        ("Credentials", "/credentials/", "Certifications and qualifications"),
    )
    cards: list[str] = []
    for label, path, desc in routes:
        href = esc(with_base(site, path))
        cards.append(
            f'        <a class="home-entry-card" href="{href}">\n'
            f'          <span class="home-entry-label">{esc(label)}</span>\n'
            f'          <span class="home-entry-desc">{esc(desc)}</span>\n'
            f"        </a>"
        )
    return (
        '        <nav class="home-entry-grid" aria-label="Explore the library">\n'
        + "\n".join(cards)
        + "\n        </nav>"
    )


def build_home(site: dict, export: dict) -> str:
    person = site["person"]
    location = str(person.get("location") or "").strip()
    platforms = [str(p) for p in (person.get("platforms") or []) if str(p).strip()][:4]

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

    atmosphere = _atmosphere_slot(site, "entrance")
    entrance_src = str(atmosphere.get("src") or "").strip()
    if entrance_src:
        src = esc(with_base(site, entrance_src))
        w = int(atmosphere.get("width") or 0)
        h = int(atmosphere.get("height") or 0)
        wh = f' width="{w}" height="{h}"' if w and h else ""
        obj_pos = esc(str(atmosphere.get("object_position") or "center center"))
        entrance_img = (
            f'      <div class="entrance-atmosphere" aria-hidden="true">\n'
            f'        <img class="entrance-photo" src="{src}" alt=""{wh} '
            f'decoding="async" fetchpriority="high" style="object-position: {obj_pos}" />\n'
            f'        <div class="entrance-scrim"></div>\n'
            f'        <div class="entrance-vignette"></div>\n'
            f"      </div>"
        )
    else:
        entrance_img = (
            '      <div class="entrance-atmosphere entrance-atmosphere--tokens" '
            'aria-hidden="true">\n'
            '        <div class="entrance-scrim"></div>\n'
            '        <div class="entrance-vignette"></div>\n'
            "      </div>"
        )

    catalog_html = ""
    if location:
        catalog_html = (
            f'        <p class="entrance-catalog">'
            f'<span class="entrance-catalog-dot" aria-hidden="true"></span>'
            f"RECORD · {esc(location.upper())}</p>\n"
        )

    thesis = esc(str(person.get("headline") or "").strip())
    lede = esc(str(person.get("tagline") or "").strip())
    current_html = _current_index_html(site, export)
    entry_grid = _home_entry_grid_html(site)
    philosophy_html = _philosophy_block_html(_about_data(site, export), home=True)
    hero = f"""    <section id="entrance" class="entrance hero home-hero" aria-labelledby="entrance-heading">
{entrance_img}
      <div class="entrance-copy hero-copy">
{catalog_html}        <h1 id="entrance-heading">{thesis}</h1>
        <p class="lede">{lede}</p>
{current_html}
{entry_grid}
{philosophy_html}{proof_html}
      </div>
    </section>
"""
    return (
        '    <div class="home-shell">\n'
        f"{hero}"
        f"{_home_competencies_html(site, export)}"
        f"{footer_html(site, compact=True)}"
        "    </div>"
    )


def _about_data(site: dict, export: dict) -> dict:
    about = export.get("about") if isinstance(export.get("about"), dict) else {}
    if not about:
        about = site.get("about") if isinstance(site.get("about"), dict) else {}
    return about


def _home_competency_item_html(row: dict) -> str:
    title = esc(str(row.get("title") or ""))
    body = esc(str((row.get("body") or "").strip()))
    title_html = (
        f'        <span class="home-competency-title">{title}</span>\n'
        if title
        else ""
    )
    return (
        f'      <li class="home-competency">\n'
        f"{title_html}"
        f'        <p class="home-competency-body">{body}</p>\n'
        f"      </li>"
    )


def _home_competencies_html(site: dict, export: dict) -> str:
    about = _about_data(site, export)
    items: list[str] = []
    for row in about.get("competencies") or []:
        if isinstance(row, dict):
            items.append(_home_competency_item_html(row))
    if not items:
        for bullet in (site.get("about") or {}).get("bullets") or []:
            items.append(
                '      <li class="home-competency">\n'
                f'        <p class="home-competency-body">{esc(bullet)}</p>\n'
                "      </li>"
            )
    if not items:
        return ""
    return (
        '    <section class="home-competencies" aria-labelledby="home-competencies-heading">\n'
        '      <h2 id="home-competencies-heading" class="home-competencies-label">Core competencies</h2>\n'
        '      <ul class="home-competency-list">\n'
        + "\n".join(items)
        + "\n      </ul>\n"
        "    </section>\n"
    )


def _philosophy_block_html(about: dict, *, home: bool = False) -> str:
    philosophy = str(about.get("philosophy") or "").strip()
    if not philosophy:
        return ""
    cls = "philosophy home-philosophy" if home else "philosophy"
    return (
        f'    <blockquote class="{cls}">\n'
        f"      <p>{esc(philosophy)}</p>\n"
        "    </blockquote>\n"
    )


def _link_label(url: str) -> str:
    u = url.lower()
    if "github.com" in u:
        return "GitHub"
    if "linkedin.com" in u:
        return "LinkedIn"
    if "medium.com" in u or "towardsdatascience.com" in u:
        return "Article"
    if "figma.com" in u:
        return "Figma deck"
    if "yzouyang.com" in u:
        return "Article archive"
    if "bit.ly" in u:
        return "Verify"
    return "Link"


def _project_item_html(row: dict) -> str:
    name = esc(row.get("name") or row.get("id") or "Project")
    hid = slugify(str(row.get("id") or row.get("name") or "project"))
    beats = case_beats_html(row, indent="        ")
    outcome = str(row.get("outcome") or row.get("impact") or row.get("description") or "").strip()
    scope = str(row.get("scope") or row.get("context") or "").strip()
    if scope and scope == outcome:
        scope = ""
    if not beats:
        outcome_html = f'        <p class="case-outcome">{esc(outcome)}</p>\n' if outcome else ""
        scope_html = f"        <p>{esc(scope)}</p>\n" if scope else ""
        beats = f"{outcome_html}{scope_html}"
    start = esc(row.get("start") or "")
    end = esc(row.get("end") or "present")
    tools = _curated_tools(row.get("tools"))
    tools_html = ""
    if tools:
        tools_html = (
            f'        <p class="case-tools meta">Tools: '
            f'{esc(", ".join(tools))}</p>\n'
        )
    links = urls_from_bullets(row.get("bullets"))
    link_html = ""
    if links:
        link_html = (
            '        <p class="links">'
            + " · ".join(
                f'<a class="external" href="{esc(u)}" target="_blank" rel="noopener noreferrer">'
                f"{esc(_link_label(u))}</a>"
                for u in links
            )
            + "</p>\n"
        )
    embed = str(row.get("embed") or "").strip()
    poster = str(row.get("poster") or "").strip()
    figma_link = next((u for u in links if "figma.com" in u.lower()), None)
    embed_html = ""
    if poster:
        embed_html = figma_embed_html(
            str(row.get("name") or "Deck"),
            embed or (figma_link or ""),
            figma_link,
            poster=poster,
            include_fallback=not bool(figma_link),
        )
    elif embed and not figma_link:
        embed_html = figma_embed_html(str(row.get("name") or "Deck"), embed, None)
    return (
        f"      <li>\n"
        f'        <h3 id="{esc(hid)}">{name}</h3>\n'
        f'        <p class="meta">{start} – {end}</p>\n'
        f"{beats}"
        f"{tools_html}"
        f"{link_html}"
        f"        {embed_html}\n"
        f"      </li>"
    )


def _case_tools_html(row: dict, indent: str = "      ") -> str:
    tools = _curated_tools(row.get("tools"))
    if not tools:
        return ""
    return (
        f'{indent}<p class="case-tools meta">Tools: '
        f'{esc(", ".join(tools))}</p>\n'
    )


def _enterprise_case_html(
    display_title: str,
    item_id: str,
    overlay: dict,
    fallback: dict,
    *,
    include_id: bool = True,
    include_heading: bool = True,
) -> str:
    beats = case_beats_html(overlay, indent="        ")
    if beats:
        body_inner = beats
    else:
        bullets = "\n".join(
            f"          <li>{esc(b)}</li>" for b in (fallback.get("bullets") or [])
        )
        body_inner = f'        <ul class="competency-list">\n{bullets}\n        </ul>\n'
    id_attr = f' id="{esc(item_id)}"' if item_id and include_id else ""
    heading_html = (
        f"          <h3{id_attr}>{esc(display_title)}</h3>\n" if include_heading else ""
    )
    return (
        "        <article class=\"proof-case\">\n"
        f"{heading_html}"
        f"{body_inner}"
        f"{_case_tools_html(overlay, indent='          ')}"
        "        </article>"
    )


def _map_record_panels_library_html(site: dict) -> str:
    domains = [d for d in (site.get("system_map") or []) if isinstance(d, dict)]
    lookup = _map_record_lookup(site)
    referenced: list[str] = []
    seen: set[str] = set()
    for domain in domains[:6]:
        for record_id in domain.get("related") or []:
            rid = str(record_id).strip()
            if rid and rid not in seen:
                seen.add(rid)
                referenced.append(rid)
    panels: list[str] = []
    for record_id in referenced:
        meta = lookup.get(record_id)
        if not meta or not meta.get("title"):
            continue
        body = _map_record_panel_body(site, record_id, meta, omit_title=True)
        if not body:
            continue
        domain_key = _record_domain_key(domains, record_id) or _system_record_domain_key(record_id)
        related_html = _related_paths_html(site, record_id, domain_key, domains)
        title = str(meta.get("title") or record_id).strip()
        inner = (
            '            <button type="button" class="library-record-back" '
            'data-library-back>Back to index</button>\n'
            f"{body}"
            f"{related_html}"
        )
        panels.append(
            library_panel_html(
                record_id,
                title,
                inner,
                level="h3",
                extra_attrs=(
                    f' data-record="{esc(record_id)}"'
                    f' data-kind="{esc(str(meta.get("kind") or "record"))}"'
                    f' data-domain="{esc(domain_key)}"'
                ),
            )
        )
    if not panels:
        return ""
    return "\n".join(panels)


def build_systems(site: dict, export: dict) -> str:
    return build_portfolio(site, export)


def build_systems_catalogue(site: dict, export: dict) -> str:
    return build_portfolio(site, export)


def build_portfolio(site: dict, export: dict) -> str:
    page = export.get("portfolio") if isinstance(export.get("portfolio"), dict) else {}
    lede = (page.get("lede") or "Selected PUBLIC projects.").strip()
    projects = [p for p in (export.get("projects") or []) if isinstance(p, dict)]
    copy_map = site.get("project_copy") if isinstance(site.get("project_copy"), dict) else {}
    section_copy = site.get("section_copy") if isinstance(site.get("section_copy"), dict) else {}
    by_section: dict[str, list] = {}
    for p in projects:
        by_section.setdefault(str(p.get("section") or "other"), []).append(p)

    panels: list[str] = []
    toc: list[dict] = []
    seen_parents: set[str] = set()
    parent_nodes: dict[str, dict] = {}
    parent_kicker_sent: set[str] = set()
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

    enterprise = page.get("enterprise_summaries") or {}
    ent_copy = site.get("enterprise_copy") if isinstance(site.get("enterprise_copy"), dict) else {}
    export_items = [
        item for item in (enterprise.get("items") or []) if isinstance(item, dict)
    ]
    used_overlay_ids: set[str] = set()
    if export_items or ent_copy:
        etitle = str(enterprise.get("title") or "Enterprise summaries")
        eid = unique_id(etitle)
        ent_node = {"id": eid, "label": etitle, "children": []}
        toc.append(ent_node)

        def append_enterprise_case(item_title: str, overlay_id: str, overlay: dict, fallback: dict) -> None:
            display_title = str(overlay.get("title") or item_title)
            item_id = str(overlay.get("heading_id") or overlay_id or "").strip()
            if not item_id:
                item_id = unique_id(display_title) if display_title else ""
            elif item_id not in used_ids:
                used_ids.add(item_id)
            if overlay_id:
                used_overlay_ids.add(overlay_id)
            if item_id:
                used_overlay_ids.add(item_id)
                ent_node["children"].append(
                    {"id": item_id, "label": display_title, "children": []}
                )
            case_html = _enterprise_case_html(
                display_title, item_id, overlay, fallback, include_heading=False
            )
            if item_id:
                body = (
                    '      <p class="section-kicker meta">Enterprise delivery</p>\n'
                    '      <div class="proof-deck">\n'
                    f"{case_html}\n"
                    "      </div>"
                )
                panels.append(library_panel_html(item_id, display_title, body, level="h3"))

        for item in export_items:
            item_title = str(item.get("title") or "")
            overlay_id, overlay = resolve_enterprise_overlay(item, ent_copy)
            append_enterprise_case(item_title, overlay_id, overlay, item)
        for key, overlay in ent_copy.items():
            if not isinstance(overlay, dict) or key in used_overlay_ids:
                continue
            append_enterprise_case(str(overlay.get("title") or key), key, overlay, {})

    for section in page.get("sections") or []:
        if not isinstance(section, dict):
            continue
        sid = str(section.get("id") or "")
        rows = by_section.pop(sid, [])
        if not rows and sid != "other":
            continue
        parent = section.get("parent")
        sc = section_copy.get(sid) if isinstance(section_copy.get(sid), dict) else {}
        title = str((sc or {}).get("title") or section.get("title") or sid)
        hid = unique_id(title)
        child_node = {"id": hid, "label": title, "children": []}
        public_kicker = "Public architectures — not enterprise delivery"

        intro_override = str((sc or {}).get("intro") or "").strip()
        intro = intro_override or (section.get("intro") or "").strip()
        child_parts: list[str] = []
        if intro:
            child_parts.append(f'      <p class="page-lede">{esc(intro)}</p>')
        child_parts.append(
            '      <ul class="item-list folio-deck">\n'
            + "\n".join(_project_item_html(_merge_project_copy(r, copy_map)) for r in rows)
            + "\n      </ul>"
        )
        footer_link = section.get("footer_link") or ""
        if footer_link:
            child_parts.append(
                f'      <p class="links"><a class="external" href="{esc(footer_link)}" target="_blank" '
                f'rel="noopener noreferrer">{esc(section.get("footer_label") or footer_link)}</a></p>'
            )
        outro = (section.get("outro") or "").strip()
        if outro:
            child_parts.append(f"      <p><em>{esc(outro)}</em></p>")
        child_inner = "\n".join(child_parts)
        panels.append(library_panel_html(hid, title, child_inner, level="h3"))

        if parent:
            parent_key = str(parent)
            if parent_key not in seen_parents:
                pid = unique_id(parent_key)
                parent_node = {"id": pid, "label": parent_key, "children": []}
                toc.append(parent_node)
                parent_nodes[parent_key] = parent_node
                seen_parents.add(parent_key)
            if parent_key not in parent_kicker_sent:
                kicker_block = f'      <p class="section-kicker meta">{esc(public_kicker)}</p>\n'
                panels[-1] = panels[-1].replace(
                    '<div class="library-panel-body">\n',
                    f'<div class="library-panel-body">\n{kicker_block}',
                    1,
                )
                parent_kicker_sent.add(parent_key)
            parent_nodes[parent_key]["children"].append(child_node)
        else:
            toc.append(child_node)

    for sid, rows in by_section.items():
        if not rows:
            continue
        title = sid.replace("_", " ").title()
        hid = unique_id(title)
        toc.append({"id": hid, "label": title, "children": []})
        inner = (
            '      <ul class="item-list folio-deck">\n'
            + "\n".join(_project_item_html(_merge_project_copy(r, copy_map)) for r in rows)
            + "\n      </ul>"
        )
        panels.append(library_section_panel(hid, title, inner))

    verify = page.get("verify") or {}
    if isinstance(verify, dict) and verify.get("items"):
        vtitle = str(verify.get("title") or "Verify")
        vid = unique_id(vtitle)
        toc.append({"id": vid, "label": vtitle, "children": []})
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
        inner = '      <ul class="competency-list">\n' + "\n".join(vitems) + "\n      </ul>"
        note = (verify.get("note") or "").strip()
        if note:
            inner += f"\n      <p><em>{esc(note)}</em></p>"
        panels.append(library_section_panel(vid, vtitle, inner))

    if not panels:
        panels.append(
            library_panel_html(
                "empty",
                "Systems",
                "      <p>No PUBLIC projects in export.</p>",
                hidden=False,
            )
        )
        toc.append({"id": "empty", "label": "Systems", "children": []})

    if panels and lede.strip():
        first = panels[0]
        lede_block = f'      <p class="page-lede">{esc(lede)}</p>\n'
        panels[0] = first.replace(
            '<div class="library-panel-body">\n',
            f'<div class="library-panel-body">\n{lede_block}',
            1,
        )

    return library_shell(
        site=site,
        title="Systems",
        overview_html="",
        toc=toc,
        panels=panels,
        strip_html=_library_strip_html(site, active="systems"),
        record_panels_html=_map_record_panels_library_html(site),
    )


def _parse_year_month(value: str) -> tuple[int, int] | None:
    raw = str(value or "").strip()
    if len(raw) >= 7 and raw[4] == "-":
        try:
            return int(raw[:4]), int(raw[5:7])
        except ValueError:
            return None
    if len(raw) >= 4 and raw[:4].isdigit():
        return int(raw[:4]), 12
    return None


def _education_is_ongoing(row: dict, *, today: date | None = None) -> bool:
    status = str(row.get("status") or "").strip().lower()
    if status in {"ongoing", "in_progress", "in progress", "studying"}:
        return True
    end = str(row.get("end") or "").strip()
    if not end or end.lower() in {"present", "ongoing", "in progress"}:
        return True
    parsed = _parse_year_month(end)
    if not parsed:
        return False
    now = today or date.today()
    end_year, end_month = parsed
    return (end_year, end_month) >= (now.year, now.month)


def _credentials_card_grid(cards: list[str]) -> str:
    if not cards:
        return ""
    return (
        '      <div class="credentials-featured-grid">\n'
        + "\n".join(cards)
        + "\n      </div>"
    )


def _cert_card_html(row: dict) -> str:
    name = esc(str(row.get("name") or ""))
    issuer = esc(str(row.get("issuer") or ""))
    issued = esc(str(row.get("issued") or ""))
    expires = esc(str(row.get("expires") or ""))
    primary, bitly = primary_and_short(urls_from_bullets(row.get("bullets")))
    verify_href = primary or bitly
    meta_bits: list[str] = []
    if issuer:
        meta_bits.append(issuer)
    if issued:
        meta_bits.append(f"issued {issued}")
    if expires:
        meta_bits.append(f"expires {expires}")
    verify_html = ""
    if verify_href:
        verify_html = (
            f'        <p class="links credential-card-links">'
            f'<a href="{esc(verify_href)}" target="_blank" rel="noopener noreferrer">Verify</a>'
            f"</p>\n"
        )
    return (
        f'      <article class="credential-card">\n'
        f'        <h3 class="credential-card-title">{name}</h3>\n'
        f'        <p class="meta credential-card-meta">{" · ".join(meta_bits)}</p>\n'
        f"{verify_html}"
        f"      </article>"
    )


def _edu_card_html(row: dict) -> str:
    cred = esc(row.get("credential") or "")
    inst = esc(row.get("institution") or "")
    start = esc(row.get("start") or "")
    end = esc(row.get("end") or "")
    ongoing = _education_is_ongoing(row)
    if ongoing:
        period = " – ".join(x for x in (start, "present") if x)
        status_html = (
            ' <span class="status-badge status-badge--ongoing">In progress</span>'
        )
    else:
        period = " – ".join(x for x in (start, end or "present") if x)
        status_html = ""
    meta_bits: list[str] = []
    if inst:
        meta_bits.append(inst + status_html)
    if period:
        meta_bits.append(period)
    links = urls_from_bullets(row.get("bullets"))
    link_html = ""
    if links:
        link_html = (
            f'        <p class="links credential-card-links">'
            + " · ".join(
                f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(_link_label(u))}</a>'
                for u in links
            )
            + "</p>\n"
        )
    return (
        f'      <article class="credential-card">\n'
        f'        <h3 class="credential-card-title">{cred}</h3>\n'
        f'        <p class="meta credential-card-meta">{" · ".join(meta_bits)}</p>\n'
        f"{link_html}"
        f"      </article>"
    )


def _certs_by_issuer_html(
    rows: list[dict], unique_id
) -> tuple[list[str], list[dict], list[tuple[str, str, str]]]:
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        issuer = str(row.get("issuer") or "Other").strip() or "Other"
        grouped.setdefault(issuer, []).append(row)
    out: list[str] = []
    children: list[dict] = []
    issuer_panels: list[tuple[str, str, str]] = []
    for issuer, group in grouped.items():
        iid = unique_id(issuer)
        children.append({"id": iid, "label": issuer, "children": []})
        list_html = _credentials_card_grid([_cert_card_html(r) for r in group])
        issuer_panels.append((iid, issuer, list_html))
        out.append(f'      <h3 class="issuer-group">{esc(issuer)}</h3>')
        out.append(list_html)
    return out, children, issuer_panels


def build_credentials(site: dict, export: dict) -> str:
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

    panels: list[str] = []
    toc: list[dict] = []
    used_ids: set[str] = set()

    overview_html = (
        f'      <p class="page-lede">{esc(lede)}</p>\n'
        f'      <p class="record-context">{len(certs)} certifications and '
        f"{len(education)} qualifications in the searchable catalogue — "
        "each entry includes an issuer verify link where available.</p>\n"
    )

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
            panels.append(
                library_section_panel(
                    hid,
                    title,
                    _credentials_card_grid([_edu_card_html(r) for r in rows]),
                )
            )
        else:
            rows = ordered(certs_by_cat.pop(sid, []), order.get(sid))
            if not rows:
                continue
            hid = unique_id(title)
            node = {"id": hid, "label": title, "children": []}
            toc.append(node)
            if sid == "professional":
                _html_parts, children, issuer_panels = _certs_by_issuer_html(rows, unique_id)
                node["children"] = children
                for iid, issuer, inner in issuer_panels:
                    panels.append(library_panel_html(iid, issuer, inner, level="h3"))
            else:
                panels.append(
                    library_section_panel(
                        hid,
                        title,
                        _credentials_card_grid([_cert_card_html(r) for r in rows]),
                    )
                )

    for sid, rows in list(certs_by_cat.items()):
        if rows:
            title = sid.replace("_", " ").title()
            hid = unique_id(title)
            toc.append({"id": hid, "label": title, "children": []})
            panels.append(
                library_section_panel(
                    hid,
                    title,
                    _credentials_card_grid([_cert_card_html(r) for r in rows]),
                )
            )
    for sid, rows in list(edu_by_cat.items()):
        if rows:
            title = sid.replace("_", " ").title()
            hid = unique_id(title)
            toc.append({"id": hid, "label": title, "children": []})
            panels.append(
                library_section_panel(
                    hid,
                    title,
                    _credentials_card_grid([_edu_card_html(r) for r in rows]),
                )
            )

    if not panels:
        panels.append(
            library_panel_html(
                "empty",
                "Professional record",
                "      <p>No PUBLIC credentials in export.</p>",
                hidden=False,
            )
        )
        toc.append({"id": "empty", "label": "Credentials", "children": []})

    return library_shell(
        site=site,
        title="Professional record",
        overview_html=overview_html,
        toc=toc,
        panels=panels,
        strip_html=_library_strip_html(site, active="credentials"),
        index_footer_html="",
    )


def _note_category(row: dict) -> str:
    return str(row.get("category") or "Essays").strip() or "Essays"


def _note_series(row: dict) -> str:
    return str(row.get("series") or "").strip()


def _note_date_sort_key(row: dict) -> tuple[str, str]:
    return (str(row.get("date") or ""), str(row.get("title") or ""))


def _notes_category_order(site: dict, categories: set[str]) -> list[str]:
    preferred = [str(c).strip() for c in (site.get("notes_category_order") or []) if str(c).strip()]
    ordered = [c for c in preferred if c in categories]
    ordered.extend(sorted(categories - set(ordered)))
    return ordered


def _note_index_label(row: dict, note_id: str) -> str:
    date_s = str(row.get("date") or "").strip()
    title = str(row.get("title") or "").strip()
    if len(title) > 48:
        title = title[:45].rstrip() + "…"
    if date_s and title:
        return f"{date_s} · {title}"
    return title or note_id


def _writing_note_panel_body(
    site: dict, row: dict, note_id: str, *, lede_html: str = ""
) -> str:
    date_s = esc(str(row.get("date") or ""))
    category = esc(_note_category(row))
    series = esc(_note_series(row))
    teaser = str(row.get("teaser") or "").strip()
    meta = " · ".join(x for x in (note_id, date_s) if x)
    taxonomy_bits = [f"<span class=\"note-category\">{category}</span>"]
    if series:
        taxonomy_bits.append(f'<span class="note-series">{series}</span>')
    taxonomy_html = (
        f'      <p class="note-taxonomy meta">{" · ".join(taxonomy_bits)}</p>\n'
    )
    dek = f'      <p class="note-dek">{esc(teaser)}</p>\n' if teaser else ""
    draft_banner = ""
    if row.get("preview_draft"):
        draft_banner = '      <p class="note-kicker meta">Draft preview — not in PUBLIC export</p>\n'
    body_md = str(row.get("body_md") or "").strip()
    body_html = ""
    if body_md:
        rendered = _markdown_to_html(body_md, note_id=note_id, site=site)
        if rendered:
            body_html = f'      <div class="note-body prose">{rendered}</div>\n'
    links_html = _writing_links_html(site, row)
    return (
        f"{lede_html}"
        f'      <article class="notes-entry">\n'
        f'        <p class="catalogue-line meta">{meta}</p>\n'
        f"{taxonomy_html}"
        f"{draft_banner}"
        f"{dek}"
        f"{body_html}"
        f"{links_html}"
        f"      </article>"
    )


def _append_note_panel(
    site: dict,
    *,
    row: dict,
    note_id: str,
    panels: list[str],
    lede_html: str,
) -> None:
    heading = str(row.get("title") or note_id).strip()
    panels.append(
        library_panel_html(
            note_id,
            esc(heading),
            _writing_note_panel_body(site, row, note_id, lede_html=lede_html),
            level="h2",
        )
    )


def build_perspectives(site: dict, export: dict) -> str:
    """Publication index — NOTE-* entries grouped by category, ordered by date."""
    rows = _writing_rows(export)
    assigned = _unique_note_catalog_ids(rows)
    lede_html = (
        "      <p class=\"page-lede\">Publication index with stable NOTE-* catalogue IDs — "
        "grouped by category, ordered by date within each topic. "
        "Essay bodies are on-site; Medium and LinkedIn remain live syndication copies.</p>\n"
    )

    by_category: dict[str, list[tuple[dict, str]]] = {}
    for row, note_id in assigned:
        by_category.setdefault(_note_category(row), []).append((row, note_id))

    toc: list[dict] = []
    panels: list[str] = []
    first_panel = True

    for category in _notes_category_order(site, set(by_category)):
        items = by_category.get(category) or []
        if not items:
            continue
        cat_id = slugify(category)
        cat_node: dict = {"id": cat_id, "label": category, "children": []}
        index_entries: list[tuple[str, str, str | None, list[tuple[dict, str]]]] = []

        by_series: OrderedDict[str, list[tuple[dict, str]]] = OrderedDict()
        standalone: list[tuple[dict, str]] = []
        for row, note_id in items:
            series = _note_series(row)
            if series:
                by_series.setdefault(series, []).append((row, note_id))
            else:
                standalone.append((row, note_id))

        for series, series_items in by_series.items():
            ordered = sorted(series_items, key=lambda pair: _note_date_sort_key(pair[0]))
            latest = max(_note_date_sort_key(row)[0] for row, _ in ordered)
            if len(ordered) > 1:
                index_entries.append((latest, "series", series, ordered))
            else:
                index_entries.append((latest, "note", None, ordered))

        for row, note_id in standalone:
            index_entries.append(
                (_note_date_sort_key(row)[0], "note", None, [(row, note_id)])
            )

        index_entries.sort(key=lambda entry: entry[0], reverse=True)

        for _, kind, series, group_items in index_entries:
            if kind == "series" and series:
                series_node = {
                    "id": slugify(f"{category}-{series}"),
                    "label": series,
                    "children": [],
                }
                for row, note_id in group_items:
                    panel_lede = lede_html if first_panel else ""
                    first_panel = False
                    _append_note_panel(
                        site,
                        row=row,
                        note_id=note_id,
                        panels=panels,
                        lede_html=panel_lede,
                    )
                    series_node["children"].append(
                        {
                            "id": note_id,
                            "label": _note_index_label(row, note_id),
                            "children": [],
                        }
                    )
                cat_node["children"].append(series_node)
            else:
                row, note_id = group_items[0]
                panel_lede = lede_html if first_panel else ""
                first_panel = False
                _append_note_panel(
                    site,
                    row=row,
                    note_id=note_id,
                    panels=panels,
                    lede_html=panel_lede,
                )
                cat_node["children"].append(
                    {
                        "id": note_id,
                        "label": _note_index_label(row, note_id),
                        "children": [],
                    }
                )

        toc.append(cat_node)

    if not panels:
        toc.append({"id": "empty", "label": "Notes", "children": []})
        panels.append(
            library_panel_html(
                "empty",
                "Notes",
                "      <p>No PUBLIC writing in export.</p>",
                hidden=False,
            )
        )

    return library_shell(
        site=site,
        title="Notes",
        overview_html="",
        toc=toc,
        panels=panels,
        strip_html=_library_strip_html(site, active="notes"),
    )


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

    export = _merge_preview_drafts(load_json(DATA / "export_public.json"))
    site["_export"] = export
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

    writing_rows = _writing_rows(export)
    note_assigned = _unique_note_catalog_ids(writing_rows)
    start_notes = [(r, nid) for r, nid in note_assigned if r.get("start_here")]
    if not start_notes:
        start_notes = note_assigned[:1]
    featured_note_row, featured_note_id = start_notes[0]

    pages = [
        (
            "index.html",
            "/",
            "Home",
            "Home",
            build_home(site, export),
            True,
            website_json_ld(site),
        ),
        (
            "systems/index.html",
            "/systems/",
            "Systems",
            "Systems",
            build_systems(site, export),
            True,
            "",
        ),
        (
            "notes/index.html",
            "/notes/",
            "Notes",
            "Notes",
            build_perspectives(site, export),
            True,
            article_json_ld(site, featured_note_row, featured_note_id),
        ),
        (
            "credentials/index.html",
            "/credentials/",
            "Credentials",
            "Credentials",
            build_credentials(site, export),
            True,
            "",
        ),
    ]
    library_rels = frozenset(
        {
            "systems/index.html",
            "notes/index.html",
            "credentials/index.html",
        }
    )
    for rel, path, title, active, body, pf, extra_head in pages:
        is_home = rel == "index.html"
        is_library = rel in library_rels
        write(
            DIST / rel,
            layout(
                site,
                title,
                active,
                body,
                pagefind=pf,
                path=path,
                deck_mode=False,
                header_search=is_home or is_library,
                library_route=is_library,
                home_route=is_home,
                extra_head=extra_head,
            ),
        )

    systems_target = with_base(site, "/systems/")
    catalogue_target = systems_target
    notes_target = with_base(site, "/notes/")
    home_target = with_base(site, "/")
    for rel_path, target, label in (
        ("portfolio/index.html", catalogue_target, "Systems"),
        ("perspectives/index.html", notes_target, "Notes"),
        ("systems/catalogue/index.html", catalogue_target, "Systems"),
        ("about/index.html", home_target, "Home"),
        ("contact/index.html", home_target, "Home"),
        ("career-journey/index.html", home_target, "Home"),
        ("blog/index.html", notes_target, "Notes"),
    ):
        write(
            DIST / rel_path,
            f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0;url={esc(target)}" />
  <link rel="canonical" href="{esc(target)}" />
  <title>{esc(label)}</title>
</head>
<body>
  <p>Moved to <a href="{esc(target)}">{esc(target)}</a>.</p>
</body>
</html>
""",
        )

    for row in _writing_rows(export):
        synd = row.get("syndication") if isinstance(row.get("syndication"), dict) else {}
        wp = str(synd.get("wordpress") or "").strip()
        if not wp:
            continue
        slug = wp.rstrip("/").split("/")[-1]
        if not slug:
            continue
        note_id = _note_catalog_id(row, 0)
        target = f"{notes_target}#{note_id}"
        write(
            DIST / slug / "index.html",
            f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0;url={esc(target)}" />
  <link rel="canonical" href="{esc(target)}" />
  <title>{esc(str(row.get("title") or slug))}</title>
</head>
<body>
  <p>Moved to <a href="{esc(target)}">{esc(target)}</a>.</p>
</body>
</html>
""",
        )

    work_target = catalogue_target
    write(
        DIST / "work" / "index.html",
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0;url={esc(work_target)}" />
  <link rel="canonical" href="{esc(canonical_url(site, "/systems/"))}" />
  <title>Work</title>
</head>
<body>
  <p>Selected work lives at <a href="{esc(work_target)}">/systems/</a>.</p>
</body>
</html>
""",
    )

    write(DIST / "styles.css", assemble_styles())
    chrome_js = SRC / "chrome.js"
    if chrome_js.is_file():
        shutil.copyfile(chrome_js, DIST / "chrome.js")
    assets_src = ROOT / "assets"
    if assets_src.is_dir():
        shutil.copytree(assets_src, DIST / "assets", dirs_exist_ok=True)
    diy = (site.get("analytics") or {}).get("diy") or {}
    if diy.get("enabled") and (SRC / "track.js").is_file():
        shutil.copyfile(SRC / "track.js", DIST / "track.js")
    notes_assets = ROOT / "assets" / "notes"
    if notes_assets.is_dir():
        shutil.copytree(notes_assets, DIST / "assets" / "notes", dirs_exist_ok=True)
    (DIST / "data").mkdir(exist_ok=True)
    shutil.copyfile(DATA / "export_public.json", DIST / "data" / "export_public.json")
    site_out = {k: v for k, v in site.items() if k != "_export"}
    write(DIST / "data" / "site.json", json.dumps(site_out, indent=2) + "\n")

    base = site["base_path"]
    redirects = f"""{base}/about {base}/ 301
{base}/about/ {base}/ 301
{base}/systems {base}/systems/ 301
{base}/systems/catalogue {base}/systems/ 301
{base}/systems/catalogue/ {base}/systems/ 301
{base}/notes {base}/notes/ 301
{base}/portfolio {base}/systems/ 301
{base}/portfolio/ {base}/systems/ 301
{base}/work {base}/systems/ 301
{base}/work/ {base}/systems/ 301
{base}/perspectives {base}/notes/ 301
{base}/perspectives/ {base}/notes/ 301
{base}/credentials {base}/credentials/ 301
{base}/contact {base}/ 301
{base}/contact/ {base}/ 301
{base}/career-journey {base}/ 301
{base}/career-journey/ {base}/ 301
{base}/blog {base}/notes/ 301
{base}/blog/ {base}/notes/ 301
"""
    write(DIST / "_redirects", redirects)

    print(f"built {len(pages)} pages + work redirect -> {DIST} (base_path={base or '/'})")

    if not args.skip_pagefind:
        run_pagefind()


if __name__ == "__main__":
    main()
