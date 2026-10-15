#!/usr/bin/env python3
"""Assert tokens.css and design-system.md match docs/figma/variables.json."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from design_system_color import colors_equivalent, computed_color_hex8

ROOT = Path(__file__).resolve().parents[1]
TOKENS = ROOT / "src" / "styles" / "tokens.css"
STYLES_DIR = ROOT / "src" / "styles"
CHROME = ROOT / "src" / "styles" / "chrome.css"
DOC = ROOT / "docs" / "design-system.md"
SNAPSHOT = ROOT / "docs" / "figma" / "variables.json"
VIOLATION_FIXTURE = ROOT / "scripts" / "fixtures" / "design_system_snapshot_violation.json"

FIGMA_URL = "https://www.figma.com/design/xr2asASU4M8amldS2Lm0hQ"
BLOCK_RE = re.compile(r"\{([^{}]*)\}", re.S)
DECL_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", re.I)
CSS_PROP_RE = re.compile(r"([a-z][a-z0-9-]*)\s*:\s*([^;]+);", re.I)
HEX_DECL_RE = re.compile(r"--[a-z0-9-]+\s*:\s*(#[0-9a-fA-F]{3,8})\b")
PX_TOLERANCE = 1.25
TEXT_STYLE_TABLE_HEADER = "| Figma style | Class | Face | Size / token | Weight / tracking |"
FIGMA_FONT_FAMILIES: dict[str, tuple[str, str]] = {
    "Crimson Pro": ("--font-display", "crimson pro"),
    "Source Sans 3": ("--font-body", "source sans 3"),
}
LINE_HEIGHT_TOLERANCE = 0.012
FONT_SIZE_PX_TOLERANCE = 1.5

# Named open CSS ↔ Figma gaps (must match docs/design-system.md Known Figma gaps).
TEXT_STYLE_OPEN_CSS_ITEMS: dict[tuple[str, str], dict[str, object]] = {
    ("Display/H2", "main.page h2"): {
        "reason": "Display/H2 Page size/tracking with Display/H2 line height",
        "skip_properties": frozenset(
            {"font-size", "font-size (px)", "font-size binding"}
        ),
    },
}

# Typography-table selectors with one documented export mismatch (Known Figma gaps).
# Unlike TEXT_STYLE_OPEN_CSS_ITEMS skip_properties, the selector still runs the full
# Figma export compare; only the named gap_property may diverge.
TEXT_STYLE_OPEN_MAPPING_GAPS: dict[tuple[str, str], dict[str, object]] = {}

DIST = ROOT / "dist"

COMPUTED_LH_ONLY_SELECTORS = frozenset(
    {".home-snap-proposition .lede", ".entrance .lede"}
)
DECL_LH_ONLY_SELECTORS = frozenset(
    {".home-record-title", ".home-practice-title"}
)

COMPUTE_LINE_HEIGHTS = ROOT / "scripts" / "compute_text_style_line_heights.mjs"

SYNC_COLLECTIONS = frozenset({"Color", "Type", "Spacing", "Radius", "Motion"})


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


def parse_css_properties(block: str) -> dict[str, str]:
    return {
        match.group(1).lower(): match.group(2).strip()
        for match in CSS_PROP_RE.finditer(block)
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
    if depth > 16:
        return None
    block = merged_theme(dark, light, theme)
    value = block.get(token)
    if value is None:
        return None
    trimmed = value.strip()
    if trimmed.startswith("var("):
        inner = trimmed[4:-1].strip()
        return resolve_css_token(inner, dark, light, theme, depth + 1)
    return trimmed


def make_color_resolver(
    dark: dict[str, str],
    light: dict[str, str],
    theme: str,
    chrome: dict[str, str],
) -> callable:
    block = merged_theme(dark, light, theme)

    def resolver(token: str) -> str | None:
        if token in chrome:
            return chrome[token]
        return block.get(token)

    return resolver


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


def css_token_for_variable(var: dict) -> str | None:
    token = css_token_from_web(var.get("web"))
    if token:
        return token
    web = (var.get("web") or "").strip()
    name = var.get("name") or ""
    if name.startswith("color/") and web.startswith("color-mix"):
        return "--" + name.removeprefix("color/").replace("/", "-")
    return None


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


SELECTOR_ALIASES: dict[str, str] = {
    ".note-body.prose .note-dropcap": ".note-body.prose > p:first-of-type::first-letter",
    ".library-index-group--depth-0": ".library-index-group--depth-0 > .library-index-group-label",
}


def parse_weight_column(cell: str) -> dict[str, object]:
    normalized = cell.replace("−", "-").replace("–", "-")
    normalized = re.sub(r"lh\s*[\d.]+\s*%?", "", normalized, flags=re.I)
    spec: dict[str, object] = {}
    weight_match = re.search(r"\b(\d{3})\b", normalized)
    if weight_match:
        spec["font_weight"] = int(weight_match.group(1))
    ls_match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", normalized)
    if ls_match:
        spec["letter_spacing_pct"] = float(ls_match.group(1))
    if re.search(r"\bcaps\b", normalized, re.I):
        spec["text_case"] = "UPPER"
    lh_match = re.search(r"\blh\s*([\d.]+)", normalized, re.I)
    if lh_match:
        spec["line_height"] = float(lh_match.group(1))
    return spec


def parse_text_style_table(doc: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start = doc.find(TEXT_STYLE_TABLE_HEADER)
    if start < 0:
        raise ValueError("missing Figma text style table in design-system.md")
    for line in doc[start:].splitlines()[1:]:
        if not line.strip().startswith("|"):
            break
        if re.match(r"^\|\s*-+\s*\|", line):
            continue
        cells = [part.strip() for part in line.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        figma_name, class_cell, _face, size_cell, weight_cell = cells[:5]
        selectors = re.findall(r"`([^`]+)`", class_cell)
        if not selectors:
            selectors = [part.strip() for part in class_cell.split(",") if part.strip()]
        token_match = re.search(r"(--text-[\w-]+)", size_cell)
        if not token_match:
            raise ValueError(f"text style {figma_name}: missing size token in doc row")
        row: dict[str, object] = {
            "name": figma_name.strip(),
            "selectors": selectors,
            "size_token": token_match.group(1),
        }
        row.update(parse_weight_column(weight_cell))
        rows.append(row)
    if not rows:
        raise ValueError("empty Figma text style table")
    return rows


def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _collect_css_rules(css: str, rules: dict[str, dict[str, str]]) -> None:
    css = css.strip()
    pos = 0
    while pos < len(css):
        while pos < len(css) and css[pos].isspace():
            pos += 1
        if pos >= len(css):
            break
        brace = css.find("{", pos)
        if brace < 0:
            break
        prelude = css[pos:brace].strip()
        depth = 1
        j = brace + 1
        while j < len(css) and depth:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
            j += 1
        body = css[brace + 1 : j - 1]
        if prelude.startswith("@"):
            _collect_css_rules(body, rules)
        else:
            decls = parse_css_properties(body)
            if decls:
                for sel in prelude.split(","):
                    sel = sel.strip()
                    if sel:
                        merged = dict(rules.get(sel, {}))
                        merged.update(decls)
                        rules[sel] = merged
        pos = j


def parse_stylesheet_selectors(styles_dir: Path) -> dict[str, dict[str, str]]:
    rules: dict[str, dict[str, str]] = {}
    for path in sorted(styles_dir.glob("*.css")):
        text = _strip_css_comments(path.read_text(encoding="utf-8"))
        _collect_css_rules(text, rules)
    return rules


def _rule_matches_doc_selector(doc_selector: str, rule_selector: str) -> bool:
    doc_sel = doc_selector.strip()
    rule_sel = rule_selector.strip()
    if doc_sel == rule_sel:
        return True
    if " " in doc_sel or ">" in doc_sel:
        if rule_sel == doc_sel:
            return True
        if rule_sel.endswith(doc_sel):
            prefix = rule_sel[: -len(doc_sel)]
            return not prefix or prefix[-1] in " >+~,"
        return rule_sel.startswith(f"{doc_sel} ") or rule_sel.startswith(f"{doc_sel}>")
    if rule_sel == doc_sel:
        return True
    if rule_sel.startswith(f"{doc_sel} ") or rule_sel.startswith(f"{doc_sel}>"):
        return True
    return rule_sel.endswith(f" {doc_sel}") and len(rule_sel) > len(doc_sel)


def collect_selector_decls(
    selector: str,
    rules: dict[str, dict[str, str]],
) -> dict[str, str]:
    resolved = SELECTOR_ALIASES.get(selector, selector)
    merged: dict[str, str] = {}
    for rule_sel, decls in sorted(rules.items(), key=lambda item: len(item[0])):
        parts = [part.strip() for part in rule_sel.split(",") if part.strip()]
        for part in parts:
            if "::" in part and part != resolved:
                continue
            if not _rule_matches_doc_selector(resolved, part):
                continue
            if part.startswith(f"{resolved} ") or part.startswith(f"{resolved}>"):
                continue
            merged.update(decls)
            break
    if resolved.endswith(".library-index-group-label"):
        merged = {**rules.get(".library-index-group-label", {}), **merged}
    if selector.endswith(" a"):
        parent = selector.rsplit(" ", 1)[0]
        parent_decls = collect_selector_decls(parent, rules)
        for key, value in parent_decls.items():
            merged.setdefault(key, value)
    return merged


def _style_letter_spacing_pct(style: dict) -> float | None:
    ls = style.get("letterSpacing") or {}
    if ls.get("unit") == "PERCENT" and "value" in ls:
        return float(ls["value"])
    return None


def _expected_bound_font_size(size_token: str) -> set[str]:
    base = size_token.removeprefix("--")
    return {
        f"font-size/{base}",
        f"font-size/{base}/max",
    }


def _figma_style_matches_doc_fixed(style: dict, row: dict[str, object]) -> list[str]:
    errors: list[str] = []
    name = str(row["name"])
    bound = (style.get("boundVariables") or {}).get("fontSize")
    size_token = str(row["size_token"])
    allowed = _expected_bound_font_size(size_token)
    if bound and bound not in allowed:
        errors.append(f"fontSize {bound!r} not in {sorted(allowed)!r}")
    if "font_weight" in row and style.get("fontWeight") != row["font_weight"]:
        errors.append(f"fontWeight {style.get('fontWeight')} != {row['font_weight']}")
    if "letter_spacing_pct" in row:
        actual = _style_letter_spacing_pct(style)
        expected = row["letter_spacing_pct"]
        if actual is None or abs(actual - float(expected)) > 0.01:
            errors.append(f"letterSpacing {actual} != {expected}")
    if "text_case" in row and style.get("textCase") != row["text_case"]:
        errors.append(f"textCase {style.get('textCase')} != {row['text_case']}")
    return [f"{name} vs doc table: {detail}" for detail in errors]


def _font_size_uses_token(font_size: str, size_token: str) -> bool:
    normalized = font_size.strip()
    if normalized == size_token:
        return True
    match = re.fullmatch(r"var\((--text-[\w-]+)\)", normalized)
    return match is not None and match.group(1) == size_token


def _parse_em(value: str) -> float | None:
    match = re.fullmatch(r"(-?[\d.]+)em", value.strip())
    if match:
        return float(match.group(1))
    return None


@dataclass(frozen=True)
class TextStyleCssMismatch:
    style: str
    selector: str
    property: str
    shipped: str
    figma: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.style, self.selector, self.property)


def _open_css_item(style_name: str, selector: str) -> dict[str, object]:
    return TEXT_STYLE_OPEN_CSS_ITEMS.get((style_name, selector), {})


def _open_skip_properties(style_name: str, selector: str) -> frozenset[str]:
    spec = _open_css_item(style_name, selector)
    raw = spec.get("skip_properties") or frozenset()
    return frozenset(str(item) for item in raw)


def _open_mapping_gap_property(style_name: str, selector: str) -> str | None:
    spec = TEXT_STYLE_OPEN_MAPPING_GAPS.get((style_name, selector))
    if not spec:
        return None
    gap = str(spec.get("gap_property") or "").strip()
    return gap or None


def _filter_mapping_gap_mismatches(
    style_name: str,
    selector: str,
    mismatches: list[TextStyleCssMismatch],
) -> list[TextStyleCssMismatch]:
    gap_property = _open_mapping_gap_property(style_name, selector)
    if not gap_property:
        return mismatches
    return [
        item
        for item in mismatches
        if not _mismatch_covers_skip(item, gap_property)
    ]


def _line_height_probe_for_selector(selector: str) -> dict[str, object]:
    if (
        "home-" in selector
        or "home-plate" in selector
        or selector == ".entrance .lede"
        or "site-nav" in selector
        or "header-actions" in selector
        or selector.startswith(".entrance")
    ):
        if selector == ".home-snap-proposition .lede":
            return {"page": "index.html", "width": 900}
        if selector == ".entrance .lede":
            return {"page": "index.html", "width": 800}
        return {"page": "index.html", "width": 1280}
    if "not-found" in selector:
        return {"page": "404.html", "width": 1280}
    if "note-dropcap" in selector or "note-body" in selector:
        return {"page": "notes/index.html", "width": 1280}
    if "credential" in selector or "issuer" in selector:
        return {"page": "credentials/index.html", "width": 1280}
    if "library-" in selector or "note-" in selector:
        return {"page": "notes/index.html", "width": 1280}
    return {"page": "systems/index.html", "width": 1280}


def validate_text_style_open_css_items(doc: str, snapshot: dict | None = None) -> list[str]:
    errors: list[str] = []
    style_names = {item["name"] for item in (snapshot or {}).get("textStyles", [])}
    for key, spec in TEXT_STYLE_OPEN_CSS_ITEMS.items():
        style_name, selector = key
        if snapshot is not None and style_name not in style_names:
            errors.append(
                f"TEXT_STYLE_OPEN_CSS_ITEMS{key!r}: stale Figma style {style_name!r} not in snapshot"
            )
        reason = str(spec.get("reason") or "").strip()
        if not reason:
            errors.append(f"TEXT_STYLE_OPEN_CSS_ITEMS{key!r}: missing reason")
            continue
        if reason not in doc:
            errors.append(
                f"TEXT_STYLE_OPEN_CSS_ITEMS{key!r}: reason not found in design-system.md"
            )
        if f"`{selector}`" not in doc:
            errors.append(
                f"TEXT_STYLE_OPEN_CSS_ITEMS{key!r}: selector {selector!r} missing from doc"
            )
        skip = spec.get("skip_properties") or frozenset()
        if "line-height" in skip or "line-height (ratio)" in skip:
            errors.append(
                f"TEXT_STYLE_OPEN_CSS_ITEMS{key!r}: must not skip line-height checks"
            )
    open_section = doc.split("**Open (not enforced by sync; Yingzhao decides):**", 1)
    open_text = open_section[1] if len(open_section) > 1 else ""
    for style_name, selector in TEXT_STYLE_OPEN_CSS_ITEMS:
        if f"`{selector}`" not in open_text:
            errors.append(
                f"TEXT_STYLE_OPEN_CSS_ITEMS{(style_name, selector)!r}: "
                f"missing from Known Figma gaps open list"
            )
    return errors


def validate_text_style_open_mapping_gaps(doc: str, snapshot: dict | None = None) -> list[str]:
    errors: list[str] = []
    style_names = {item["name"] for item in (snapshot or {}).get("textStyles", [])}
    open_section = doc.split("**Open (not enforced by sync; Yingzhao decides):**", 1)
    open_text = open_section[1] if len(open_section) > 1 else ""
    table = parse_text_style_table(doc)
    for key, spec in TEXT_STYLE_OPEN_MAPPING_GAPS.items():
        style_name, selector = key
        if snapshot is not None and style_name not in style_names:
            errors.append(
                f"TEXT_STYLE_OPEN_MAPPING_GAPS{key!r}: stale Figma style {style_name!r} not in snapshot"
            )
        reason = str(spec.get("reason") or "").strip()
        if not reason:
            errors.append(f"TEXT_STYLE_OPEN_MAPPING_GAPS{key!r}: missing reason")
            continue
        gap_property = str(spec.get("gap_property") or "").strip()
        if not gap_property:
            errors.append(f"TEXT_STYLE_OPEN_MAPPING_GAPS{key!r}: missing gap_property")
            continue
        if reason not in doc:
            errors.append(
                f"TEXT_STYLE_OPEN_MAPPING_GAPS{key!r}: reason not found in design-system.md"
            )
        if f"`{selector}`" not in doc:
            errors.append(
                f"TEXT_STYLE_OPEN_MAPPING_GAPS{key!r}: selector {selector!r} missing from doc"
            )
        if f"`{selector}`" not in open_text:
            errors.append(
                f"TEXT_STYLE_OPEN_MAPPING_GAPS{key!r}: missing from Known Figma gaps open list"
            )
        row = next((item for item in table if item["name"] == style_name), None)
        if row is None or selector not in row["selectors"]:
            errors.append(
                f"TEXT_STYLE_OPEN_MAPPING_GAPS{key!r}: selector missing from typography table row"
            )
    return errors


def _mismatch_covers_skip(mismatch: TextStyleCssMismatch, skip_token: str) -> bool:
    prop = mismatch.property
    if skip_token in ("line-height", "line-height (ratio)"):
        return prop == "line-height"
    if skip_token == "font-size":
        return prop in ("font-size", "font-size (px)", "font-size binding")
    if skip_token == "font-size (px)":
        return prop in ("font-size", "font-size (px)", "font-size binding")
    if skip_token == "font-size binding":
        return prop in ("font-size", "font-size (px)", "font-size binding")
    if skip_token == "letter-spacing":
        return prop in ("letter-spacing", "letter-spacing (doc)")
    return prop == skip_token


def validate_stale_open_css_skips(
    snapshot: dict,
    doc: str,
    styles_dir: Path,
    dark: dict[str, str],
    light: dict[str, str],
) -> list[str]:
    if not TEXT_STYLE_OPEN_CSS_ITEMS:
        return []
    doc_rows = parse_text_style_table(doc)
    by_name = {item["name"]: item for item in snapshot.get("textStyles", [])}
    css_rules = parse_stylesheet_selectors(styles_dir)
    selectors: list[str] = []
    for row in doc_rows:
        selectors.extend(str(sel) for sel in row["selectors"])
    for _style, selector in TEXT_STYLE_OPEN_CSS_ITEMS:
        selectors.append(selector)
    computed_lh = computed_line_height_ratios(
        sorted(s for s in set(selectors) if s not in DECL_LH_ONLY_SELECTORS),
        styles_dir,
    )
    errors: list[str] = []
    for (style_name, selector), spec in TEXT_STYLE_OPEN_CSS_ITEMS.items():
        skip_props = frozenset(str(item) for item in (spec.get("skip_properties") or frozenset()))
        if not skip_props:
            continue
        style = by_name.get(style_name)
        row = next((item for item in doc_rows if item["name"] == style_name), None)
        if style is None or row is None:
            continue
        decls = collect_selector_decls(selector, css_rules)
        if not decls:
            continue
        raw = collect_figma_export_css_mismatches(
            style,
            row,
            selector,
            decls,
            dark,
            light,
            css_rules,
            computed_lh,
            skip_props_override=frozenset(),
        )
        for skip_token in sorted(skip_props):
            if not any(_mismatch_covers_skip(item, skip_token) for item in raw):
                errors.append(
                    f"TEXT_STYLE_OPEN_CSS_ITEMS{(style_name, selector)!r}: "
                    f"stale skip for {skip_token!r} (shipped CSS already matches Figma)"
                )
    return errors


def validate_stale_open_mapping_gaps(
    snapshot: dict,
    doc: str,
    styles_dir: Path,
    dark: dict[str, str],
    light: dict[str, str],
) -> list[str]:
    if not TEXT_STYLE_OPEN_MAPPING_GAPS:
        return []
    doc_rows = parse_text_style_table(doc)
    by_name = {item["name"]: item for item in snapshot.get("textStyles", [])}
    css_rules = parse_stylesheet_selectors(styles_dir)
    selectors: list[str] = []
    for row in doc_rows:
        selectors.extend(str(sel) for sel in row["selectors"])
    for _style, selector in TEXT_STYLE_OPEN_MAPPING_GAPS:
        selectors.append(selector)
    computed_lh = computed_line_height_ratios(
        sorted(s for s in set(selectors) if s not in DECL_LH_ONLY_SELECTORS),
        styles_dir,
    )
    errors: list[str] = []
    for (style_name, selector), spec in TEXT_STYLE_OPEN_MAPPING_GAPS.items():
        gap_property = str(spec.get("gap_property") or "").strip()
        if not gap_property:
            continue
        style = by_name.get(style_name)
        row = next((item for item in doc_rows if item["name"] == style_name), None)
        if style is None or row is None:
            continue
        decls = collect_selector_decls(selector, css_rules)
        if not decls:
            continue
        raw = collect_figma_export_css_mismatches(
            style,
            row,
            selector,
            decls,
            dark,
            light,
            css_rules,
            computed_lh,
            skip_props_override=frozenset(),
        )
        if not any(_mismatch_covers_skip(item, gap_property) for item in raw):
            errors.append(
                f"TEXT_STYLE_OPEN_MAPPING_GAPS{(style_name, selector)!r}: "
                f"stale gap for {gap_property!r} (shipped CSS already matches Figma)"
            )
    return errors


def computed_line_height_ratios(
    selectors: list[str],
    styles_dir: Path | None = None,
    dist_dir: Path | None = None,
) -> dict[str, float | None]:
    if not selectors:
        return {}
    if not COMPUTE_LINE_HEIGHTS.is_file():
        raise RuntimeError(f"missing {COMPUTE_LINE_HEIGHTS}")
    dist = dist_dir or DIST
    if os.environ.get("GITHUB_ACTIONS") == "true" and not dist.is_dir():
        raise RuntimeError(
            f"dist/ is required for line-height probes in CI; run scripts/build.py first ({dist})"
        )
    probes = [
        {"selector": sel, **_line_height_probe_for_selector(sel)} for sel in selectors
    ]
    payload = json.dumps(
        {
            "distDir": str(dist.resolve()),
            "stylesDir": str((styles_dir or STYLES_DIR).resolve()),
            "probes": probes,
        }
    ).encode("utf-8")
    proc = subprocess.run(
        ["node", str(COMPUTE_LINE_HEIGHTS)],
        input=payload,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "compute_text_style_line_heights failed: "
            + proc.stderr.decode("utf-8", errors="replace")
        )
    return json.loads(proc.stdout.decode("utf-8"))


def _resolve_css_scalar(
    raw: str,
    dark: dict[str, str],
    light: dict[str, str],
    theme: str = "dark",
) -> str:
    trimmed = raw.strip()
    if trimmed.startswith("var("):
        token = trimmed[4:-1].strip()
        resolved = resolve_css_token(token, dark, light, theme)
        return resolved if resolved is not None else trimmed
    return trimmed


def _parse_line_height_ratio(
    raw: str,
    dark: dict[str, str],
    light: dict[str, str],
) -> float | None:
    value = _resolve_css_scalar(raw, dark, light)
    if value.endswith("%"):
        return float(value[:-1]) / 100.0
    try:
        return float(value)
    except ValueError:
        return None


def _figma_line_height_ratio(style: dict) -> float | None:
    lh = style.get("lineHeight") or {}
    unit = lh.get("unit")
    if unit == "PERCENT" and "value" in lh:
        return float(lh["value"]) / 100.0
    if unit == "PIXELS" and "value" in lh:
        font_size = style.get("fontSize")
        if isinstance(font_size, (int, float)) and font_size:
            return float(lh["value"]) / float(font_size)
    return None


def _format_line_height_ratio(ratio: float | None) -> str:
    if ratio is None:
        return "AUTO"
    return f"{round(ratio * 100)}%"


def _css_font_family_matches(figma_family: str, css_value: str) -> bool:
    token_hint, needle = FIGMA_FONT_FAMILIES.get(figma_family, ("", figma_family.lower()))
    normalized = css_value.lower().replace('"', "")
    if needle and needle in normalized:
        return True
    if token_hint and f"var({token_hint})" in css_value.replace(" ", ""):
        return True
    return False


def _css_text_transform_matches(figma_case: str, css_value: str) -> bool:
    if figma_case == "UPPER":
        return css_value.strip().lower() == "uppercase"
    if figma_case in ("ORIGINAL", "AS_TYPED"):
        return css_value.strip().lower() in ("", "none")
    return True


def _css_text_decoration_matches(figma_decoration: str, css_value: str) -> bool:
    if figma_decoration == "NONE":
        return css_value.strip().lower() in ("", "none")
    return figma_decoration.lower() in css_value.lower()


def _expected_css_font_style(figma_style_name: str) -> str:
    if "italic" in figma_style_name.lower():
        return "italic"
    return "normal"


def collect_figma_export_css_mismatches(
    style: dict,
    row: dict[str, object],
    selector: str,
    decls: dict[str, str],
    dark: dict[str, str],
    light: dict[str, str],
    rules: dict[str, dict[str, str]],
    computed_line_heights: dict[str, float | None],
    *,
    skip_props_override: frozenset[str] | None = None,
) -> list[TextStyleCssMismatch]:
    name = str(row["name"])
    skip_props = (
        skip_props_override
        if skip_props_override is not None
        else _open_skip_properties(name, selector)
    )
    mismatches: list[TextStyleCssMismatch] = []

    figma_family = str(style.get("fontFamily") or "")
    css_family = decls.get("font-family", "")
    if figma_family and css_family and not _css_font_family_matches(figma_family, css_family):
        mismatches.append(
            TextStyleCssMismatch(
                name,
                selector,
                "font-family",
                css_family,
                figma_family,
            )
        )

    figma_weight = style.get("fontWeight")
    if isinstance(figma_weight, int):
        css_weight = decls.get("font-weight", "").strip() or "400"
        if str(figma_weight) != css_weight:
            mismatches.append(
                TextStyleCssMismatch(
                    name,
                    selector,
                    "font-weight",
                    css_weight,
                    str(figma_weight),
                )
            )

    figma_style_name = str(style.get("fontStyle") or "")
    expected_font_style = _expected_css_font_style(figma_style_name)
    css_font_style = decls.get("font-style", "").strip().lower() or "normal"
    if css_font_style == "oblique":
        css_font_style = "italic"
    if css_font_style != expected_font_style:
        mismatches.append(
            TextStyleCssMismatch(
                name,
                selector,
                "font-style",
                css_font_style,
                expected_font_style,
            )
        )

    size_token = str(row["size_token"])
    css_font_size = decls.get("font-size", "")
    if not _font_size_uses_token(css_font_size, size_token):
        mismatches.append(
            TextStyleCssMismatch(
                name,
                selector,
                "font-size",
                css_font_size or "(missing)",
                size_token,
            )
        )
    else:
        bound = (style.get("boundVariables") or {}).get("fontSize")
        allowed = _expected_bound_font_size(size_token)
        if bound and bound not in allowed:
            mismatches.append(
                TextStyleCssMismatch(
                    name,
                    selector,
                    "font-size binding",
                    str(bound),
                    ", ".join(sorted(allowed)),
                )
            )
        figma_px = style.get("fontSize")
        if isinstance(figma_px, (int, float)):
            token_px_val = token_px(size_token, dark)
            if token_px_val is not None and abs(token_px_val - float(figma_px)) > FONT_SIZE_PX_TOLERANCE:
                mismatches.append(
                    TextStyleCssMismatch(
                        name,
                        selector,
                        "font-size (px)",
                        f"{token_px_val:.2f}px",
                        f"{float(figma_px):.2f}px",
                    )
                )

    figma_lh = _figma_line_height_ratio(style)
    if figma_lh is not None and "line-height" not in skip_props:
        decl_lh = _parse_line_height_ratio(decls.get("line-height", ""), dark, light)
        computed_lh = computed_line_heights.get(selector)
        if selector in COMPUTED_LH_ONLY_SELECTORS:
            css_lh = computed_lh
        elif selector in DECL_LH_ONLY_SELECTORS:
            css_lh = decl_lh
        elif decls.get("line-height", "").strip():
            css_lh = decl_lh if decl_lh is not None else computed_lh
        else:
            css_lh = computed_lh if computed_lh is not None else decl_lh
        if css_lh is None or abs(css_lh - figma_lh) > LINE_HEIGHT_TOLERANCE:
            shipped = str(css_lh) if css_lh is not None else "(missing)"
            mismatches.append(
                TextStyleCssMismatch(
                    name,
                    selector,
                    "line-height",
                    shipped,
                    _format_line_height_ratio(figma_lh),
                )
            )

    figma_ls = _style_letter_spacing_pct(style)
    if figma_ls is not None and abs(figma_ls) > 0.01:
        expected_em = figma_ls / 100.0
        css_ls = decls.get("letter-spacing", "")
        parsed = _parse_em(css_ls) if css_ls else None
        if parsed is None or abs(parsed - expected_em) > 0.0001:
            mismatches.append(
                TextStyleCssMismatch(
                    name,
                    selector,
                    "letter-spacing",
                    css_ls or "(missing)",
                    f"{figma_ls:g}%",
                )
            )

    figma_case = str(style.get("textCase") or "ORIGINAL")
    css_transform = decls.get("text-transform", "")
    if not _css_text_transform_matches(figma_case, css_transform):
        mismatches.append(
            TextStyleCssMismatch(
                name,
                selector,
                "text-transform",
                css_transform or "none",
                figma_case,
            )
        )

    figma_decoration = str(style.get("textDecoration") or "NONE")
    css_decoration = decls.get("text-decoration", "")
    if not _css_text_decoration_matches(figma_decoration, css_decoration):
        mismatches.append(
            TextStyleCssMismatch(
                name,
                selector,
                "text-decoration",
                css_decoration or "none",
                figma_decoration,
            )
        )

    if "font_weight" in row:
        expected_fw = int(row["font_weight"])
        css_fw = decls.get("font-weight", "").strip() or "400"
        if str(expected_fw) != css_fw:
            mismatches.append(
                TextStyleCssMismatch(
                    name,
                    selector,
                    "font-weight (doc)",
                    css_fw,
                    str(expected_fw),
                )
            )

    if "letter_spacing_pct" in row:
        expected_em = float(row["letter_spacing_pct"]) / 100.0
        if abs(expected_em) > 0.0001:
            css_ls = decls.get("letter-spacing", "")
            parsed = _parse_em(css_ls) if css_ls else None
            if parsed is None or abs(parsed - expected_em) > 0.0001:
                mismatches.append(
                    TextStyleCssMismatch(
                        name,
                        selector,
                        "letter-spacing (doc)",
                        css_ls or "(missing)",
                        f"{float(row['letter_spacing_pct']):g}%",
                    )
                )

    if row.get("text_case") == "UPPER":
        css_transform = decls.get("text-transform", "")
        if css_transform.lower() != "uppercase":
            mismatches.append(
                TextStyleCssMismatch(
                    name,
                    selector,
                    "text-transform (doc)",
                    css_transform or "none",
                    "uppercase",
                )
            )

    filtered: list[TextStyleCssMismatch] = []
    for item in mismatches:
        if item.property in skip_props:
            continue
        filtered.append(item)
    return filtered


def collect_text_style_css_mismatches(
    snapshot: dict,
    doc: str,
    styles_dir: Path,
    dark: dict[str, str],
    light: dict[str, str],
) -> list[TextStyleCssMismatch]:
    doc_rows = parse_text_style_table(doc)
    by_name = {item["name"]: item for item in snapshot.get("textStyles", [])}
    css_rules = parse_stylesheet_selectors(styles_dir)
    mismatches: list[TextStyleCssMismatch] = []
    selectors: list[str] = []
    for row in doc_rows:
        selectors.extend(str(sel) for sel in row["selectors"])
    for _style, selector in TEXT_STYLE_OPEN_CSS_ITEMS:
        selectors.append(selector)
    for _style, selector in TEXT_STYLE_OPEN_MAPPING_GAPS:
        selectors.append(selector)
    lh_selectors = sorted(
        s for s in set(selectors) if s not in DECL_LH_ONLY_SELECTORS
    )
    computed_lh = computed_line_height_ratios(lh_selectors, styles_dir)

    for row in doc_rows:
        name = str(row["name"])
        style = by_name.get(name)
        if style is None:
            continue
        for selector in row["selectors"]:
            decls = collect_selector_decls(selector, css_rules)
            if not decls:
                mismatches.append(
                    TextStyleCssMismatch(
                        name,
                        selector,
                        "selector",
                        "(missing)",
                        "present in src/styles",
                    )
                )
                continue
            mismatches.extend(
                _filter_mapping_gap_mismatches(
                    name,
                    selector,
                    collect_figma_export_css_mismatches(
                        style,
                        row,
                        selector,
                        decls,
                        dark,
                        light,
                        css_rules,
                        computed_lh,
                    ),
                )
            )

    for (style_name, selector), _spec in TEXT_STYLE_OPEN_CSS_ITEMS.items():
        style = by_name.get(style_name)
        row = next((item for item in doc_rows if item["name"] == style_name), None)
        if style is None or row is None:
            continue
        decls = collect_selector_decls(selector, css_rules)
        if not decls:
            mismatches.append(
                TextStyleCssMismatch(
                    style_name,
                    selector,
                    "selector",
                    "(missing)",
                    "present in src/styles",
                )
            )
            continue
        mismatches.extend(
            collect_figma_export_css_mismatches(
                style,
                row,
                selector,
                decls,
                dark,
                light,
                css_rules,
                computed_lh,
            )
        )
    return mismatches


def validate_text_styles(
    snapshot: dict,
    doc: str,
    styles_dir: Path,
    dark: dict[str, str],
    light: dict[str, str],
) -> list[str]:
    errors: list[str] = []
    doc_rows = parse_text_style_table(doc)
    by_name = {item["name"]: item for item in snapshot.get("textStyles", [])}

    for row in doc_rows:
        name = str(row["name"])
        style = by_name.get(name)
        if style is None:
            errors.append(f"text style {name} missing from snapshot")
            continue
        errors.extend(_figma_style_matches_doc_fixed(style, row))
    export_mismatches = collect_text_style_css_mismatches(
        snapshot, doc, styles_dir, dark, light
    )
    for item in export_mismatches:
        errors.append(
            f"text style CSS mismatch: {item.style} {item.selector} {item.property} "
            f"shipped={item.shipped!r} figma={item.figma!r}"
        )
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

    if isinstance(figma_value, str) and figma_value.startswith("#"):
        resolver = make_color_resolver(dark, light, theme, chrome)
        try:
            computed = computed_color_hex8(css_value, resolver)
        except ValueError:
            return False
        return colors_equivalent(figma_value, computed)

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
            token = css_token_for_variable(var)
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
    styles_dir: Path | None = None,
) -> list[str]:
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    dark, light = theme_maps(css)
    chrome = parse_declarations(CHROME.read_text(encoding="utf-8"))
    errors: list[str] = []
    sheet_dir = styles_dir or STYLES_DIR

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
    errors.extend(validate_text_styles(snapshot, doc, sheet_dir, dark, light))

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


def assert_library_index_label_not_group_caps(doc: str) -> None:
    """`.library-index-label` is doc-only (Known gaps), not Label/Xs Group Caps."""
    rows = parse_text_style_table(doc)
    group_row = next((row for row in rows if row["name"] == "Label/Xs Group Caps"), None)
    if group_row is None:
        raise SystemExit("missing Label/Xs Group Caps row in design-system.md")
    selectors = [str(item) for item in group_row["selectors"]]
    if ".library-index-label" in selectors:
        raise SystemExit(
            "Label/Xs Group Caps must not map to .library-index-label "
            "(use .library-index-group--depth-0; index header is a known gap)"
        )
    rules = parse_stylesheet_selectors(STYLES_DIR)
    decls = collect_selector_decls(".library-index-label", rules)
    weight = decls.get("font-weight", "400").strip()
    if weight not in ("400", "normal"):
        raise SystemExit(
            f".library-index-label font-weight {weight!r} looks like Group Caps (600)"
        )


def assert_fixture_fails() -> None:
    if not VIOLATION_FIXTURE.is_file():
        raise SystemExit(f"missing fixture {VIOLATION_FIXTURE}")
    css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    errors = sync_snapshot(VIOLATION_FIXTURE, css, doc)
    if not errors:
        raise SystemExit("design_system_snapshot_violation fixture should fail sync")
    joined = "\n".join(errors)
    if "color/bg-deep" not in joined or "#000000" not in joined:
        raise SystemExit(
            "fixture should fail on color/bg-deep drift (#000000); got: "
            + "; ".join(errors[:5])
        )


def main() -> None:
    css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.is_file() else {}
    errors: list[str] = []
    errors.extend(validate_text_style_open_css_items(doc, snapshot))
    errors.extend(validate_text_style_open_mapping_gaps(doc, snapshot))
    dark, light = theme_maps(css)
    errors.extend(validate_stale_open_css_skips(snapshot, doc, STYLES_DIR, dark, light))
    errors.extend(validate_stale_open_mapping_gaps(snapshot, doc, STYLES_DIR, dark, light))
    if re.search(r"TEXT_STYLE_FIELD_DRIFT\s*[:=]", Path(__file__).read_text(encoding="utf-8")):
        errors.append("TEXT_STYLE_FIELD_DRIFT allow-list must not return (removed)")

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
    assert_library_index_label_not_group_caps(doc)

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
