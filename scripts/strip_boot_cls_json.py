#!/usr/bin/env python3
"""Strip accidental stderr prefix from boot CLS JSON captures (stdout must be JSON only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "docs" / "reviews" / "boot-cls-2026-10-15"
FILES = ("cls-before.json", "cls-after.json")


def load_array(text: str) -> list[object]:
    start = text.find("[")
    if start < 0:
        raise ValueError("missing JSON array")
    return json.loads(text[start:])


def main() -> None:
    for name in FILES:
        path = DIR / name
        raw = path.read_text(encoding="utf-8")
        if raw.lstrip().startswith("["):
            data = json.loads(raw)
        else:
            data = load_array(raw)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"normalized {name} ({len(data)} rows)")
    print("strip_boot_cls_json ok")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
