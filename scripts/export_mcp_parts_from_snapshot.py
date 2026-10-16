#!/usr/bin/env python3
"""Write docs/figma/mcp-parts/ from variables.json (strip web bindings only)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from figma_mcp_snapshot import COLLECTION_ORDER, DEFAULT_PARTS_DIR

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"


def strip_web(coll: dict) -> dict:
    out = deepcopy(coll)
    for var in out.get("variables", []):
        var.pop("web", None)
    return out


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    by_name = {coll["name"]: coll for coll in snapshot.get("collections", [])}
    head = {
        "fileKey": snapshot.get("fileKey"),
        "fileUrl": snapshot.get("fileUrl"),
        "exportedAt": snapshot.get("exportedAt"),
        "source": "cursor-figma-mcp, read-only",
        "textStyles": snapshot.get("textStyles", []),
    }
    DEFAULT_PARTS_DIR.mkdir(parents=True, exist_ok=True)
    (DEFAULT_PARTS_DIR / "head.json").write_text(
        json.dumps(head, indent=2) + "\n", encoding="utf-8"
    )
    (DEFAULT_PARTS_DIR / "color.json").write_text(
        json.dumps(strip_web(by_name["Color"]), indent=2) + "\n", encoding="utf-8"
    )
    type_spacing = [strip_web(by_name["Type"]), strip_web(by_name["Spacing"])]
    (DEFAULT_PARTS_DIR / "type-spacing.json").write_text(
        json.dumps(type_spacing, indent=2) + "\n", encoding="utf-8"
    )
    rest_names = ["Radius", "Motion", "Text Scale", "Breakpoint"]
    rest = [strip_web(by_name[name]) for name in rest_names]
    (DEFAULT_PARTS_DIR / "rest.json").write_text(
        json.dumps(rest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {DEFAULT_PARTS_DIR} ({len(COLLECTION_ORDER)} collections)")


if __name__ == "__main__":
    main()
