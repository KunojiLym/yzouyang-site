#!/usr/bin/env python3
"""Contract checks against built dist/ (run after scripts/build.py)."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from build import (
    DeployBaseError,
    _beat_value_html,
    _format_note_date,
    _inline_markdown,
    _markdown_to_html,
    _note_asset_href,
    _note_index_title,
    _redirect_document,
    _render_image_block,
    _robots_noindex_head,
    _writing_note_panel_body,
    figma_embed_html,
    layout,
    normalize_base,
    og_image_dimensions,
    person_json_ld,
    resolve_enterprise_overlay,
    resolve_site_base_path,
    site_origin,
    website_json_ld,
    with_base,
)
from launch_facts import LOCKED_PROOF_TEXT, launch_fact_errors
from note_figures import NoteFigureContext, local_image_size, resolve_note_alt

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


def html_ul_block(html: str, class_name: str) -> str:
    match = re.search(
        rf'<ul class="{re.escape(class_name)}"[^>]*>(.*?)</ul>',
        html,
        re.DOTALL,
    )
    return match.group(1) if match else ""


def infer_base_path_from_dist() -> str:
    index = DIST / "index.html"
    if not index.is_file():
        return ""
    home = index.read_text(encoding="utf-8")
    match = re.search(r'href="([^"]*)/styles\.css"', home)
    if not match:
        return ""
    return normalize_base(match.group(1))


def resolve_site_base(site: dict) -> dict:
    merged = dict(site)
    if os.environ.get("SITE_BASE_PATH") is not None:
        merged["base_path"] = os.environ["SITE_BASE_PATH"]
    else:
        merged["base_path"] = infer_base_path_from_dist()
    merged["base_path"] = normalize_base(merged.get("base_path", ""))
    return merged


def href_attr(site: dict, path: str) -> str:
    return f'href="{with_base(site, path)}"'


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


def assert_note_asset_href() -> None:
    site = {"base_path": ""}
    note_id = "NOTE-2025-014"
    cases = {
        "assets/01.jpg": "/assets/notes/NOTE-2025-014/01.jpg",
        "assets/NOTE-2025-014/01.jpg": "/assets/notes/NOTE-2025-014/01.jpg",
        "assets/writing/NOTE-2025-014/01.jpg": "/assets/notes/NOTE-2025-014/01.jpg",
        "assets/notes/NOTE-2025-014/01.jpg": "/assets/notes/NOTE-2025-014/01.jpg",
        "/assets/01.jpg": "/assets/notes/NOTE-2025-014/01.jpg",
        "writing/assets/01.jpg": "/assets/notes/NOTE-2025-014/01.jpg",
    }
    for src, expected in cases.items():
        got = _note_asset_href(site, note_id, src)
        if got != expected:
            fail(f"_note_asset_href({src!r}) == {got!r}, expected {expected!r}")
    html = _inline_markdown("![chart](/assets/01.jpg)", note_id=note_id, site=site)
    if 'src="/assets/notes/NOTE-2025-014/01.jpg"' not in html:
        fail(f"inline image /assets/01.jpg mapped incorrectly: {html}")
    html = _inline_markdown("![chart](writing/assets/01.jpg)", note_id=note_id, site=site)
    if 'src="/assets/notes/NOTE-2025-014/01.jpg"' not in html:
        fail(f"inline image writing/assets/01.jpg mapped incorrectly: {html}")
    html = _inline_markdown(
        "![chart](https://i0.wp.com/www.yzouyang.com/wp-content/uploads/x.png?fit=700%2C510&ssl=1)",
        note_id=note_id,
        site=site,
    )
    if "&amp;amp;" in html:
        fail(f"image src was double-escaped: {html}")
    if 'src="https://i0.wp.com/www.yzouyang.com/wp-content/uploads/x.png?fit=700%2C510&amp;ssl=1"' not in html:
        fail(f"image query string lost a single &amp; escape: {html}")


def assert_note_heading_anchors() -> None:
    from build import _inarticle_toc_from_md, _markdown_to_html

    site = {"base_path": ""}
    md = """Table Of Contents

- [TL;DR](#1-tldr)
- [I. Setting up Databricks Free Edition account](#2-i-setting-up-databricks-free-edition-account)

## TL;DR

Summary.

## I. Setting up Databricks Free Edition account

Body.
"""
    html = _markdown_to_html(md, note_id="NOTE-2025-012", site=site)
    if 'id="1-tldr"' not in html:
        fail("TOC heading must render Medium-style id on matching h3")
    if 'id="2-i-setting-up-databricks-free-edition-account"' not in html:
        fail("TOC heading must map roman-numeral section to Medium anchor id")
    if "Table Of Contents" in html:
        fail("inline Table Of Contents must not render in note body")
    if 'href="#1-tldr"' in html:
        fail("inline TOC list links must not render in note body")
    if 'class="note-back-top"' in html:
        fail("back-to-top must live in the section menu, not inline on headings")
    if 'note-section-heading--major' not in html:
        fail("major section headings must use tier class")
    md_nested = """## Major

Intro.

#### Minor bit

Detail.
"""
    nested_html = _markdown_to_html(md_nested, note_id="NOTE-x", site=site)
    if 'note-section-heading--minor' not in nested_html:
        fail("h4 headings must render as minor section tier")
    nested_toc = _inarticle_toc_from_md(md_nested)
    if not nested_toc or not nested_toc[0].get("children"):
        fail("heading fallback TOC must nest h4 under h3")
    plain = _markdown_to_html("## Fallback heading\n", note_id="NOTE-x", site=site)
    if 'id="fallback-heading"' not in plain:
        fail("headings without TOC must slugify to stable ids")


def assert_note_cover_html() -> None:
    site = {"base_path": ""}
    row = {
        "title": "Example",
        "images": [
            {
                "path": "assets/NOTE-2025-012/cover.webp",
                "alt": "Databricks architecture overview",
                "role": "cover",
            }
        ],
    }
    html = _writing_note_panel_body(site, row, "NOTE-2025-012")
    if 'class="note-cover"' not in html:
        fail("writing panel must render cover image when images[] has role=cover")
    if 'src="/assets/notes/NOTE-2025-012/cover.webp"' not in html:
        fail("cover image must map to vendored /assets/notes/ path")


def assert_note_prose_blocks() -> None:
    from build import _markdown_to_html

    site = {"base_path": ""}
    expand_md = (
        "Expand to see screencap of **DISCOVERY** tab\n"
        "![](assets/NOTE-2025-011/01.png)Discovery tab caption\n\n"
        "- bullet after fold"
    )
    expand_html = _markdown_to_html(expand_md, note_id="NOTE-2025-011", site=site)
    if 'class="note-expand"' not in expand_html:
        fail("Expand to see lines must render as note-expand details")
    if "<summary" not in expand_html or "DISCOVERY" not in expand_html:
        fail("note-expand summary must preserve expand label")
    if 'class="note-figure"' not in expand_html:
        fail("note-expand body must render block figures")
    if expand_html.index("note-expand") < expand_html.index("note-figure"):
        pass
    elif "note-figure" not in expand_html:
        fail("note-expand must wrap following image lines")

    code_md = (
        "Pattern:\n\n```\n"
        "Content_{date start in YYYY-MM-DD}_{ProfileName}.xlsx\n"
        "```\n"
    )
    code_html = _markdown_to_html(code_md, note_id="NOTE-2025-011", site=site)
    if 'class="note-code"' not in code_html:
        fail("fenced code blocks must use note-code pre class")
    if "note-code-gutter" not in code_html or "note-code-line" not in code_html:
        fail("fenced code blocks must render line numbers and preserved indentation")
    if 'class="note-code-block"' not in code_html:
        fail("fenced code must render note-code-block markup")

    quote_md = "> The pipeline should fail closed.\n> Always verify inputs.\n\nNext para"
    quote_html = _markdown_to_html(quote_md, note_id="NOTE-2025-011", site=site)
    if 'class="note-blockquote"' not in quote_html:
        fail("markdown blockquotes must render note-blockquote")
    if "fail closed" not in quote_html:
        fail("note-blockquote must preserve quoted text")

    wrapped_md = (
        "[!\\[\\](https://i0.wp.com/www.yzouyang.com/wp-content/uploads/a.png?fit=1&ssl=1)]"
        "(https://i0.wp.com/www.yzouyang.com/wp-content/uploads/a.png?ssl=1)Caption"
    )
    wrapped_html = _markdown_to_html(wrapped_md, note_id="NOTE-2025-011", site=site)
    if 'class="note-figure"' not in wrapped_html:
        fail("link-wrapped markdown images must unwrap to note-figure blocks")

    image_md = "Intro\n\n![](assets/NOTE-2025-011/02.png)Caption line\n\nNext para"
    image_html = _markdown_to_html(image_md, note_id="NOTE-2025-011", site=site)
    if 'class="note-figure"' not in image_html:
        fail("standalone markdown image lines must render note-figure blocks")
    if "<p>Intro</p>" not in image_html:
        fail("image block must not merge preceding paragraph text")


def assert_inarticle_toc_sidebar() -> None:
    from build import _inarticle_toc_attr, _inarticle_toc_from_md

    md = """Table Of Contents

- [TL;DR](#1-tldr)
  - [Nested](#nested-bit)
- [Section two](#section-two)

## TL;DR

Summary.

## Section two

Body.
"""
    tree = _inarticle_toc_from_md(md)
    if len(tree) != 2:
        fail(f"in-article TOC tree must have two top-level entries, got {len(tree)}")
    if not tree[0].get("children"):
        fail("in-article TOC must preserve nested children from embedded TOC")
    attr = _inarticle_toc_attr(md)
    if 'data-inarticle-toc="' not in attr:
        fail("_inarticle_toc_attr must emit data-inarticle-toc on note panels")


def assert_library_index_controls() -> None:
    notes = (DIST / "notes" / "index.html").read_text(encoding="utf-8")
    for marker in (
        "library-index-header",
        "library-index-control",
        "library-index-pin",
        "library-index-control-icon",
        "library-index-rail",
        "library-index-drawer",
    ):
        if marker not in notes:
            fail(f"notes library index missing {marker}")
    if 'data-inarticle-toc="' not in notes:
        fail("notes panels must include data-inarticle-toc for sidebar heading navigation")
    if 'library-index-group--depth-0' not in notes:
        fail("notes index must mark top-level category groups for sticky TOC headers")


def assert_format_note_date() -> None:
    if _format_note_date("2025-12-22") != "22 Dec 2025":
        fail("_format_note_date must render full publication dates")
    if _format_note_date("2026-05") != "May 2026":
        fail("_format_note_date must still support month-only fallback")


def assert_writing_rows_preserve_images() -> None:
    export = {
        "writing": [
            {
                "id": "NOTE-2026-007-2",
                "title": "Example",
                "images": [{"path": "assets/NOTE-2026-007-2/cover.png", "role": "cover"}],
            }
        ]
    }
    from build import _writing_rows

    row = _writing_rows(export)[0]
    if not row.get("images"):
        fail("_writing_rows must preserve export images metadata for cover rendering")


def _meta(html: str, *, prop: str = "", name: str = "") -> str:
    if prop:
        match = re.search(
            rf'<meta property="{re.escape(prop)}" content="([^"]*)"',
            html,
        )
    else:
        match = re.search(rf'<meta name="{re.escape(name)}" content="([^"]*)"', html)
    return match.group(1) if match else ""


def _canonical(html: str) -> str:
    match = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    return match.group(1) if match else ""


def _json_ld_urls(html: str) -> list[str]:
    urls: list[str] = []
    for match in re.finditer(
        r'<script type="application/ld\+json">(\{.*?\})</script>',
        html,
    ):
        data = json.loads(match.group(1))
        url = data.get("url")
        if isinstance(url, str):
            urls.append(url)
    return urls


def _with_env(updates: dict[str, str | None], fn) -> None:
    saved: dict[str, str | None] = {}
    for key, value in updates.items():
        saved[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    try:
        fn()
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _site_for_preview(mode: bool) -> dict:
    raw = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
    raw.setdefault("deploy", {})["preview_mode"] = mode
    raw["base_path"] = resolve_site_base_path(raw, explicit=None, explicit_set=False)
    return raw


def _assert_rendered_head(site: dict, *, robots: str, origin: str) -> None:
    page = layout(
        site,
        "Home",
        "Home",
        "    <p>Home</p>\n",
        path="/",
        extra_head=website_json_ld(site),
    )
    redirect = _redirect_document(site, "/systems/", "Systems", "  <p>Moved.</p>")
    found_robots = _meta(page, name="robots")
    if found_robots != robots:
        fail(f"rendered robots {found_robots!r} != {robots!r}")
    redirect_robots = _meta(redirect, name="robots")
    if redirect_robots != robots:
        fail(f"redirect robots {redirect_robots!r} != {robots!r}")
    canonical = _canonical(page)
    if canonical != origin + "/":
        fail(f"canonical {canonical!r} != {origin}/")
    if _canonical(redirect) != origin + "/systems/":
        fail(f"redirect canonical {_canonical(redirect)!r} is not {origin}/systems/")
    if _meta(page, prop="og:url") != canonical:
        fail("og:url must match canonical")
    og_image = _meta(page, prop="og:image")
    if og_image != origin + "/assets/og/og-default.png":
        fail(f"og:image {og_image!r} is not on {origin}")
    urls = _json_ld_urls(page)
    if origin + "/" not in urls:
        fail(f"JSON-LD url missing {origin}/ in {urls}")
    person = person_json_ld(site)
    if '"image":"' + origin + '/assets/og/og-default.png"' not in person:
        fail("JSON-LD Person.image must stay on the OG card for this origin")
    styles = re.search(r'href="([^"]*)/styles\.css"', page)
    if not styles:
        fail("rendered page missing styles.css")
    prefix = normalize_base(styles.group(1))
    expected_base = normalize_base(site.get("base_path", ""))
    if prefix != expected_base:
        fail(f"asset prefix {prefix!r} != base_path {expected_base!r}")
    if robots == "" and prefix and not origin.endswith(prefix):
        fail("live canonical origin and asset prefix disagree")


def assert_deploy_preview_contract() -> None:
    try:
        _robots_noindex_head()  # type: ignore[call-arg]
    except TypeError:
        pass
    else:
        fail("_robots_noindex_head requires site")

    preview = _site_for_preview(True)
    live = _site_for_preview(False)
    if preview["base_path"] != "/yzouyang-site":
        fail("preview base_path must be derived from preview_origin")
    if live["base_path"] != "":
        fail("live base_path must be derived from the public origin")
    if resolve_site_base_path(preview, explicit="", explicit_set=True) != "":
        fail("empty SITE_BASE_PATH must stay the local/e2e exception while preview is on")
    try:
        resolve_site_base_path(live, explicit="/yzouyang-site", explicit_set=True)
    except DeployBaseError:
        pass
    else:
        fail("preview_mode off must reject a leftover /yzouyang-site base path")
    try:
        resolve_site_base_path(preview, explicit="/elsewhere", explicit_set=True)
    except DeployBaseError:
        pass
    else:
        fail("a preview base path that is not the origin path must fail")

    preview_origin = site_origin(preview)
    live_origin = site_origin(live)
    _assert_rendered_head(preview, robots="noindex, follow", origin=preview_origin)
    _with_env(
        {"SITE_UAT_BUILD": None, "PREVIEW_INCLUDE_DRAFTS": None},
        lambda: _assert_rendered_head(live, robots="", origin=live_origin),
    )

    def assert_strict(site: dict, origin: str) -> None:
        _assert_rendered_head(site, robots="noindex, nofollow", origin=origin)

    _with_env(
        {"SITE_UAT_BUILD": "1", "PREVIEW_INCLUDE_DRAFTS": None},
        lambda: assert_strict(preview, preview_origin),
    )
    _with_env(
        {"SITE_UAT_BUILD": None, "PREVIEW_INCLUDE_DRAFTS": "1"},
        lambda: assert_strict(preview, preview_origin),
    )
    _with_env(
        {"SITE_UAT_BUILD": "1", "PREVIEW_INCLUDE_DRAFTS": None},
        lambda: assert_strict(live, live_origin),
    )

    size = og_image_dimensions()
    if size != (1200, 630):
        fail(f"og:image dimensions {size} must come from the PNG, expected 1200x630")
    sample = layout(preview, "Home", "Home", "    <p>Home</p>\n", path="/")
    if 'property="og:image:width" content="1200"' not in sample:
        fail("og:image:width must use the measured PNG width")
    if 'property="og:image:height" content="630"' not in sample:
        fail("og:image:height must use the measured PNG height")

    def assert_not_found_head(site: dict) -> None:
        page = layout(
            site,
            "Not in the catalogue",
            "404",
            "    <p>Missing</p>\n",
            path="/404.html",
        )
        if _meta(page, name="robots") != "noindex, nofollow":
            fail(f"404 robots {_meta(page, name='robots')!r} must always be noindex, nofollow")
        if _canonical(page):
            fail("404 must not emit a canonical")
        if _meta(page, prop="og:url"):
            fail("404 must not emit og:url")

    assert_not_found_head(preview)
    assert_not_found_head(live)


def _jpeg(marker: int, width: int, height: int, *, prefix: bytes = b"") -> bytes:
    body = bytes([8]) + height.to_bytes(2, "big") + width.to_bytes(2, "big") + bytes([1, 1, 0x11, 0])
    segment = bytes([0xFF, marker]) + (len(body) + 2).to_bytes(2, "big") + body
    return b"\xff\xd8" + prefix + segment + b"\xff\xd9"


def assert_local_image_size() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        png = root / "card.png"
        # Signature, then IHDR length/type so width and height sit at bytes 16 and 20.
        png.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + (13).to_bytes(4, "big")
            + b"IHDR"
            + (1200).to_bytes(4, "big")
            + (630).to_bytes(4, "big")
            + bytes(5)
        )
        if local_image_size(png) != (1200, 630):
            fail("PNG size must be read from the IHDR")
        app0 = b"\xff\xe0\x00\x04JF"
        for marker, label in ((0xC0, "SOF0"), (0xC3, "SOF3"), (0xCA, "SOF10"), (0xCF, "SOF15")):
            path = root / f"{label}.jpg"
            path.write_bytes(_jpeg(marker, 640, 480, prefix=app0))
            if local_image_size(path) != (640, 480):
                fail(f"JPEG {label} marker must yield the frame size")
        dht = root / "dht-only.jpg"
        dht.write_bytes(b"\xff\xd8\xff\xc4\x00\x04\x00\x00\xff\xd9")
        if local_image_size(dht) is not None:
            fail("a DHT marker must not be treated as a JPEG frame")


def assert_note_alt_precedence() -> None:
    def ctx(alts: dict[str, str] | None = None) -> NoteFigureContext:
        return NoteFigureContext(note_id="NOTE-1", title="Signal", alts_by_path=dict(alts or {}))

    from_images = resolve_note_alt(
        ctx({"dir/chart.png": "From images"}),
        "From markdown",
        "dir/chart.png",
        caption="From caption",
    )
    if from_images.text != "From images" or from_images.decorative:
        fail(f"images[].alt must win: {from_images}")

    from_markdown = resolve_note_alt(
        ctx(),
        "From markdown",
        "dir/chart.png",
        caption="From caption",
    )
    if from_markdown.text != "From markdown" or from_markdown.decorative:
        fail(f"markdown alt must beat caption: {from_markdown}")

    from_caption = resolve_note_alt(ctx(), "", "./dir/chart.png?w=1", caption="**Bold** caption")
    if from_caption.text != "Bold caption" or from_caption.decorative:
        fail(f"caption must beat the Figure fallback: {from_caption}")

    fallback_ctx = ctx()
    fallback = resolve_note_alt(fallback_ctx, "", "other/chart.png", caption="")
    if fallback.text != "Figure 1 from “Signal”" or fallback.decorative:
        fail(f"missing alt must use Figure N: {fallback}")
    if len(fallback_ctx.uncaptioned) != 1:
        fail("Figure N fallback must be recorded once")
    again = resolve_note_alt(fallback_ctx, "", "dir/chart.png")
    if again.text != "Figure 2 from “Signal”" or fallback_ctx.figure_n != 2:
        fail(f"each uncaptioned figure resolves once and increments: {again} n={fallback_ctx.figure_n}")
    basename = ctx({"dir/chart.png": "Full path"})
    missed = resolve_note_alt(basename, "", "other/chart.png")
    if missed.text == "Full path" or "Figure 1" not in missed.text:
        fail(f"alt lookup must use the full path, not the basename: {missed}")
    hit = resolve_note_alt(basename, "", "dir/chart.png")
    if hit.text != "Full path":
        fail(f"full relative path must hit images[].alt: {hit}")

    decorative_images = resolve_note_alt(
        ctx({"dir/chart.png": "Decorative"}),
        "From markdown",
        "/dir/chart.png",
        caption="From caption",
    )
    if not decorative_images.decorative or decorative_images.text != "":
        fail("images[].alt decorative marker must win and clear the alt")

    decorative_markdown = resolve_note_alt(ctx(), "decorative", "dir/plain.png", caption="From caption")
    if not decorative_markdown.decorative or decorative_markdown.text != "":
        fail("markdown decorative marker must clear the alt")

    site = {"base_path": ""}
    block_ctx = ctx()
    html = _render_image_block(
        "![](assets/NOTE-1/a.png)",
        note_id="NOTE-1",
        site=site,
        figures=block_ctx,
    )
    if 'alt="Figure 1 from “Signal”"' not in html or "Figure 2" in html:
        fail(f"a figure must resolve its alt once: {html}")
    if len(block_ctx.uncaptioned) != 1:
        fail("rendering one figure must record one uncaptioned fallback")
    marked = _render_image_block(
        "![decorative](assets/NOTE-1/b.png)Visible caption",
        note_id="NOTE-1",
        site=site,
        figures=ctx(),
    )
    if 'alt=""' not in marked or 'role="presentation"' not in marked:
        fail(f"decorative figures render an empty alt and presentation role: {marked}")
    if "Visible caption" not in marked:
        fail("a decorative figure keeps its visible caption")
    if "aria-hidden" in marked:
        fail("a decorative figure must not aria-hide a caption that is not the alt")

    repeated = _render_image_block(
        "![Chart of hours](assets/NOTE-1/a.png)Chart of hours",
        note_id="NOTE-1",
        site=site,
        figures=ctx(),
    )
    if 'aria-hidden="true"' not in repeated:
        fail(f"a plain caption identical to the alt is hidden: {repeated}")

    linked = _render_image_block(
        "![ILO report](assets/NOTE-1/a.png)[ILO report](https://ilo.org/report)",
        note_id="NOTE-1",
        site=site,
        figures=ctx(),
    )
    if "aria-hidden" in linked:
        fail(f"a caption with a link must stay available: {linked}")
    if 'alt="ILO report"' not in linked:
        fail(f"markdown alt still wins when the caption is a link: {linked}")

    sourced = resolve_note_alt(
        ctx(),
        "",
        "dir/chart.png",
        caption="Source: [ILO](https://ilo.org/report)",
    )
    if not sourced.text.startswith("Figure 1 from") or sourced.decorative:
        fail(f"a Source caption must fall through to Figure N: {sourced}")
    named = resolve_note_alt(
        ctx({"dir/chart.png": "Chart of hours"}),
        "",
        "dir/chart.png",
        caption="Source: ILO",
    )
    if named.text != "Chart of hours":
        fail(f"images[].alt still wins over a Source caption: {named}")
    source_html = _render_image_block(
        "![](assets/NOTE-1/a.png)Source: [ILO](https://ilo.org/report)",
        note_id="NOTE-1",
        site=site,
        figures=ctx(),
    )
    if "aria-hidden" in source_html:
        fail(f"an attribution caption must not be aria-hidden: {source_html}")
    if 'alt="Figure 1 from' not in source_html or "ilo.org/report" not in source_html:
        fail(f"an attribution caption stays visible and is not the alt: {source_html}")

    leaked = NoteFigureContext(note_id="NOTE-2", title="Other", alts_by_path={})
    leaked_alt = resolve_note_alt(leaked, "", "dir/chart.png")
    if leaked_alt.text == "From images":
        fail("alt state leaked across note contexts")


def assert_launch_facts() -> None:
    site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
    export = json.loads((DATA / "export_public.json").read_text(encoding="utf-8"))
    errors = launch_fact_errors(site, export)
    if errors:
        fail("; ".join(errors))
    if site["home_proof_line"]["text"] != LOCKED_PROOF_TEXT:
        fail("locked proof line changed")
    bad_title = json.loads(json.dumps(site))
    bad_title["person"]["job_title"] = bad_title["person"]["job_title"].replace("&", "and")
    if not any("job_title" in item for item in launch_fact_errors(bad_title, export)):
        fail("job_title must match the experience title exactly, including &")
    bad_employer = json.loads(json.dumps(site))
    bad_employer["person"]["employer"] = "Prudential"
    if not any("employer" in item for item in launch_fact_errors(bad_employer, export)):
        fail("person.employer must match the experience organization exactly")
    bad_card = json.loads(json.dumps(site))
    bad_card["home_featured"]["systems"][2]["employer"] = "STB"
    if not any("stb-data-engineer" in item for item in launch_fact_errors(bad_card, export)):
        fail("featured SYS employer must match that record's organization")
    bad_source = json.loads(json.dumps(site))
    bad_source["home_proof_line"]["sources"] = ["outcomes[9]"]
    if not any("does not resolve" in item for item in launch_fact_errors(bad_source, export)):
        fail("proof sources must resolve in site.json or export")
    bad_number = json.loads(json.dumps(site))
    bad_number["home_proof_line"]["text"] = LOCKED_PROOF_TEXT
    bad_number["outcomes"][0]["label"] = "Documentation cycle without digits"
    bad_number["enterprise_copy"][
        "prudential-singapore-senior-data-engineer-solutioning-architecture"
    ]["outcome"] = "Ramp and documentation improved."
    missing_numbers = [
        item for item in launch_fact_errors(bad_number, export) if item.startswith("home_proof_line number")
    ]
    if not missing_numbers:
        fail("every number in the proof line must appear in the resolved sources")


def assert_library_boot_panel() -> None:
    css = (ROOT / "src" / "styles" / "library.css").read_text(encoding="utf-8")
    rule = re.search(
        r'html\[data-library-boot="detail"\] \.library-panels > \.library-panel:first-child:not\(\[hidden\]\) \{([^}]+)\}',
        css,
    )
    if rule is None or "display: block" not in rule.group(1) or "!important" in rule.group(1):
        fail("desktop boot must show only the unhidden first panel, without beating [hidden]")
    if "library-panel:first-child {" in css:
        fail("boot rule must not target every first panel, including hidden ones")
    boot = (ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
    if 'matchMedia("(min-width: 49rem)")' not in boot:
        fail("library boot script must use the same 49rem rail as the CSS")
    if "data-library-hash" not in boot:
        fail("library boot script must record the hash before first paint")
    if ".library-panel:is(:target, :has(:target))" not in css:
        fail("deep-link panels must be visible from the hash before first paint")
    chrome = (ROOT / "src" / "chrome.js").read_text(encoding="utf-8")
    if 'classList.add("is-booting")' in chrome:
        fail("is-booting belongs on the shell markup only")
    for rel in ("notes/index.html", "systems/index.html"):
        html = (DIST / rel).read_text(encoding="utf-8")
        first = re.search(
            r'<article class="library-panel[^"]*" data-panel-id="[^"]*"\s*(hidden)?',
            html,
        )
        if first is None:
            fail(f"{rel} missing a library panel")
        if first.group(1):
            fail(f"{rel} first panel must be unhidden so the desktop boot paint can show it")


def main() -> None:
    if not DIST.is_dir():
        fail("dist/ missing — run python scripts/build.py first")
    assert_evidence_href_https_only()
    assert_deploy_preview_contract()
    assert_local_image_size()
    assert_note_alt_precedence()
    assert_launch_facts()
    assert_library_boot_panel()
    assert_note_asset_href()
    assert_note_heading_anchors()
    assert_note_cover_html()
    assert_note_prose_blocks()
    assert_inarticle_toc_sidebar()
    assert_format_note_date()
    assert_writing_rows_preserve_images()

    site = resolve_site_base(json.loads((DATA / "site.json").read_text(encoding="utf-8")))
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
    if 'class="current-index"' in home:
        fail("home must not use legacy current-index (use featured record rows)")
    if not has_html_class(home, "home-featured-records"):
        fail("home missing featured record rows")
    if not has_html_class(home, "home-record-row"):
        fail("home featured records must use record rows")
    if (
        home.count('data-record="SYS-01"') != 1
        or home.count('data-record="SYS-02"') != 1
        or home.count('data-record="SYS-03"') != 1
    ):
        fail("home featured strip must show SYS-01, SYS-02, and SYS-03 once each")
    if "Governed lakehouse operating patterns" in home:
        fail("the second SYS-01 angle must leave Home")
    if home.count('class="entrance-proof"') != 1:
        fail("home must carry exactly one quiet proof line")
    if "entrance-identity" not in home or "entrance-name" not in home or "entrance-role" not in home:
        fail("home missing identity line")
    if "home-record-employer" not in home:
        fail("featured system cards must name the employer on a meta line")
    if "NOTE-2026-005" not in home:
        fail("home must feature a governance-aligned note")
    if f"{with_base(site, '/systems/')}#SYS-" not in home or f"{with_base(site, '/notes/')}#NOTE-" not in home:
        fail("home featured records must deep-link to catalogue records, not section indexes")
    if 'data-library-deck' in home or has_html_class(home, "library-slide"):
        fail("home must not ship the library slide deck")
    if not has_html_class(home, "header-search"):
        fail("home search must live in the header for instant access")
    if 'id="catalogue-search"' in home:
        fail("home must not bury catalogue search at page bottom")
    if has_html_class(home, "home-entry-grid"):
        fail("home must not duplicate header nav with entry grid cards")
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
    if not has_html_class(home, "home-pacing"):
        fail("home must use paced snap sections")
    if not has_html_class(home, "home-snap-proposition"):
        fail("home missing proposition snap section")
    if not has_html_class(home, "home-snap-proof"):
        fail("home missing proof snap section")
    if not has_html_class(home, "home-record-strip"):
        fail("home featured records must use horizontal snap strip")
    if 'class="home-record-rows"' in home:
        fail("home must not use vertical featured record stack")
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
    if 'class="proof-strip"' in home:
        fail("home must not use legacy proof-strip (split context and platform strips)")
    if not has_html_class(home, "home-context-strip"):
        fail("home missing location/context strip")
    if not has_html_class(home, "home-platform-strip"):
        fail("home missing platform strip")
    platform_strip = html_ul_block(home, "home-platform-strip")
    if "AWS" in platform_strip:
        fail("home platform strip must not list AWS")
    if 'class="cta-row"' in home:
        fail("home must not ship cta-row (use entrance-actions)")
    if not has_html_class(home, "entrance-actions"):
        fail("home missing entrance action links")
    hero_before_meta = home.split("home-context-strip", 1)[0]
    if "View systems" in hero_before_meta:
        fail("home hero must not duplicate Systems button")
    if href_attr(site, "/contact/") in hero_before_meta:
        fail("home hero must not ship Connect button (contact is in footer)")
    if "Specialist" in hero_before_meta:
        fail("entrance must not use vague Specialist positioning")
    if "CTO" in hero_before_meta or "CDAO" in hero_before_meta:
        fail("entrance must not claim CTO/CDAO")
    if "Building intelligible systems" not in home:
        fail("home entrance must use thesis headline")
    if "cost-intelligence" not in home:
        fail("home lede must name cost-intelligence capability")
    if "operationally sustainable" not in home:
        fail("home lede must describe operational sustainability")
    if "The durable part of a platform is not the stack" not in home:
        fail("home philosophy must not replay the lede")
    if "bridging the gap" in home:
        fail("home must not keep the legacy philosophy restatement")
    if 'class="portrait-chip"' in home:
        fail("home must not use hero portrait-chip")
    if href_attr(site, "/career-journey/") in home:
        fail("home must not link to removed Career Journey route")
    if href_attr(site, "/credentials/") not in home:
        fail("home must link to credentials via header or current index")
    if href_attr(site, "/about/") in home.split("home-platform-strip", 1)[-1]:
        fail("home footer area must not link to removed Profile route")
    if 'class="home-philosophy"' not in home and 'class="philosophy home-philosophy"' not in home:
        fail("home must surface philosophy blockquote")
    if "Operating principle" not in home:
        fail("home must label the philosophy block")
    if not has_html_class(home, "home-practice-areas"):
        fail("home must surface practice areas")
    if not has_html_class(home, "home-practice-item"):
        fail("home practice areas must use list items")
    if "Governed data platforms" not in home:
        fail("home practice areas must include governed data platforms")
    if "Product & User Focus" in home:
        fail("home must not surface Product & User Focus competency card")
    if "Data Engineering Leadership" in home:
        fail("home must not surface legacy competency cards")
    if 'class="home-practice-proof"' in home:
        fail("home practice areas must not show catalogue id proof links")
    if f"{with_base(site, '/notes/')}#NOTE-" not in home:
        fail("home featured records must link into notes catalogue records")
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
    if href_attr(site, "/systems/") not in desktop_nav:
        fail("desktop nav Systems must link to /systems/")
    if href_attr(site, "/notes/") not in desktop_nav:
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
    if href_attr(site, "/about/") in primary_nav:
        fail("primary nav must not link to removed Profile route")
    if href_attr(site, "/systems/") not in primary_nav:
        fail("primary nav must link Systems to /systems/")

    systems_href = with_base(site, "/systems/")
    notes_href = with_base(site, "/notes/")
    portfolio_redirect = (DIST / "portfolio" / "index.html").read_text(encoding="utf-8")
    if systems_href not in portfolio_redirect:
        fail("/portfolio/ redirect must point to /systems/")
    catalogue_redirect = (DIST / "systems" / "catalogue" / "index.html").read_text(encoding="utf-8")
    if systems_href not in catalogue_redirect:
        fail("/systems/catalogue/ redirect must point to /systems/")
    perspectives_redirect = (DIST / "perspectives" / "index.html").read_text(encoding="utf-8")
    if notes_href not in perspectives_redirect:
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
    if "Enterprise records" not in systems:
        fail("systems index must include the enterprise records section")
    if "Selected Work Summaries" in systems:
        fail("systems index must not keep the Selected Work Summaries label")
    if 'library-index-group--depth-' not in systems:
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
    sys01_related = re.search(
        r'<article class="library-panel[^"]*"[^>]*data-record="SYS-01"[^>]*>[\s\S]*?'
        r'<p class="related-paths meta">([\s\S]*?)</p>',
        systems,
    )
    if not sys01_related:
        fail("SYS-01 library panel must include related paths")
    sys01_related_html = sys01_related.group(1)
    if "Credentials" in sys01_related_html or "Notes" in sys01_related_html:
        if sys01_related_html.count("<a ") <= 2:
            fail("SYS-01 related paths must not be only generic Credentials and Notes")
    if "SYS-02" not in sys01_related_html and "NOTE-2026-005" not in sys01_related_html:
        fail("SYS-01 related paths must link sibling records from system_map")
    if "CEI internals are not published" in systems:
        fail("Prudential evidence must not use retired CEI internals disclaimer")
    if "Public record: LinkedIn role. Internal dashboards are not public." not in systems:
        fail("Prudential evidence must disclose the public record without linking internal dashboards")
    if "Internal platforms and dashboards are not linked" in systems:
        fail("Prudential evidence must use the tightened public-record sentence")
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
    if re.search(
        r"\.home-snap-proposition\.home-hero\s*\{[^}]*min-height:\s*calc\(100dvh",
        css,
        re.S,
    ):
        fail("home proposition must not lock to full viewport height (featured records should peek)")
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
    if css.count("@keyframes") != 1 or "@keyframes map-panel-in" not in css:
        fail("only map-panel-in may remain as a keyframe")
    if "--dur-fast: 150ms" not in css or "--dur-base: 240ms" not in css or "--dur-slow: 400ms" not in css:
        fail("motion durations must be the three tokens 150/240/400ms")

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
    light_faint = _token_hex(light, "--text-faint")
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
        ("light --text-faint on --bg-deep", light_faint, light_bg, 4.5),
        ("light --text-faint on --bg-mid", light_faint, light_mid, 4.5),
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
    if "<title>Systems — Yingzhao Ouyang</title>" not in portfolio:
        fail("systems title must be Systems — Yingzhao Ouyang")
    if "<title>Yingzhao Ouyang — Building intelligible systems" not in home:
        fail("home title must lead with the name and the thesis")
    if "<title>Notes — Yingzhao Ouyang</title>" not in notes:
        fail("notes title must be Notes — Yingzhao Ouyang")
    if "<title>Professional record — Yingzhao Ouyang</title>" not in credentials:
        fail("credentials title must use the DS route name")
    not_found = (DIST / "404.html").read_text(encoding="utf-8")
    if "<title>Not in the catalogue — Yingzhao Ouyang</title>" not in not_found:
        fail("404 title must be Not in the catalogue — Yingzhao Ouyang")
    if "That record isn't on the shelves." not in not_found:
        fail("404 must use the catalogue-voice line")
    if 'rel="icon"' not in home or "favicon.svg" not in home:
        fail("pages must link a favicon")
    if "/assets/og/og-default.png" not in home:
        fail("og:image must point at the default share card")
    if not (DIST / "assets" / "og" / "og-default.png").is_file():
        fail("og image must be copied into dist")
    if "Crimson+Pro:ital,wght@0,400;0,600;1,400" not in home:
        fail("font stylesheet must load real Crimson Pro italic")
    def assert_built_origin(html: str, label: str) -> None:
        canon = _canonical(html)
        if not canon:
            fail(f"{label} missing canonical")
        og_url = _meta(html, prop="og:url")
        og_image = _meta(html, prop="og:image")
        if og_url and og_url != canon:
            fail(f"{label} og:url must match canonical")
        styles = re.search(r'href="([^"]*)/styles\.css"', html)
        prefix = normalize_base(styles.group(1)) if styles else ""
        canon_path = urlparse(canon).path
        if prefix and not (canon_path.startswith(prefix + "/") or canon_path.rstrip("/") == prefix):
            fail(f"{label} asset prefix {prefix!r} disagrees with canonical path {canon_path!r}")
        if og_image:
            image = urlparse(og_image)
            page = urlparse(canon)
            if (image.scheme, image.netloc) != (page.scheme, page.netloc):
                fail(f"{label} og:image host disagrees with canonical")
            if prefix and not image.path.startswith(prefix + "/"):
                fail(f"{label} og:image path {image.path!r} disagrees with asset prefix {prefix!r}")
            if not prefix and image.path.startswith("/yzouyang-site/") and "www.yzouyang.com" in canon:
                fail(f"{label} canonical is public while og:image stays on the project path")
        for url in _json_ld_urls(html):
            if urlparse(url).netloc != urlparse(canon).netloc:
                fail(f"{label} JSON-LD url {url} disagrees with canonical")

    assert_built_origin(home, "home")
    if _meta(not_found, name="robots") != "noindex, nofollow":
        fail("built 404 must always be noindex, nofollow")
    if _canonical(not_found):
        fail("built 404 must not emit a canonical")
    if _meta(not_found, prop="og:url"):
        fail("built 404 must not emit og:url")
    contact_built = (DIST / "contact" / "index.html").read_text(encoding="utf-8")
    if _canonical(contact_built) and urlparse(_canonical(contact_built)).netloc != urlparse(_canonical(home)).netloc:
        fail("redirect canonical host disagrees with home")
    if _meta(contact_built, name="robots") != _meta(home, name="robots"):
        fail("redirect robots must match the page robots directive")
    person_ld = person_json_ld(site)
    if '"jobTitle":"Senior Manager, Cloud Economics & Intelligence"' not in person_ld:
        fail("JSON-LD jobTitle must be the current role, not the thesis")
    if '"email"' in person_ld:
        fail("JSON-LD must not repeat the footer email")
    if "/notes/" in person_ld:
        fail("JSON-LD sameAs must not include the relative notes path")
    for url in (
        "https://www.linkedin.com/in/yzouyang/",
        "https://www.github.com/KunojiLym",
        "https://medium.com/@kunojilym",
    ):
        if url not in person_ld:
            fail(f"JSON-LD sameAs missing absolute URL {url}")
    for phrase in (
        "Bitly optional",
        "in the searchable catalogue",
        "Selected technical, data science, and product/UX work",
        "Selected Work Summaries",
        "How to Verify",
    ):
        for label, html in (
            ("home", home),
            ("systems", systems),
            ("notes", notes),
            ("credentials", credentials),
        ):
            if phrase in html:
                fail(f"{label} still shows visitor-facing internal copy: {phrase}")
    if "Senior Manager, Cloud Economics and Intelligence" not in portfolio:
        fail("Prudential title must match master CV (Senior Manager, Cloud Economics…)")
    if "Senior Data Engineer, Solutioning" in portfolio:
        fail("Prudential title must not remain Senior Data Engineer")
    if 'id="skillup-mtech-capstone"' not in portfolio:
        fail("work page missing SkillUP heading id")
    if 'id="stb-data-engineer-applied-ml"' not in portfolio:
        fail("work page missing STB applied-ML enterprise case")
    if 'library-index-group--depth-' not in portfolio:
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
    ent_pos = portfolio.find("Enterprise records")
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
    if 'library-index-group--depth-' not in credentials:
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
    if "<title>Yingzhao Ouyang — Building intelligible systems" not in about:
        fail("about redirect must use the name-first home title")
    if "<title>Home</title>" in about:
        fail("about redirect must not be titled Home")
    if has_html_class(about, "library-shell"):
        fail("about must redirect to home, not ship library shell")
    if not has_html_class(credentials, "library-shell"):
        fail("credentials missing library-shell layout")
    if not has_html_class(credentials, "library-index"):
        fail("credentials missing library index")
    if 'data-panel-id="core-competencies"' in credentials:
        fail("credentials must not host core competencies (practice areas live on home)")
    if 'data-panel-id="career-journey"' in credentials:
        fail("credentials must not host career journey panel")
    if 'class="library-index-footer"' in credentials:
        fail("credentials must not ship sidebar footer (removed with Career Journey)")
    if href_attr(site, "/career-journey/") in credentials:
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
    if 'library-index-group--depth-' not in notes:
        fail("notes index must group essays by category")
    if "note-kicker" not in notes or "note-byline" not in notes:
        fail("notes panels must show category kicker and reading byline")
    if "medium.com/@kunojilym" not in notes:
        fail("notes page missing Medium writing links")
    if "notes-entry" not in notes:
        fail("notes page must render per-note entry panels")
    if "Publication index with stable NOTE-* catalogue IDs" in notes:
        fail("notes page must not show legacy publication index lede")
    if 'class="library-index-meta"' not in notes:
        fail("notes index entries should show publication date as meta")
    assert_library_index_controls()
    if "Part 1: How AI is Reshaping" not in notes:
        fail("notes series index should show part titles without repeating series name")
    note_entry_bodies = re.findall(
        r'<article class="notes-entry">([\s\S]*?)</article>', notes
    )
    if any("<h2" in body for body in note_entry_bodies):
        fail("notes library panels must not duplicate titles inside entry body")

    series_title = _note_index_title(
        {"title": "The AI Disruption Part 1: How AI is Reshaping Work"},
        series="The AI Disruption",
    )
    if not series_title.startswith("Part 1:"):
        fail("_note_index_title must strip repeated series prefix from index labels")

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
    home_path = with_base(site, "/")
    for source in ("/about", "/about/", "/contact", "/contact/"):
        line = f"{with_base(site, source)} {home_path} 301"
        if line not in redirects:
            fail(f"_redirects must 301 {source} to home")

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
