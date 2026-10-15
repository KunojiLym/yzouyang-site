#!/usr/bin/env python3
"""Assert tokens.css and design-system.md match docs/figma/variables.json."""

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
DECL_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", re.I)
HEX_DECL_RE = re.compile(r"--[a-z0-9-]+\s*:\s*(#[0-9a-fA-F]{3,8})\b")
PX_TOLERANCE = 1.25

COLOR_MIX_TOKENS = frozenset(
    {
        "--line-soft",
        "--line-strong",
        "--accent-cta-bg",
        "--accent-cta-border",
    }
)

# CSS / design-system.md — must match Figma snapshot except TEXT_STYLE_FIGMA_CSS_GAPS.
DOC_TEXT_STYLE_SPEC: dict[str, dict[str, object]] = {
    "Display/Hero": {
        "font_size": "font-size/text-display-hero/max",
        "font_weight": 600,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Display/H1": {
        "font_size": "font-size/text-display-1/max",
        "font_weight": 600,
        "letter_spacing_pct": -2,
        "text_case": "ORIGINAL",
    },
    "Display/H2": {
        "font_size": "font-size/text-display-3/max",
        "font_weight": 600,
    },
    "Display/Brand": {
        "font_size": "font-size/text-xl",
        "font_weight": 600,
        "letter_spacing_pct": -2,
        "text_case": "ORIGINAL",
    },
    "Display/Record Title": {
        "font_size": "font-size/text-md",
        "font_weight": 600,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Display/Practice Title": {
        "font_size": "font-size/text-sm",
        "font_weight": 600,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Display/Dropcap": {
        "font_size": "font-size/text-dropcap/max",
        "font_weight": 600,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Heading/H3": {
        "font_size": "font-size/text-lg",
        "font_weight": 600,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Label/Caps": {
        "font_size": "font-size/text-xs",
        "font_weight": 600,
        "letter_spacing_pct": 8,
        "text_case": "UPPER",
    },
    "Label/Xs Caps": {
        "font_size": "font-size/text-xs",
        "font_weight": 400,
        "letter_spacing_pct": 8,
        "text_case": "UPPER",
    },
    "Label/Xs Group": {
        "font_size": "font-size/text-xs",
        "font_weight": 600,
        "letter_spacing_pct": 8,
        "text_case": "UPPER",
    },
    "Label/Xs Group Light": {
        "font_size": "font-size/text-xs",
        "font_weight": 400,
        "letter_spacing_pct": 2,
        "text_case": "ORIGINAL",
    },
    "Body/Base": {
        "font_size": "font-size/text-base",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Body/Large": {
        "font_size": "font-size/text-lg",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Body/Proof": {
        "font_size": "font-size/text-proof/max",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Body/Small": {
        "font_size": "font-size/text-sm",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Body/Small Strong": {
        "font_size": "font-size/text-sm",
        "font_weight": 600,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Body/Prose": {
        "font_size": "font-size/text-md",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Body/Blockquote": {
        "font_size": "font-size/text-lg",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Meta/Small": {
        "font_size": "font-size/text-sm",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Meta/Xs": {
        "font_size": "font-size/text-xs",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "Meta/Record Domains": {
        "font_size": "font-size/text-xs",
        "font_weight": 400,
        "letter_spacing_pct": 4,
        "text_case": "ORIGINAL",
    },
    "Meta/Map Node Label": {
        "font_size": "font-size/text-xs",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
    "UI/Control": {
        "font_size": "font-size/text-sm",
        "font_weight": 400,
        "letter_spacing_pct": 0,
        "text_case": "ORIGINAL",
    },
}

TEXT_STYLE_FIGMA_CSS_GAPS = frozenset(
    {
        "Display/H2",
        "Label/Xs Caps",
        "Label/Xs Group",
    }
)

FIGMA_TEXT_STYLE_SNAPSHOT: dict[str, dict[str, object]] = {
    "Display/H2": {
        "font_size": "font-size/text-display-2/max",
        "font_weight": 600,
        "letter_spacing_pct": -1,
        "text_case": "ORIGINAL",
    },
    "Label/Xs Caps": {
        "font_size": "font-size/text-xs",
        "font_weight": 400,
        "letter_spacing_pct": 6,
        "text_case": "UPPER",
    },
    "Label/Xs Group": {
        "font_size": "font-size/text-xs",
        "font_weight": 600,
        "letter_spacing_pct": 2,
        "text_case": "ORIGINAL",
    },
}


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


def theme_maps(css: str) -> tuple[dict[str, str], dict[str, str]]:
    dark = parse_declarations(_block_after(css, ':root,\n[data-theme="dark"]'))
    light = parse_declarations(_block_after(css, '[data-theme="light"]'))
    return dark, light


def merged_theme(dark: dict[str, str], light: dict[str, str], theme: str) -> dict[str, str]:
    base = dict(dark)
    if theme == "light":
        base.update(light)
    return base


def resolve_css_token(
    token: str,
    dark: dict[str, str],
    light: dict[str, str],
    theme: str,
    depth: int = 0,
) -> str | None:
    if depth > 8:
        return None
    block = merged_theme(dark, light, theme)
    value = block.get(token)
    if value is None:
        return None
    if value.startswith("var("):
        return resolve_css_token(value[4:-1].strip(), dark, light, theme, depth + 1)
    return value


def _hex_channels(hex_color: str) -> tuple[int, int, int, float]:
    value = hex_color.lstrip("#").lower()
    if len(value) == 6:
        value += "ff"
    if len(value) != 8:
        raise ValueError(hex_color)
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    a = int(value[6:8], 16) / 255.0
    return r, g, b, a


def _parse_rgb_percent(value: str) -> tuple[int, int, int, float] | None:
    match = re.fullmatch(
        r"rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*/\s*([\d.]+)%\s*\)",
        value.strip(),
        re.I,
    )
    if not match:
        return None
    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        float(match.group(4)) / 100.0,
    )


def colors_equivalent(figma: str, css_value: str) -> bool:
    fig = figma.strip().lower()
    css = css_value.strip().lower()
    if fig == css:
        return True
    if fig.startswith("#"):
        fr, fg, fb, fa = _hex_channels(fig)
        parsed = _parse_rgb_percent(css)
        if parsed:
            cr, cg, cb, ca = parsed
            return (fr, fg, fb) == (cr, cg, cb) and abs(fa - ca) < 0.025
        hex6 = re.fullmatch(r"#([0-9a-f]{6})\b", css)
        if hex6 and len(fig) >= 7:
            return fig[:7] == f"#{hex6.group(1)}"
    return False


def scaled_rem_px(css_value: str) -> float | None:
    match = re.fullmatch(
        r"calc\(\s*([\d.]+)rem\s*\*\s*var\(--text-scale\)\s*\)",
        css_value.strip(),
        re.I,
    )
    if match:
        return float(match.group(1)) * 16.0
    return None


def clamp_min_px(css_value: str) -> float | None:
    match = re.search(
        r"clamp\(\s*calc\(([\d.]+)rem",
        css_value,
        re.I,
    )
    if match:
        return float(match.group(1)) * 16.0
    match = re.search(r"clamp\(\s*([\d.]+)rem", css_value, re.I)
    if match:
        return float(match.group(1)) * 16.0
    return None


def token_px(token: str, dark: dict[str, str]) -> float | None:
    raw = dark.get(token)
    if raw is None:
        return None
    scaled = scaled_rem_px(raw)
    if scaled is not None:
        return scaled
    if raw.strip().endswith("rem"):
        return float(raw.strip()[:-3]) * 16.0
    return None


def numeric_px(css_value: str, dark: dict[str, str]) -> float | None:
    scaled = scaled_rem_px(css_value)
    if scaled is not None:
        return scaled
    if css_value.strip().endswith("rem"):
        return float(css_value.strip()[:-3]) * 16.0
    if "clamp(" in css_value:
        match = re.search(
            r"clamp\([^,]+,[^,]+,\s*calc\(([\d.]+)rem",
            css_value,
            re.I,
        )
        if match:
            return float(match.group(1)) * 16.0
        match = re.search(r"clamp\([^,]+,[^,]+,\s*([\d.]+)rem", css_value, re.I)
        if match:
            return float(match.group(1)) * 16.0
    if css_value.strip().startswith("calc(") and "var(--text-sm)" in css_value:
        space_2 = token_px("--space-2", dark)
        text_sm = token_px("--text-sm", dark)
        if space_2 is None or text_sm is None:
            return None
        return (space_2 * 2) + (1.2 * text_sm)
    return None


def css_token_from_web(web: str | None) -> str | None:
    if web and web.startswith("var("):
        return web[4:-1].strip()
    return None


SYNC_COLLECTIONS = frozenset({"Color", "Type", "Spacing", "Radius", "Motion"})


def figma_modes(collection: dict) -> list[tuple[str, str]]:
    name = collection["name"]
    modes = collection["modes"]
    if name not in SYNC_COLLECTIONS:
        return []
    if name == "Color":
        return [("dark", "Dark"), ("light", "Light")]
    if name == "Spacing":
        return [("desktop", "Desktop (>48rem, @1280)")]
    if len(modes) == 1:
        return [("value", modes[0])]
    return []


def theme_for_css_mode(css_mode: str) -> str:
    if css_mode == "light":
        return "light"
    return "dark"


def normalize_font_stack(value: str) -> str:
    return re.sub(r'"', "", value.lower().replace(" ", ""))


def color_mix_matches(
    token: str, snapshot_hex: str, css_value: str, theme: str = "dark"
) -> bool:
    snap = snapshot_hex.strip().lower()
    css = css_value.lower().replace(" ", "")
    if token == "--line-soft":
        expected = "#4a5c4e24" if theme == "dark" else "#4a5c4e1f"
        pct = "14%" if theme == "dark" else "12%"
        return snap == expected and "var(--rail-green)" in css and pct in css
    if token == "--line-strong":
        expected = "#4a5c4e47" if theme == "dark" else "#4a5c4e38"
        pct = "28%" if theme == "dark" else "22%"
        return snap == expected and "var(--rail-green)" in css and pct in css
    if token == "--accent-cta-bg":
        return snap == "#c49a5a14" and "var(--accent)" in css and "8%" in css
    if token == "--accent-cta-border":
        return (
            snap == "#ad8e58ac"
            and "55%" in css
            and "var(--accent)" in css
            and "var(--line-strong)" in css
        )
    return False


def _style_letter_spacing_pct(style: dict) -> float | None:
    ls = style.get("letterSpacing") or {}
    if ls.get("unit") == "PERCENT" and "value" in ls:
        return float(ls["value"])
    return None


def _style_matches_spec(style: dict, spec: dict[str, object]) -> list[str]:
    errors: list[str] = []
    bound = (style.get("boundVariables") or {}).get("fontSize")
    expected_fs = spec.get("font_size")
    if expected_fs and bound != expected_fs:
        errors.append(f"fontSize {bound!r} != {expected_fs!r}")
    if "font_weight" in spec and style.get("fontWeight") != spec["font_weight"]:
        errors.append(f"fontWeight {style.get('fontWeight')} != {spec['font_weight']}")
    if "letter_spacing_pct" in spec:
        actual = _style_letter_spacing_pct(style)
        expected = spec["letter_spacing_pct"]
        if actual is None or abs(actual - float(expected)) > 0.01:
            errors.append(f"letterSpacing {actual} != {expected}")
    if "text_case" in spec and style.get("textCase") != spec["text_case"]:
        errors.append(f"textCase {style.get('textCase')} != {spec['text_case']}")
    return errors


def validate_text_styles(snapshot: dict, doc: str) -> list[str]:
    errors: list[str] = []
    if "Text style drift" not in doc:
        errors.append('design-system.md missing "Text style drift" under Known Figma gaps')
    by_name = {item["name"]: item for item in snapshot.get("textStyles", [])}
    for name, spec in DOC_TEXT_STYLE_SPEC.items():
        style = by_name.get(name)
        if style is None:
            errors.append(f"text style {name} missing from snapshot")
            continue
        if name not in doc:
            errors.append(f"text style {name} missing from design-system.md")
        if name in TEXT_STYLE_FIGMA_CSS_GAPS:
            figma_spec = FIGMA_TEXT_STYLE_SNAPSHOT[name]
            for detail in _style_matches_spec(style, figma_spec):
                errors.append(f"{name} snapshot drift: {detail}")
            continue
        for detail in _style_matches_spec(style, spec):
            errors.append(f"{name} vs doc/CSS spec: {detail}")
    return errors


def value_matches(
    figma_name: str,
    css_mode: str,
    figma_value: object,
    css_token: str,
    dark: dict[str, str],
    light: dict[str, str],
    chrome: dict[str, str],
    snapshot: dict,
) -> bool:
    theme = theme_for_css_mode(css_mode)
    if css_token in chrome:
        css_value = chrome[css_token]
    else:
        css_value = resolve_css_token(css_token, dark, light, theme)
    if css_value is None:
        return False

    if css_token == "--code-border":
        line_token = "--line-strong" if theme == "dark" else "--line-soft"
        line_css = resolve_css_token(line_token, dark, light, theme)
        if isinstance(figma_value, str) and line_css:
            if colors_equivalent(figma_value, line_css):
                return True
            if line_token in COLOR_MIX_TOKENS and "color-mix" in line_css:
                return color_mix_matches(line_token, figma_value, line_css, theme)

    if isinstance(figma_value, str) and figma_value.startswith("#"):
        if colors_equivalent(figma_value, css_value):
            return True
        if css_token in COLOR_MIX_TOKENS and "color-mix" in css_value:
            return color_mix_matches(css_token, figma_value, css_value, theme)
        if css_value.startswith("var("):
            inner = css_token_from_web(css_value)
            if inner in COLOR_MIX_TOKENS:
                return True
        return False

    if figma_name.endswith("/min") and "clamp(" in css_value:
        px = clamp_min_px(css_value)
        if px is not None and isinstance(figma_value, (int, float)):
            return abs(px - float(figma_value)) <= PX_TOLERANCE

    if figma_name.endswith("/max") and "clamp(" in css_value:
        px = numeric_px(css_value, dark)
        if px is not None and isinstance(figma_value, (int, float)):
            return abs(px - float(figma_value)) <= PX_TOLERANCE

    if isinstance(figma_value, (int, float)):
        if css_token.startswith("--dur-") and css_value.endswith("ms"):
            return int(figma_value) == int(css_value.replace("ms", "").strip())
        if css_token.startswith("--lh-") or css_token == "--note-read-lead":
            return abs(float(figma_value) - float(css_value.strip())) < 0.01
        if css_token == "--track-caps" and css_value.endswith("em"):
            return abs(float(figma_value) - float(css_value.replace("em", ""))) < 0.01
        px = numeric_px(css_value, dark)
        if px is not None:
            return abs(px - float(figma_value)) <= PX_TOLERANCE
        return abs(float(figma_value) - float(css_value.strip())) < 0.01

    if css_token.startswith("--font-"):
        return normalize_font_stack(str(figma_value)) == normalize_font_stack(css_value)

    return str(figma_value) == css_value


def iter_snapshot_bindings(snapshot: dict) -> list[tuple[str, str, str, object]]:
    rows: list[tuple[str, str, str, object]] = []
    for collection in snapshot.get("collections", []):
        for var in collection.get("variables", []):
            token = css_token_from_web(var.get("web"))
            if not token:
                continue
            for css_mode, figma_mode in figma_modes(collection):
                resolved = var["values"][figma_mode].get("resolved")
                if resolved is None:
                    continue
                rows.append((var["name"], css_mode, token, resolved))
    return rows


def sync_snapshot(
    snapshot_path: Path,
    css: str,
    doc: str,
) -> tuple[list[str], list[str]]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    dark, light = theme_maps(css)
    chrome = parse_declarations(CHROME.read_text(encoding="utf-8"))
    errors: list[str] = []

    for figma_name, css_mode, token, resolved in iter_snapshot_bindings(snapshot):
        theme = theme_for_css_mode(css_mode)
        if not value_matches(
            figma_name, css_mode, resolved, token, dark, light, chrome, snapshot
        ):
            css_show = chrome.get(token) or resolve_css_token(token, dark, light, theme)
            errors.append(
                f"{figma_name} [{css_mode}] snapshot {resolved!r} "
                f"≠ tokens.css {token} ({css_show!r})"
            )
    errors.extend(validate_text_styles(snapshot, doc))

    return errors


def hex_tokens_in_doc(css: str, doc: str) -> list[str]:
    errors: list[str] = []
    dark = _block_after(css, ':root,\n[data-theme="dark"]')
    light = _block_after(css, '[data-theme="light"]')
    tables = "\n".join(
        line.lower() for line in doc.splitlines() if line.strip().startswith("|")
    )
    for block, theme in ((dark, "dark"), (light, "light")):
        for match in HEX_DECL_RE.finditer(block):
            if match.group(1).lower() not in tables:
                errors.append(f"{theme} token {match.group(1).lower()} missing from doc tables")
    return errors


def assert_fixture_fails() -> None:
    if not VIOLATION_FIXTURE.is_file():
        raise SystemExit(f"missing fixture {VIOLATION_FIXTURE}")
    css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    errors = sync_snapshot(VIOLATION_FIXTURE, css, doc)
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

    errors.extend(sync_snapshot(SNAPSHOT, css, doc))
    errors.extend(hex_tokens_in_doc(css, doc))

    assert_fixture_fails()

    if errors:
        print("test_design_system_sync failed:", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    snapshot_data = json.loads(SNAPSHOT.read_text())
    print(
        "test_design_system_sync ok "
        f"(figma variables with web: {len(iter_snapshot_bindings(snapshot_data))}; "
        f"textStyles: {len(snapshot_data['textStyles'])})"
    )


if __name__ == "__main__":
    main()
