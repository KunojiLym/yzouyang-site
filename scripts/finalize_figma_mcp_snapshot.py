#!/usr/bin/env python3
"""Merge Figma MCP export parts into docs/figma/variables.json, preserving web + notes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"
INBOX = ROOT / "inbox"
COLLECTION_ORDER = (
    "Color",
    "Type",
    "Spacing",
    "Radius",
    "Motion",
    "Text Scale",
    "Breakpoint",
)


def web_by_name(snapshot: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for coll in snapshot.get("collections", []):
        for var in coll.get("variables", []):
            web = var.get("web")
            if web:
                out[var["name"]] = web
    return out


def apply_web(collections: list[dict], web_map: dict[str, str]) -> None:
    for coll in collections:
        for var in coll.get("variables", []):
            web = web_map.get(var["name"])
            if web:
                var["web"] = web


def sync_text_styles_from_mcp(styles: list[dict]) -> list[dict]:
    by = {item["name"]: dict(item) for item in styles}
    h1 = by.get("Display/H1")
    if h1:
        h1["lineHeight"] = {"unit": "PERCENT", "value": 120.00000476837158}
    base = by.get("Body/Base")
    if base and "Body/Base Underline" not in by:
        underline = dict(base)
        underline["name"] = "Body/Base Underline"
        underline["textDecoration"] = "UNDERLINE"
        by["Body/Base Underline"] = underline
    strong = by.get("Body/Small Strong")
    if strong and "Body/Small Strong Underline" not in by:
        underline = dict(strong)
        underline["name"] = "Body/Small Strong Underline"
        underline["textDecoration"] = "UNDERLINE"
        by["Body/Small Strong Underline"] = underline
    return [by[name] for name in sorted(by)]


def main() -> None:
    head_path = INBOX / "mcp-head.json"
    color_path = INBOX / "mcp-color.json"
    type_spacing_path = INBOX / "mcp-type-spacing.json"
    rest_path = INBOX / "mcp-rest.json"

    if not head_path.is_file() or not color_path.is_file():
        raise SystemExit(f"missing {head_path} and/or {color_path}")

    old = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    head = json.loads(head_path.read_text(encoding="utf-8"))
    color = json.loads(color_path.read_text(encoding="utf-8"))

    by_name = {coll["name"]: coll for coll in old.get("collections", [])}
    by_name["Color"] = color
    if type_spacing_path.is_file():
        for coll in json.loads(type_spacing_path.read_text(encoding="utf-8")):
            by_name[coll["name"]] = coll
    if rest_path.is_file():
        for coll in json.loads(rest_path.read_text(encoding="utf-8")):
            by_name[coll["name"]] = coll
    collections = [by_name[name] for name in COLLECTION_ORDER if name in by_name]
    web_map = web_by_name(old)
    apply_web(collections, web_map)

    notes = list(old.get("notes", []))
    stamp = head.get("exportedAt", "").split("T")[0]
    notes.append(
        f"{stamp}: MCP re-export (109 vars / 30 text styles). "
        "New colors: warning-text, success-text, danger-text; "
        "Display/H2 Page → font-size/text-display-2/max; "
        "text styles Body/Base Underline, Body/Small Strong Underline."
    )

    text_styles = head.get("textStyles")
    if not text_styles:
        text_styles = sync_text_styles_from_mcp(old.get("textStyles", []))
    else:
        text_styles = sync_text_styles_from_mcp(text_styles)

    out = {
        "fileKey": head.get("fileKey", old.get("fileKey")),
        "fileUrl": head.get("fileUrl", old.get("fileUrl")),
        "exportedAt": head.get("exportedAt", old.get("exportedAt")),
        "source": "cursor-figma-mcp + repo web bindings",
        "counts": head.get("counts", old.get("counts")),
        "notes": notes,
        "collections": collections,
        "textStyles": text_styles,
    }

    INBOX.mkdir(parents=True, exist_ok=True)
    full = INBOX / "figma-vars-full.json"
    text = json.dumps(out, indent=2) + "\n"
    full.write_text(text, encoding="utf-8")
    SNAPSHOT.write_text(text, encoding="utf-8")
    print(f"wrote {full} and {SNAPSHOT}")
    print(
        "counts:",
        out["counts"],
        "textStyles:",
        len(out["textStyles"]),
    )


if __name__ == "__main__":
    main()
