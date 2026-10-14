"""Inline markdown for note prose: emphasis, code, links, and images.

This is general markdown, not an image helper. Image paths and sizes stay in
note_images.
"""

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
    caption_aria_hidden,
    resolve_note_alt,
)
from note_images import (
    IMAGE_LINE_RE,
    figures_for,
    is_image_line,
    is_note_asset_ref,
    markdown_image_tag,
    note_asset_href,
)
from site_paths import esc, with_base


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
