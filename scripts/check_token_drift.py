#!/usr/bin/env python3
"""Fail CI if a raw hex color, palette rgb(), or font-family literal sneaks
into a CSS file other than tokens.css.

This is intentionally narrow: it does not check font-size/spacing/radius
(stylelint's scale-unlimited/declaration-strict-value rule owns that, see
.stylelintrc.json). Hex colors and named font-family strings are always
flagged. rgb()/rgba() is flagged only when the channels match a palette
token. Overlay scrims stay on an allow-list.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES_DIR = ROOT / "src" / "styles"
TOKENS_FILE = STYLES_DIR / "tokens.css"

HEX_COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
FONT_FAMILY_LITERAL_RE = re.compile(r"font-family:(?!\s*var\()")
RGB_LITERAL_RE = re.compile(
    r"rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})"
    r"(?:[\s,]+(?:/)?\s*[\d.]+%?)?\s*\)",
    re.IGNORECASE,
)

# Channels that already have a token. A literal with these channels outside
# tokens.css is drift, whatever the alpha is.
PALETTE_RGB = {
    (196, 154, 90),  # --accent
    (212, 163, 92),  # --glow
    (168, 154, 136),  # retired muted
    (74, 92, 78),  # --rail-green / --line-*
    (61, 122, 94),  # retired record-domain green
}

# Overlays that are not palette tokens. 43 84 64 stays until Figma gap C9
# has a variable.
ALLOW_RGB = {
    (6, 5, 3),
    (0, 0, 0),
    (10, 11, 10),
    (232, 223, 208),
    (245, 239, 228),
    (43, 84, 64),
}


def find_violations(
    styles_dir: Path | None = None,
    tokens_file: Path | None = None,
) -> list[str]:
    styles_dir = styles_dir or STYLES_DIR
    tokens_file = tokens_file or (styles_dir / "tokens.css")
    violations: list[str] = []
    for css_file in sorted(styles_dir.glob("*.css")):
        if css_file.resolve() == tokens_file.resolve():
            continue
        text = css_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("/*") or stripped.startswith("*"):
                continue
            for match in HEX_COLOR_RE.finditer(line):
                violations.append(
                    f"{_display(css_file)}:{lineno}: raw hex color {match.group(0)!r} "
                    f"outside tokens.css — add a token instead"
                )
            if FONT_FAMILY_LITERAL_RE.search(line):
                violations.append(
                    f"{_display(css_file)}:{lineno}: font-family set without "
                    f"var(--font-*) — use --font-display / --font-body from tokens.css"
                )
            for match in RGB_LITERAL_RE.finditer(line):
                channels = tuple(int(part) for part in match.groups())
                if channels in ALLOW_RGB or channels not in PALETTE_RGB:
                    continue
                violations.append(
                    f"{_display(css_file)}:{lineno}: palette rgb {match.group(0)!r} "
                    f"outside tokens.css — use a token or color-mix()"
                )
    return violations


def _display(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> None:
    if not TOKENS_FILE.is_file():
        print(f"check_token_drift error: missing {TOKENS_FILE}", file=sys.stderr)
        raise SystemExit(1)

    violations = find_violations()
    if violations:
        print("check_token_drift: found raw values outside tokens.css:", file=sys.stderr)
        for item in violations:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    print("check_token_drift ok")


if __name__ == "__main__":
    main()
