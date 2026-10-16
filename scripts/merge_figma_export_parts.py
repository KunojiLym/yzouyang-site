#!/usr/bin/env python3
"""Merge split Figma MCP export JSON parts into inbox/figma-vars-full.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox" / "figma-vars-full.json"
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("usage: merge_figma_export_parts.py <head.json> <collection.json> ...")

    head = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    collections = []
    for path in sys.argv[2:]:
        collections.append(json.loads(Path(path).read_text(encoding="utf-8")))
    head["collections"] = collections
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    INBOX.write_text(json.dumps(head, indent=2) + "\n", encoding="utf-8")
    SNAPSHOT.write_text(json.dumps(head, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {INBOX} and {SNAPSHOT}")
    print(
        "counts:",
        head.get("counts"),
        "textStyles:",
        len(head.get("textStyles", [])),
    )


if __name__ == "__main__":
    main()
