#!/usr/bin/env python3
"""Stage a raw MCP merge under inbox/; run finalize_figma_mcp_snapshot.py for web + notes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox" / "figma-vars-full.json"


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit(
            "usage: merge_figma_export_parts.py <head.json> <collection.json> ..."
        )

    head = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    collections = []
    for path in sys.argv[2:]:
        collections.append(json.loads(Path(path).read_text(encoding="utf-8")))
    head["collections"] = collections
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    INBOX.write_text(json.dumps(head, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {INBOX} (raw merge, no web bindings)")
    print("Next: uv run python scripts/finalize_figma_mcp_snapshot.py")


if __name__ == "__main__":
    main()
