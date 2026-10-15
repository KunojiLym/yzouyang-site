#!/usr/bin/env python3
"""Fail CI if a raw hex color, palette rgb(), or font-family literal sneaks
into a CSS file other than tokens.css.

This is intentionally narrow: it does not check font-size/spacing/radius
(stylelint's scale-unlimited/declaration-strict-value rule owns that, see
.stylelintrc.json). Hex colors and named font-family strings are always
flagged. rgb()/rgba() literals are flagged outside tokens.css except for
overlay scrims on the allow-list. hsl(), oklch(), and named colors
are flagged outside tokens.css. Literal rgb inside color-mix() is flagged.
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
    r"rgba?\(\s*"
    r"(?:"
    r"(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})"
    r"|(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})"
    r"|(\d+(?:\.\d+)?%)\s+(\d+(?:\.\d+)?%)\s+(\d+(?:\.\d+)?%)"
    r")"
    r"(?:\s*/\s*[\d.]+%?)?\s*\)",
    re.IGNORECASE,
)
COLOR_MIX_RGB_RE = re.compile(
    r"color-mix\(\s*in\s+srgb\s*,\s*rgba?\([^)]+\)",
    re.IGNORECASE,
)
HSL_RE = re.compile(r"hsla?\(", re.IGNORECASE)
OKLCH_RE = re.compile(r"oklch\(", re.IGNORECASE)
NAMED_COLOR_RE = re.compile(
    r"(?<![\w-])(?:"
    r"aliceblue|antiquewhite|aqua|aquamarine|azure|beige|bisque|black|blanchedalmond|"
    r"blue|blueviolet|brown|burlywood|cadetblue|chartreuse|chocolate|coral|cornflowerblue|"
    r"cornsilk|crimson|cyan|darkblue|darkcyan|darkgoldenrod|darkgray|darkgreen|darkgrey|"
    r"darkkhaki|darkmagenta|darkolivegreen|darkorange|darkorchid|darkred|darksalmon|"
    r"darkseagreen|darkslateblue|darkslategray|darkslategrey|darkturquoise|darkviolet|"
    r"deeppink|deepskyblue|dimgray|dimgrey|dodgerblue|firebrick|floralwhite|forestgreen|"
    r"fuchsia|gainsboro|ghostwhite|gold|goldenrod|gray|green|greenyellow|grey|honeydew|"
    r"hotpink|indianred|indigo|ivory|khaki|lavender|lavenderblush|lawngreen|lemonchiffon|"
    r"lightblue|lightcoral|lightcyan|lightgoldenrodyellow|lightgray|lightgreen|lightgrey|"
    r"lightpink|lightsalmon|lightseagreen|lightskyblue|lightslategray|lightslategrey|"
    r"lightsteelblue|lightyellow|lime|limegreen|linen|magenta|maroon|mediumaquamarine|"
    r"mediumblue|mediumorchid|mediumpurple|mediumseagreen|mediumslateblue|mediumspringgreen|"
    r"mediumturquoise|mediumvioletred|midnightblue|mintcream|mistyrose|moccasin|navajowhite|"
    r"navy|oldlace|olive|olivedrab|orange|orangered|orchid|palegoldenrod|palegreen|"
    r"paleturquoise|palevioletred|papayawhip|peachpuff|peru|pink|plum|powderblue|purple|"
    r"rebeccapurple|red|rosybrown|royalblue|saddlebrown|salmon|sandybrown|seagreen|"
    r"seashell|sienna|silver|skyblue|slateblue|slategray|slategrey|snow|springgreen|"
    r"steelblue|tan|teal|thistle|tomato|turquoise|violet|wheat|white|whitesmoke|"
    r"yellow|yellowgreen"
    r")(?![\w-])",
    re.IGNORECASE,
)

# Overlays that are not palette tokens. 43 84 64 stays until Figma gap C9
# has a variable.
ALLOW_RGB = {
    (6, 5, 3),
    (0, 0, 0),
    (43, 84, 64),
}


def _rgb_channels_allowed(match: re.Match[str]) -> bool:
    groups = match.groups()
    if groups[0] is not None:
        channels = tuple(int(groups[i]) for i in range(3))
        return channels in ALLOW_RGB
    if groups[3] is not None:
        channels = tuple(int(groups[i]) for i in range(3, 6))
        return channels in ALLOW_RGB
    return False


def _iter_scannable_lines(text: str) -> list[tuple[int, str]]:
    """Yield (lineno, line) skipping comments (including ` * ` continuation lines)."""
    lines: list[tuple[int, str]] = []
    in_block = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if in_block:
            if "*/" in line:
                in_block = False
            continue
        if stripped.startswith("//"):
            continue
        if stripped.startswith("/*"):
            if "*/" not in line:
                in_block = True
            continue
        lines.append((lineno, line))
    return lines


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
        for lineno, line in _iter_scannable_lines(text):
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
            if HSL_RE.search(line):
                violations.append(
                    f"{_display(css_file)}:{lineno}: hsl() outside tokens.css — use a token"
                )
            if OKLCH_RE.search(line):
                violations.append(
                    f"{_display(css_file)}:{lineno}: oklch() outside tokens.css — use a token"
                )
            for match in NAMED_COLOR_RE.finditer(line):
                violations.append(
                    f"{_display(css_file)}:{lineno}: named color {match.group(0)!r} "
                    f"outside tokens.css — use a token"
                )
            for match in COLOR_MIX_RGB_RE.finditer(line):
                violations.append(
                    f"{_display(css_file)}:{lineno}: color-mix with raw rgb literal "
                    f"{match.group(0)!r} outside tokens.css — use a token or color-mix()"
                )
            for match in RGB_LITERAL_RE.finditer(line):
                if _rgb_channels_allowed(match):
                    continue
                violations.append(
                    f"{_display(css_file)}:{lineno}: rgb/rgba literal "
                    f"{match.group(0)!r} outside tokens.css — use a token or color-mix()"
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
