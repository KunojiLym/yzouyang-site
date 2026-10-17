#!/usr/bin/env python3
"""Merge committed Figma MCP parts into docs/figma/variables.json."""

from __future__ import annotations

import sys
from pathlib import Path

from figma_mcp_snapshot import (
    DEFAULT_PARTS_DIR,
    build_snapshot,
    load_parts,
    write_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"


def main() -> None:
    parts_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PARTS_DIR
    old = __import__("json").loads(SNAPSHOT.read_text(encoding="utf-8"))
    head, collections = load_parts(parts_dir)
    snapshot = build_snapshot(head, collections, old)
    write_snapshot(snapshot)
    print(f"wrote {SNAPSHOT}")
    print("counts:", snapshot["counts"])


if __name__ == "__main__":
    main()
