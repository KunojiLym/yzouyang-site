"""Per-note figure alt resolution and local image sizes.

Alt state lives on a NoteFigureContext for one note. Callers must not stash it
on the shared site dict, and image keys are full relative paths.

The decorative alt marker is the literal string "decorative" (matched
case-insensitively, see DECORATIVE_ALT). Put it in images[].alt or the
markdown image alt. It renders alt="" and role="presentation". An empty alt
is not decorative and falls through to the caption or the Figure N fallback.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from html import unescape as html_unescape
from pathlib import Path

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"\*(.+?)\*")
CODE_RE = re.compile(r"`([^`]+)`")
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# A real link, not the `[alt](src)` tail of an image.
_FOCUSABLE_CAPTION_RE = re.compile(
    r"(?<!!)\[([^\]]+)\]\(([^)]+)\)"
    r"|<\s*(?:a|button|input|select|textarea|iframe|audio|video|summary)\b"
    r"|tabindex\s*=",
    re.IGNORECASE,
)
_ATTRIBUTION_CAPTION_RE = re.compile(r"(?i)^source\s*:")

DECORATIVE_ALT = "decorative"

# SOF0–SOF15, excluding DHT (C4), JPG (C8), and DAC (CC), which are not frames.
_JPEG_SOF_MARKERS = set(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}


@dataclass
class NoteFigureContext:
    note_id: str
    title: str = ""
    alts_by_path: dict[str, str] = field(default_factory=dict)
    figure_n: int = 0
    uncaptioned: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedAlt:
    text: str
    decorative: bool


def image_path_key(src: str) -> str:
    """Full relative path, without a query, fragment, or leading slash."""
    raw = html_unescape(str(src or "").strip()).replace("\\", "/")
    raw = raw.split("?", 1)[0].split("#", 1)[0]
    while raw.startswith("./"):
        raw = raw[2:]
    return raw.lstrip("/")


def alts_by_full_path(images: object) -> dict[str, str]:
    """images[].alt keyed by the full relative path. Empty alts are omitted."""
    found: dict[str, str] = {}
    if not isinstance(images, list):
        return found
    for image in images:
        if not isinstance(image, dict):
            continue
        alt = str(image.get("alt") or "").strip()
        path = str(image.get("path") or "").strip()
        if not alt or not path:
            continue
        found[image_path_key(path)] = alt
    return found


def plain_caption_text(text: str) -> str:
    plain = MD_IMAGE_RE.sub(r"\1", text)
    plain = MD_LINK_RE.sub(r"\1", plain)
    plain = BOLD_RE.sub(r"\1", plain)
    plain = ITALIC_RE.sub(r"\1", plain)
    plain = CODE_RE.sub(r"\1", plain)
    plain = html_unescape(plain).replace("\u00a0", " ")
    plain = re.sub(r"\s+", " ", plain).strip()
    if len(plain) > 140:
        plain = plain[:139].rstrip() + "…"
    return plain


def _is_decorative(value: str) -> bool:
    return value.strip().lower() == DECORATIVE_ALT


def caption_is_attribution(caption: str) -> bool:
    """Source: lines are credits, not a description of the figure."""
    return bool(_ATTRIBUTION_CAPTION_RE.match(plain_caption_text(caption)))


def caption_aria_hidden(caption: str, alt_text: str) -> bool:
    """Hide a caption only when it repeats a plain-text alt and cannot be focused."""
    if not str(caption or "").strip() or not str(alt_text or "").strip():
        return False
    if _FOCUSABLE_CAPTION_RE.search(caption):
        return False
    plain = plain_caption_text(caption)
    return bool(plain) and plain == alt_text


def resolve_note_alt(
    figures: NoteFigureContext,
    alt: str,
    src: str,
    *,
    caption: str = "",
) -> ResolvedAlt:
    """images[].alt, then markdown alt, then caption, then Figure N.

    The decorative marker is the literal string "decorative". An explicit
    marker in either alt field renders an empty alt. An empty alt is not
    decorative. Each call resolves one figure.
    """
    key = image_path_key(src)
    if key in figures.alts_by_path:
        supplied = figures.alts_by_path[key].strip()
        if _is_decorative(supplied):
            return ResolvedAlt("", True)
        if supplied:
            return ResolvedAlt(supplied, False)
    explicit = str(alt or "").strip()
    if _is_decorative(explicit):
        return ResolvedAlt("", True)
    if explicit:
        return ResolvedAlt(explicit, False)
    plain_caption = plain_caption_text(caption) if caption else ""
    if plain_caption and not caption_is_attribution(caption):
        return ResolvedAlt(plain_caption, False)
    figures.figure_n += 1
    title = figures.title.strip() or figures.note_id
    fallback = f"Figure {figures.figure_n} from “{title}”"
    record = {"note_id": figures.note_id, "src": html_unescape(str(src).strip()), "alt": fallback}
    figures.uncaptioned.append(record)
    print(f"uncaptioned-figure {figures.note_id} {record['src']}", file=sys.stderr)
    return ResolvedAlt(fallback, False)


def local_image_size(path: Path) -> tuple[int, int] | None:
    """Read PNG, JPEG, or WebP pixel size without a third-party image library."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        return (width, height) if width and height else None
    if data[:2] == b"\xff\xd8":
        return _jpeg_size(data)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X" and len(data) >= 30:
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height
        if data[12:16] == b"VP8 " and len(data) >= 30 and data[23:26] == b"\x9d\x01\x2a":
            width = int.from_bytes(data[26:28], "little") & 0x3FFF
            height = int.from_bytes(data[28:30], "little") & 0x3FFF
            return (width, height) if width and height else None
        if data[12:16] == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little")
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return width, height
    return None


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    i = 2
    while i + 8 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in _JPEG_SOF_MARKERS:
            height = int.from_bytes(data[i + 5 : i + 7], "big")
            width = int.from_bytes(data[i + 7 : i + 9], "big")
            return (width, height) if width and height else None
        if marker == 0x01 or marker == 0xD8 or marker == 0xD9 or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if i + 4 > len(data):
            break
        size = int.from_bytes(data[i + 2 : i + 4], "big")
        if size < 2:
            break
        i += 2 + size
    return None
