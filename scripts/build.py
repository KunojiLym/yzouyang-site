#!/usr/bin/env python3
"""Build static Phase 1 pages from data/export_public.json + data/site.json."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"
SRC = ROOT / "src"


def esc(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


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


def nav_html(site: dict, active: str) -> str:
    parts: list[str] = []
    for item in site.get("nav") or []:
        label = esc(item.get("label", ""))
        href = esc(item.get("href", "#"))
        external = bool(item.get("external"))
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
        chunks.append(
            f'  <script defer src="/track.js" data-collect-url="{collect}" '
            f'data-honor-dnt="{honor}"></script>'
        )

    return "\n".join(chunks)


def layout(site: dict, title: str, active: str, body: str, *, pagefind: bool = False) -> str:
    person = site["person"]
    brand = esc(person.get("brand", "yzouyang"))
    page_title = f"{esc(title)} — {brand}"
    pf_attr = ' data-pagefind-body' if pagefind else ""
    head_analytics = analytics_head(site)
    body_analytics = analytics_body(site, active)
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
  <link rel="stylesheet" href="/styles.css" />
  <link rel="stylesheet" href="/pagefind/pagefind-ui.css" />
{head_analytics}
</head>
<body>
  <header class="site-header">
    <p class="brand"><a href="/">{brand}</a></p>
    <nav class="site-nav" aria-label="Primary">
      {nav_html(site, active)}
    </nav>
  </header>
  <main class="page"{pf_attr}>
{body}
  </main>
  <footer class="site-footer">
    <p>Static migration of yzouyang.com — Phase 1 pages from PUBLIC export.</p>
    <p>Writing remains on WordPress / Medium / LinkedIn until C2b.</p>
  </footer>
  <script src="/pagefind/pagefind-ui.js" type="text/javascript"></script>
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


def build_home(site: dict) -> str:
    person = site["person"]
    return f"""    <section class="hero">
      <h1>{esc(person['full_name'])}</h1>
      <p class="subtitle">{esc(person['headline'])}</p>
      <p class="lede">{esc(person['tagline'])}</p>
      <div class="cta-row">
        <a class="btn btn-primary" href="/contact/">Contact</a>
        <a class="btn" href="/about/">About</a>
        <a class="btn" href="/credentials/">Credentials</a>
        <a class="btn" href="/portfolio/">Portfolio</a>
      </div>
    </section>
"""


def build_about(site: dict, export: dict) -> str:
    about = site["about"]
    bullets = "\n".join(f"        <li>{esc(b)}</li>" for b in about.get("bullets") or [])
    exp = export.get("experiences") or []
    exp_items = []
    for row in exp[:3]:
        if not isinstance(row, dict):
            continue
        org = esc(row.get("organization") or row.get("org") or "")
        title = esc(row.get("title") or "")
        start = esc(row.get("start") or "")
        end = esc(row.get("end") or "present")
        exp_items.append(
            f'      <li><h2>{title}</h2><p class="meta">{org} · {start} – {end}</p>'
            f"<p>{esc(row.get('summary') or '')}</p></li>"
        )
    return f"""    <h1>About</h1>
    <p class="page-lede">{esc(about.get('lede', ''))}</p>
    <ul>
{bullets}
    </ul>
    <h2 style="font-family:var(--font-display);margin-top:2.5rem">Recent experience</h2>
    <ul class="item-list">
{chr(10).join(exp_items) if exp_items else "      <li>No PUBLIC experiences in export.</li>"}
    </ul>
"""


def build_portfolio(site: dict, export: dict) -> str:
    short = esc(site["external"].get("portfolio_short", ""))
    items = []
    for row in export.get("projects") or []:
        if not isinstance(row, dict):
            continue
        name = esc(row.get("name") or row.get("id") or "Project")
        desc = esc(row.get("description") or "")
        start = esc(row.get("start") or "")
        end = esc(row.get("end") or "present")
        links = urls_from_bullets(row.get("bullets"))
        link_html = ""
        if links:
            link_html = (
                '<p class="links">'
                + " · ".join(
                    f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(u)}</a>'
                    for u in links
                )
                + "</p>"
            )
        items.append(
            f"      <li>\n"
            f"        <h2>{name}</h2>\n"
            f'        <p class="meta">{start} – {end}</p>\n'
            f"        <p>{desc}</p>\n"
            f"        {link_html}\n"
            f"      </li>"
        )
    return f"""    <div id="search"></div>
    <h1>Portfolio</h1>
    <p class="page-lede">Selected PUBLIC projects from the personal-content export. Short link: <a href="{short}" target="_blank" rel="noopener noreferrer">{short}</a></p>
    <ul class="item-list">
{chr(10).join(items) if items else "      <li>No PUBLIC projects in export.</li>"}
    </ul>
"""


def build_credentials(site: dict, export: dict) -> str:
    short = esc(site["external"].get("credentials_short", ""))
    items = []
    for row in export.get("certifications") or []:
        if not isinstance(row, dict):
            continue
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
        items.append(
            f"      <li>\n"
            f"        <h2>{name}</h2>\n"
            f'        <p class="meta">{issuer} · issued {issued}'
            + (f" · expires {expires}" if expires else "")
            + "</p>\n"
            f"        {link_html}\n"
            f"      </li>"
        )
    return f"""    <div id="search"></div>
    <h1>Credentials &amp; Verifications</h1>
    <p class="page-lede">PUBLIC certifications with canonical verify URLs. Short link: <a href="{short}" target="_blank" rel="noopener noreferrer">{short}</a></p>
    <ul class="item-list">
{chr(10).join(items) if items else "      <li>No PUBLIC certifications in export.</li>"}
    </ul>
"""


def build_contact(site: dict) -> str:
    contact = site["contact"]
    ext = site["external"]
    return f"""    <h1>Contact</h1>
    <p class="page-lede">{esc(contact.get('note', ''))}</p>
    <ul class="item-list">
      <li>
        <h2>Email</h2>
        <p><a href="mailto:{esc(contact['email'])}">{esc(contact['email'])}</a></p>
      </li>
      <li>
        <h2>Phone</h2>
        <p><a href="tel:{esc(contact['phone'].replace(' ', ''))}">{esc(contact['phone'])}</a></p>
      </li>
      <li>
        <h2>Elsewhere</h2>
        <p class="links">
          <a class="external" href="{esc(ext['linkedin'])}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
          <a class="external" href="{esc(ext['medium'])}" target="_blank" rel="noopener noreferrer">Medium</a>
          <a class="external" href="{esc(ext['github'])}" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a class="external" href="{esc(ext['blog'])}" target="_blank" rel="noopener noreferrer">Blog (WordPress)</a>
        </p>
      </li>
    </ul>
"""


def main() -> None:
    site = load_json(DATA / "site.json")
    export = load_json(DATA / "export_public.json")
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    pages = [
        ("index.html", "Home", "Home", build_home(site), False),
        ("about/index.html", "About", "About", build_about(site, export), False),
        ("portfolio/index.html", "Portfolio", "Portfolio", build_portfolio(site, export), True),
        (
            "credentials/index.html",
            "Credentials",
            "Credentials",
            build_credentials(site, export),
            True,
        ),
        ("contact/index.html", "Contact", "Contact", build_contact(site), False),
    ]
    for rel, title, active, body, pf in pages:
        write(DIST / rel, layout(site, title, active, body, pagefind=pf))

    shutil.copyfile(SRC / "styles.css", DIST / "styles.css")
    diy = (site.get("analytics") or {}).get("diy") or {}
    if diy.get("enabled") and (SRC / "track.js").is_file():
        shutil.copyfile(SRC / "track.js", DIST / "track.js")
    # Keep source data in dist for transparency / future client use
    (DIST / "data").mkdir(exist_ok=True)
    shutil.copyfile(DATA / "export_public.json", DIST / "data" / "export_public.json")
    shutil.copyfile(DATA / "site.json", DIST / "data" / "site.json")

    # SPA-style trailing-slash helpers for Pages
    redirects = """/about /about/ 301
/portfolio /portfolio/ 301
/credentials /credentials/ 301
/contact /contact/ 301
"""
    write(DIST / "_redirects", redirects)

    print(f"built {len(pages)} pages -> {DIST}")


if __name__ == "__main__":
    main()
