#!/usr/bin/env python3
"""Shared helpers for merging Figma MCP export parts into variables.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"
INBOX = ROOT / "inbox"
DEFAULT_PARTS_DIR = ROOT / "docs" / "figma" / "mcp-parts"
COLLECTION_ORDER = (
    "Color",
    "Type",
    "Spacing",
    "Radius",
    "Motion",
    "Text Scale",
    "Breakpoint",
)


def web_by_name(snapshot: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for coll in snapshot.get("collections", []):
        for var in coll.get("variables", []):
            web = var.get("web")
            if web:
                out[var["name"]] = web
    return out


def apply_web(collections: list[dict[str, Any]], web_map: dict[str, str]) -> None:
    for coll in collections:
        for var in coll.get("variables", []):
            web = web_map.get(var["name"])
            if web:
                var["web"] = web


def load_parts(parts_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    head_path = parts_dir / "head.json"
    color_path = parts_dir / "color.json"
    type_spacing_path = parts_dir / "type-spacing.json"
    rest_path = parts_dir / "rest.json"
    missing = [
        p
        for p in (head_path, color_path, type_spacing_path, rest_path)
        if not p.is_file()
    ]
    if missing:
        raise FileNotFoundError(
            "missing MCP part file(s): " + ", ".join(str(p) for p in missing)
        )
    head = json.loads(head_path.read_text(encoding="utf-8"))
    color = json.loads(color_path.read_text(encoding="utf-8"))
    type_spacing = json.loads(type_spacing_path.read_text(encoding="utf-8"))
    rest = json.loads(rest_path.read_text(encoding="utf-8"))
    if not isinstance(type_spacing, list) or not isinstance(rest, list):
        raise ValueError("type-spacing.json and rest.json must be JSON arrays")
    collections = [color, *type_spacing, *rest]
    ordered = []
    by_name = {coll["name"]: coll for coll in collections}
    for name in COLLECTION_ORDER:
        if name not in by_name:
            raise ValueError(f"missing collection {name!r} in MCP parts")
        ordered.append(by_name[name])
    return head, ordered


def derive_counts(
    collections: list[dict[str, Any]], text_styles: list[dict[str, Any]]
) -> dict[str, Any]:
    per_collection: dict[str, dict[str, Any]] = {}
    variables = 0
    for coll in collections:
        vars_in_coll = coll.get("variables", [])
        variables += len(vars_in_coll)
        per_collection[coll["name"]] = {
            "variables": len(vars_in_coll),
            "modes": list(coll.get("modes", [])),
        }
    return {
        "collections": len(collections),
        "variables": variables,
        "textStyles": len(text_styles),
        "perCollection": per_collection,
    }


def build_snapshot(
    head: dict[str, Any],
    collections: list[dict[str, Any]],
    old_snapshot: dict[str, Any],
) -> dict[str, Any]:
    text_styles = head.get("textStyles")
    if not text_styles:
        raise ValueError("head.json has no textStyles; export them from Figma MCP")

    web_map = web_by_name(old_snapshot)
    apply_web(collections, web_map)

    counts = derive_counts(collections, text_styles)
    notes = list(old_snapshot.get("notes", []))
    stamp = str(head.get("exportedAt", "")).split("T")[0] or "unknown"
    note = (
        f"{stamp}: MCP re-export ({counts['variables']} vars / "
        f"{len(text_styles)} text styles)."
    )
    if note not in notes:
        notes.append(note)

    return {
        "fileKey": head.get("fileKey", old_snapshot.get("fileKey")),
        "fileUrl": head.get("fileUrl", old_snapshot.get("fileUrl")),
        "exportedAt": head.get("exportedAt", old_snapshot.get("exportedAt")),
        "source": "cursor-figma-mcp + repo web bindings",
        "counts": counts,
        "notes": notes,
        "collections": collections,
        "textStyles": text_styles,
    }


def write_snapshot(snapshot: dict[str, Any]) -> None:
    INBOX.mkdir(parents=True, exist_ok=True)
    full = INBOX / "figma-vars-full.json"
    text = json.dumps(snapshot, indent=2) + "\n"
    full.write_text(text, encoding="utf-8")
    SNAPSHOT.write_text(text, encoding="utf-8")
