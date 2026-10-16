#!/usr/bin/env python3
"""Write inbox/mcp-head.json and inbox/mcp-color.json from live MCP values (2026-10-16)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"
INBOX = ROOT / "inbox"

NEW_COLORS = [
    {
        "name": "color/danger-text",
        "type": "COLOR",
        "scopes": ["TEXT_FILL"],
        "values": {
            "Dark": {"resolved": "#e09b88"},
            "Light": {"resolved": "#79352b"},
        },
    },
    {
        "name": "color/success-text",
        "type": "COLOR",
        "scopes": ["TEXT_FILL"],
        "values": {
            "Dark": {"resolved": "#8cbd9a"},
            "Light": {"resolved": "#244f35"},
        },
    },
    {
        "name": "color/warning-text",
        "type": "COLOR",
        "scopes": ["TEXT_FILL"],
        "values": {
            "Dark": {"resolved": "#e2bc70"},
            "Light": {"resolved": "#60420f"},
        },
    },
]

HEAD = {
    "fileKey": "xr2asASU4M8amldS2Lm0hQ",
    "fileUrl": "https://www.figma.com/design/xr2asASU4M8amldS2Lm0hQ",
    "exportedAt": "2026-10-16T06:40:34.713+08:00 (SGT)",
    "counts": {
        "collections": 7,
        "variables": 109,
        "textStyles": 30,
        "perCollection": {
            "Color": {"variables": 46, "modes": ["Dark", "Light"]},
            "Type": {"variables": 25, "modes": ["Value"]},
            "Spacing": {
                "variables": 21,
                "modes": ["Desktop (>48rem, @1280)", "Compact (<=48rem)"],
            },
            "Radius": {"variables": 3, "modes": ["Value"]},
            "Motion": {"variables": 3, "modes": ["Value"]},
            "Text Scale": {
                "variables": 1,
                "modes": [
                    "Base (<1280)",
                    ">=1280px",
                    ">=1440px",
                    "Reading large",
                    "Reading xlarge",
                ],
            },
            "Breakpoint": {"variables": 10, "modes": ["Value"]},
        },
    },
}


def main() -> None:
    old = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    color = next(c for c in old["collections"] if c["name"] == "Color")
    by_name = {v["name"]: v for v in color["variables"]}
    for var in NEW_COLORS:
        by_name[var["name"]] = var
    color = dict(color)
    color["variables"] = [by_name[name] for name in sorted(by_name)]
    INBOX.mkdir(parents=True, exist_ok=True)
    (INBOX / "mcp-head.json").write_text(
        json.dumps(HEAD, indent=2) + "\n", encoding="utf-8"
    )
    (INBOX / "mcp-color.json").write_text(
        json.dumps(color, indent=2) + "\n", encoding="utf-8"
    )
    print("wrote inbox/mcp-head.json and inbox/mcp-color.json")


if __name__ == "__main__":
    main()
