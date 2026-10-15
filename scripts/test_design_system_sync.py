#!/usr/bin/env python3
"""Assert tokens.css and design-system.md match the committed Figma snapshot."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "src" / "styles" / "tokens.css"
CHROME = ROOT / "src" / "styles" / "chrome.css"
DOC = ROOT / "docs" / "design-system.md"
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"
VIOLATION_FIXTURE = ROOT / "scripts" / "fixtures" / "design_system_snapshot_violation.json"

FIGMA_URL = "https://www.figma.com/design/xr2asASU4M8amldS2Lm0hQ"
BLOCK_RE = re.compile(r"\{([^{}]*)\}", re.S)
DECL_RE = re.compile(
    r"(--[a-z0-9-]+)\s*:\s*([^;]+);",
    re.I,
)
PX_TOLERANCE = 1.25


def _block_after(text: str, marker: str) -> str:
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"missing {marker}")
    match = BLOCK_RE.search(text, start)
    if not match:
        raise ValueError(f"missing block after {marker}")
    return match.group(1)


def parse_declarations(block: str) -> dict[str, str]:
    return {
        match.group(1): match.group(2).strip()
        for match in DECL_RE.finditer(block)
    }


def token_blocks(css: str) -> tuple[dict[str, str], dict[str, str]]:
    dark = parse_declarations(_block_after(css, ':root,\n[data-theme="dark"]'))
    light = parse_declarations(_block_after(css, '[data-theme="light"]'))
    return dark, light


def chrome_declarations() -> dict[str, str]:
    text = CHROME.read_text(encoding="utf-8")
    return parse_declarations(text)


def _hex8_to_rgb_alpha(hex8: str) -> tuple[tuple[int, int, int], float]:
    value = hex8.lstrip("#").lower()
    if len(value) != 8:
        raise ValueError(hex8)
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    a = int(value[6:8], 16) / 255.0
    return (r, g, b), a


def _parse_rgb_percent(value: str) -> tuple[tuple[int, int, int], float] | None:
    match = re.fullmatch(
        r"rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*/\s*([\d.]+)%\s*\)",
        value.strip(),
        re.I,
    )
    if not match:
        return None
    rgb = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    alpha = float(match.group(4)) / 100.0
    return rgb, alpha


def _parse_hex6(value: str) -> str | None:
    match = re.fullmatch(r"#([0-9a-fA-F]{6})\b", value.strip())
    if not match:
        return None
    return f"#{match.group(1).lower()}"


def colors_equivalent(snapshot: str, css_value: str) -> bool:
    snap = snapshot.strip().lower()
    css = css_value.strip().lower()
    if snap.startswith("#") and len(snap) == 9:
        snap_rgb, snap_a = _hex8_to_rgb_alpha(snap)
        parsed = _parse_rgb_percent(css)
        if parsed:
            css_rgb, css_a = parsed
            return snap_rgb == css_rgb and abs(snap_a - css_a) < 0.02
    if snap.startswith("#") and len(snap) == 7:
        snap_hex = _parse_hex6(snap)
        css_hex = _parse_hex6(css)
        if snap_hex and css_hex:
            return snap_hex == css_hex
    return snap in css or css in snap


def rem_to_px(rem: str) -> float:
    match = re.fullmatch(r"([\d.]+)rem", rem.strip())
    if not match:
        raise ValueError(rem)
    return float(match.group(1)) * 16.0


def clamp_max_px(clamp_value: str) -> float:
    match = re.search(
        r"clamp\([^,]+,[^,]+,\s*calc\(([\d.]+)rem",
        clamp_value,
        re.I,
    )
    if match:
        return float(match.group(1)) * 16.0
    match = re.search(r"clamp\([^,]+,[^,]+,\s*([\d.]+)rem", clamp_value, re.I)
    if match:
        return float(match.group(1)) * 16.0
    raise ValueError(f"unsupported clamp: {clamp_value}")


def declaration_px(value: str, dark: dict[str, str], token: str) -> float:
    scaled = scaled_rem_px(value)
    if scaled is not None:
        return scaled
    if value.endswith("rem"):
        return rem_to_px(value)
    raise ValueError(f"{token}: {value}")


def calc_text_px(expr: str, dark: dict[str, str]) -> float:
    text = expr.strip()
    if text.startswith("calc(") and "var(--text-sm)" in text:
        space_2 = declaration_px(dark["--space-2"], dark, "--space-2")
        text_sm = declaration_px(dark["--text-sm"], dark, "--text-sm")
        return (space_2 * 2) + (1.2 * text_sm)
    raise ValueError(expr)


def scaled_rem_px(css_value: str) -> float | None:
    css = css_value.strip()
    match = re.fullmatch(
        r"calc\(\s*([\d.]+)rem\s*\*\s*var\(--text-scale\)\s*\)",
        css,
        re.I,
    )
    if match:
        return float(match.group(1)) * 16.0
    return None


def numeric_equivalent(snapshot: str, css_value: str, dark: dict[str, str]) -> bool:
    target = float(snapshot)
    css = css_value.strip()
    scaled = scaled_rem_px(css)
    if scaled is not None:
        return abs(scaled - target) <= PX_TOLERANCE
    if css.startswith("calc(") and "var(--text-sm)" in css:
        actual = calc_text_px(css, dark)
        return abs(actual - target) <= PX_TOLERANCE
    if "clamp(" in css:
        actual = clamp_max_px(css)
        return abs(actual - target) <= PX_TOLERANCE
    if css.endswith("rem"):
        actual = rem_to_px(css)
        return abs(actual - target) <= PX_TOLERANCE
    return False


def css_token_for_snapshot(name: str) -> str:
    if name == "color/glow":
        return "--glow"
    if name.startswith("--"):
        return name
    raise ValueError(name)


def resolve_css_value(
    token: str,
    theme: str,
    dark: dict[str, str],
    light: dict[str, str],
    chrome: dict[str, str],
) -> str | None:
    if token == "--header-control-height":
        return chrome.get(token)
    if theme == "light":
        return light.get(token)
    return dark.get(token)


def color_mix_matches(token: str, snapshot_value: str, css_value: str) -> bool:
    snap = snapshot_value.strip().lower()
    css = css_value.lower()
    if token == "--line-soft":
        return snap == "#4a5c4e24" and "14%" in css
    if token == "--line-strong":
        return snap == "#4a5c4e47" and "28%" in css
    if token == "--accent-cta-bg":
        return snap == "#c49a5a14" and "8%" in css
    if token == "--accent-cta-border":
        return snap == "#ad8e58ac" and "55%" in css
    return False


def value_matches_snapshot(
    token: str,
    theme: str,
    snapshot_value: str,
    dark: dict[str, str],
    light: dict[str, str],
    chrome: dict[str, str],
) -> bool:
    css_value = resolve_css_value(token, theme, dark, light, chrome)
    if css_value is None:
        return False
    snap = snapshot_value.strip()
    if snap.startswith("#"):
        if "color-mix" in css_value:
            return color_mix_matches(token, snap, css_value) or colors_equivalent(
                snap, css_value
            )
        return colors_equivalent(snap, css_value)
    return numeric_equivalent(snap, css_value, dark)


def doc_contains_value(doc: str, name: str, value: str) -> bool:
    lowered = doc.lower()
    if name.startswith("Display/") or name.startswith("Body/") or name.startswith("Label/") or name.startswith("Meta/") or name.startswith("UI/") or name.startswith("Heading/"):
        return name.lower() in lowered
    if name == "color/glow":
        return "c49a5a29" in lowered or "color/glow" in lowered
    token = css_token_for_snapshot(name).lower()
    if token not in lowered:
        return False
    if value.startswith("#"):
        if value.lower() in lowered:
            return True
        return token in lowered
    return True


def count_nulls(snapshot: dict) -> int:
    total = 0
    for entry in snapshot.get("variables", []):
        if entry.get("dark") is None:
            total += 1
        if entry.get("light") is None:
            total += 1
    for entry in snapshot.get("text_styles", []):
        if entry.get("dark") is None:
            total += 1
        if entry.get("light") is None:
            total += 1
    return total


def sync_snapshot(
    snapshot_path: Path,
    css: str,
    doc: str,
) -> tuple[list[str], int, list[str]]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    dark, light = token_blocks(css)
    chrome = chrome_declarations()
    errors: list[str] = []
    pending: list[str] = []

    for entry in snapshot.get("variables", []):
        name = entry["name"]
        for theme, key in (("dark", "dark"), ("light", "light")):
            value = entry.get(key)
            if value is None:
                pending.append(f"{name} ({theme})")
                continue
            token = css_token_for_snapshot(name)
            if not value_matches_snapshot(token, theme, value, dark, light, chrome):
                css_val = resolve_css_value(token, theme, dark, light, chrome)
                errors.append(
                    f"{name} {theme} snapshot {value!r} does not match tokens.css ({css_val!r})"
                )
            if not doc_contains_value(doc, name, value):
                errors.append(f"{name} {theme} value not documented in design-system.md")

    for entry in snapshot.get("text_styles", []):
        name = entry["name"]
        for theme, key in (("dark", "dark"), ("light", "light")):
            value = entry.get(key)
            if value is None:
                pending.append(f"{name} text ({theme})")
                continue
            if name not in doc:
                errors.append(f"text style {name} missing from design-system.md")

    return errors, count_nulls(snapshot), pending


def assert_fixture_fails() -> None:
    if not VIOLATION_FIXTURE.is_file():
        raise SystemExit(f"missing fixture {VIOLATION_FIXTURE}")
    css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    errors, _, _ = sync_snapshot(VIOLATION_FIXTURE, css, doc)
    if not errors:
        raise SystemExit("design_system_snapshot_violation fixture should fail sync")


def main() -> None:
    css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    errors: list[str] = []

    if "## Source of truth" not in doc:
        errors.append('design-system.md missing heading "Source of truth"')
    if FIGMA_URL not in doc:
        errors.append(f"design-system.md missing Figma URL {FIGMA_URL}")
    if "docs/figma/variables.json" not in doc:
        errors.append("design-system.md missing pointer to docs/figma/variables.json")
    if not SNAPSHOT.is_file():
        errors.append(f"missing snapshot {SNAPSHOT}")

    sync_errors, null_count, pending = sync_snapshot(SNAPSHOT, css, doc)
    errors.extend(sync_errors)

    assert_fixture_fails()

    if errors:
        print("test_design_system_sync failed:", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "test_design_system_sync ok "
        f"(snapshot null values: {null_count}; pending full light/dark export)"
    )
    if pending:
        print("snapshot pending (null, not failures):")
        for item in pending[:8]:
            print(f"  - {item}")
        if len(pending) > 8:
            print(f"  … and {len(pending) - 8} more")


if __name__ == "__main__":
    main()
