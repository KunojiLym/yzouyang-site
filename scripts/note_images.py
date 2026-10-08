"""Note image tags, sizes, and the inline markdown that embeds them."""

from __future__ import annotations

import re
from html import unescape as html_unescape
from urllib.parse import unquote

from note_figures import (
    BOLD_RE,
    CODE_RE,
    ITALIC_RE,
    MD_IMAGE_RE,
    MD_LINK_RE,
    NoteFigureContext,
    ResolvedAlt,
    caption_aria_hidden,
    local_image_size,
    resolve_note_alt,
)
from site_paths import ROOT, esc, normalize_base, with_base

IMAGE_LINE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)(.*)$")
EXPAND_LINE_RE = re.compile(r"^Expand to see\b", re.I)
BLOCK_BREAK_RE = re.compile(r"^(#{1,4}\s|-\s|\d+\.\s|```)")


def is_note_asset_ref(href: str) -> bool:
    cleaned = href.strip().replace("\\", "/")
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]
    return cleaned.startswith(("assets/", "writing/assets/"))


def note_asset_href(site: dict, note_id: str, rel_path: str) -> str:
    cleaned = rel_path.strip().replace("\\", "/").lstrip("/")
    for prefix in ("assets/writing/", "assets/notes/", "writing/assets/", "assets/"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break
    note_prefix = f"{note_id}/"
    if cleaned.startswith(note_prefix):
        return with_base(site, f"/assets/notes/{cleaned}")
    return with_base(site, f"/assets/notes/{note_id}/{cleaned}")


def is_image_line(line: str) -> bool:
    return bool(IMAGE_LINE_RE.match(line.strip()))


def figures_for(
    note_id: str,
    figures: NoteFigureContext | None,
    *,
    title: str = "",
) -> NoteFigureContext:
    if figures is not None:
        return figures
    return NoteFigureContext(note_id=note_id, title=title or note_id)


def size_attrs_for_src(site: dict, note_id: str, raw_src: str) -> str:
    if not is_note_asset_ref(raw_src) and not raw_src.startswith("/assets/"):
        return ""
    href = note_asset_href(site, note_id, raw_src)
    rel = href
    base = normalize_base(site.get("base_path", ""))
    if base and rel.startswith(base):
        rel = rel[len(base) :]
    path = ROOT / rel.lstrip("/")
    size = local_image_size(path)
    if not size:
        return ""
    width, height = size
    return f' width="{width}" height="{height}"'


def markdown_image_tag(
    alt: str,
    src: str,
    *,
    note_id: str,
    site: dict,
    caption: str = "",
    figures: NoteFigureContext | None = None,
    resolved: ResolvedAlt | None = None,
) -> str:
    raw_src = html_unescape(src.strip())
    if is_note_asset_ref(raw_src):
        path = esc(note_asset_href(site, note_id, raw_src))
    elif raw_src.startswith(("http://", "https://")):
        path = esc(raw_src)
    else:
        path = esc(with_base(site, raw_src))
    if resolved is None:
        resolved = resolve_note_alt(
            figures_for(note_id, figures),
            alt,
            raw_src,
            caption=caption,
        )
    dims = size_attrs_for_src(site, note_id, raw_src)
    role = ' role="presentation"' if resolved.decorative else ""
    return f'<img src="{path}" alt="{esc(resolved.text)}"{role}{dims} loading="lazy" />'


def inline_markdown(
    text: str,
    *,
    note_id: str,
    site: dict,
    figures: NoteFigureContext | None = None,
    anchor_ids: set[str] | None = None,
    scope_anchors: bool = False,
) -> str:
    ctx = figures_for(note_id, figures)
    safe = esc(text)
    safe = BOLD_RE.sub(r"<strong>\1</strong>", safe)
    safe = ITALIC_RE.sub(r"<em>\1</em>", safe)
    safe = CODE_RE.sub(r"<code>\1</code>", safe)

    def img_repl(match: re.Match[str]) -> str:
        alt, src = match.group(1), match.group(2)
        return markdown_image_tag(alt, src, note_id=note_id, site=site, figures=ctx)

    safe = MD_IMAGE_RE.sub(img_repl, safe)

    def link_repl(match: re.Match[str]) -> str:
        label, href = match.group(1), match.group(2).strip()
        raw_href = html_unescape(href)
        if raw_href.startswith("#") and scope_anchors and note_id and anchor_ids:
            frag = unquote(raw_href[1:])
            if frag in anchor_ids:
                raw_href = f"#{note_id}-{frag}"
            return f'<a href="{esc(raw_href)}">{label}</a>'
        if is_note_asset_ref(raw_href):
            path = esc(note_asset_href(site, note_id, raw_href))
            return f'<a href="{path}">{label}</a>'
        if raw_href.startswith(("http://", "https://")):
            return (
                f'<a class="external" href="{href}" target="_blank" '
                f'rel="noopener noreferrer">{label}</a>'
            )
        return f'<a href="{esc(with_base(site, raw_href))}">{label}</a>'

    return MD_LINK_RE.sub(link_repl, safe)


def render_image_block(
    line: str,
    *,
    note_id: str,
    site: dict,
    figures: NoteFigureContext | None = None,
) -> str:
    ctx = figures_for(note_id, figures)
    match = IMAGE_LINE_RE.match(line.strip())
    if not match:
        return f"<p>{inline_markdown(line.strip(), note_id=note_id, site=site, figures=ctx)}</p>"
    alt, src, caption = match.group(1), match.group(2), match.group(3).strip()
    resolved = resolve_note_alt(ctx, alt, src, caption=caption)
    img_html = markdown_image_tag(
        alt, src, note_id=note_id, site=site, figures=ctx, resolved=resolved
    )
    caption_html = ""
    if caption:
        hidden = ' aria-hidden="true"' if caption_aria_hidden(caption, resolved.text) else ""
        caption_html = (
            f'  <figcaption class="note-figure-caption"{hidden}>'
            f"{inline_markdown(caption, note_id=note_id, site=site, figures=ctx)}"
            f"</figcaption>\n"
        )
    return f'<figure class="note-figure">\n  {img_html}\n{caption_html}</figure>'


def collect_expand_body(lines: list[str], start: int) -> tuple[list[str], int]:
    body: list[str] = []
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and is_image_line(lines[j]):
                i += 1
                continue
            break
        if EXPAND_LINE_RE.match(stripped) or BLOCK_BREAK_RE.match(stripped):
            break
        if is_image_line(stripped):
            body.append(lines[i])
            i += 1
            continue
        break
    return body, i


def render_expand_block(
    summary_line: str,
    body_lines: list[str],
    *,
    note_id: str,
    site: dict,
    figures: NoteFigureContext | None = None,
) -> str:
    ctx = figures_for(note_id, figures)
    summary_html = inline_markdown(summary_line.strip(), note_id=note_id, site=site, figures=ctx)
    body_parts = [
        render_image_block(line, note_id=note_id, site=site, figures=ctx)
        for line in body_lines
        if line.strip() and is_image_line(line)
    ]
    if not body_parts:
        return f"<p>{summary_html}</p>"
    body_inner = "\n".join(body_parts)
    return (
        '<details class="note-expand">\n'
        f'  <summary class="note-expand-summary">{summary_html}</summary>\n'
        '  <div class="note-expand-body">\n'
        f"{body_inner}\n"
        "  </div>\n"
        "</details>"
    )
