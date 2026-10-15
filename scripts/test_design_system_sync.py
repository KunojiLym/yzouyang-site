#!/usr/bin/env python3
"""Assert design-system.md token tables mirror tokens.css hex values."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "src" / "styles" / "tokens.css"
DOC = ROOT / "docs" / "design-system.md"

HEX_DECL_RE = re.compile(r"--[a-z0-9-]+\s*:\s*(#[0-9a-fA-F]{3,8})\b")
BLOCK_RE = re.compile(r"\{([^{}]*)\}", re.S)
FIGMA_URL = "https://www.figma.com/design/xr2asASU4M8amldS2Lm0hQ"


def _block_after(text: str, marker: str) -> str:
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"missing {marker}")
    match = BLOCK_RE.search(text, start)
    if not match:
        raise ValueError(f"missing block after {marker}")
    return match.group(1)


def hex_tokens(css: str) -> dict[str, set[str]]:
    dark = _block_after(css, ':root,\n[data-theme="dark"]')
    light = _block_after(css, '[data-theme="light"]')
    return {
        "dark": {match.group(1).lower() for match in HEX_DECL_RE.finditer(dark)},
        "light": {match.group(1).lower() for match in HEX_DECL_RE.finditer(light)},
    }


def table_lines(markdown: str) -> list[str]:
    return [line.lower() for line in markdown.splitlines() if line.strip().startswith("|")]


def main() -> None:
    css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    errors: list[str] = []

    if "## Source of truth" not in doc:
        errors.append('design-system.md missing heading "Source of truth"')
    if FIGMA_URL not in doc:
        errors.append(f"design-system.md missing Figma URL {FIGMA_URL}")

    tables = "\n".join(table_lines(doc))
    found = hex_tokens(css)
    for theme, hexes in found.items():
        if not hexes:
            errors.append(f"parsed no {theme} hex tokens from tokens.css")
        for value in sorted(hexes):
            if value not in tables:
                errors.append(f"{theme} token {value} is missing from design-system.md token tables")

    if errors:
        print("test_design_system_sync failed:", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "test_design_system_sync ok "
        f"(dark {len(found['dark'])}, light {len(found['light'])})"
    )


if __name__ == "__main__":
    main()
