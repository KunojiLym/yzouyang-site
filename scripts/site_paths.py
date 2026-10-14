"""Path prefixing and HTML escaping shared by the builder and image renderer."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
