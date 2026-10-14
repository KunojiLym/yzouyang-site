"""Note image paths, sizes, and figure tags."""

from __future__ import annotations

import re
from html import unescape as html_unescape

from note_figures import (
    NoteFigureContext,
    ResolvedAlt,
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
