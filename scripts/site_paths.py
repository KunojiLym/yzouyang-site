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


def lookup_site(site: dict, path: str, default: object = "") -> object:
    """Read a dotted site.json path. Missing or wrong-typed values return default.

    A default of None has no type to check, so a present value is returned.
    A stored null is treated as missing and returns default.
    """
    node: object = site
    for part in path.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    if node is None:
        return default
    if default is not None and not isinstance(node, type(default)):
        return default
    return node


def esc(value: object) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
