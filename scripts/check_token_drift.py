#!/usr/bin/env python3
"""Fail CI if a raw hex color or font-family literal sneaks into a CSS file
other than tokens.css. Cheap insurance against a hardcoded value bypassing
the design-token system documented in docs/design-system.md.

This is intentionally narrow: it does not check font-size/spacing/radius
(stylelint's scale-unlimited/declaration-strict-value rule owns that, see
.stylelintrc.json) — just the two things a regex can check reliably without
false positives: hex colors and named font-family strings.
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

# rgba()/rgb() literals are not flagged here: several are legitimate
# one-off overlays (shadows, scrims) rather than palette colors, and a
# blanket ban would need its own allow-list. Hex colors are a much
# stronger signal of "someone typed a palette color instead of a token."


def find_violations() -> list[str]:
    violations: list[str] = []
    for css_file in sorted(STYLES_DIR.glob("*.css")):
        if css_file == TOKENS_FILE:
            continue
        text = css_file.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("/*") or stripped.startswith("*"):
                continue
            for m in HEX_COLOR_RE.finditer(line):
                violations.append(
                    f"{css_file.relative_to(ROOT)}:{lineno}: raw hex color {m.group(0)!r} "
                    f"outside tokens.css — add a token instead"
                )
            if FONT_FAMILY_LITERAL_RE.search(line):
                violations.append(
                    f"{css_file.relative_to(ROOT)}:{lineno}: font-family set without "
                    f"var(--font-*) — use --font-display / --font-body from tokens.css"
                )
    return violations


def main() -> None:
    if not TOKENS_FILE.is_file():
        print(f"check_token_drift error: missing {TOKENS_FILE}", file=sys.stderr)
        raise SystemExit(1)

    violations = find_violations()
    if violations:
        print("check_token_drift: found raw values outside tokens.css:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        raise SystemExit(1)

    print("check_token_drift ok")


if __name__ == "__main__":
    main()
