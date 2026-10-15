#!/usr/bin/env python3
"""Assert tokens.css and design-system.md match docs/figma/variables.json."""

from __future__ import annotations

import json
import re
import sys
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
# Intentional Figma vs CSS selector gaps: (figma style, selector) -> reason.
ALLOWED_FIGMA_CSS_MISMATCHES: dict[tuple[str, str], str] = {}

# Text styles skipped for CSS selector checks: figma style name -> reason.
TEXT_STYLE_FIGMA_CSS_GAPS: dict[str, str] = {}

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


def _parse_em(value: str) -> float | None:
    match = re.fullmatch(r"(-?[\d.]+)em", value.strip())
    if match:
        return float(match.group(1))
    return None


def _css_matches_row(
    selector: str,
    row: dict[str, object],
    rules: dict[str, dict[str, str]],
    used_mismatches: set[tuple[str, str]],
) -> list[str]:
    name = str(row["name"])
    gap_key = name
    if gap_key in TEXT_STYLE_FIGMA_CSS_GAPS:
        return []
    mismatch_key = (name, selector)
    if mismatch_key in ALLOWED_FIGMA_CSS_MISMATCHES:
        used_mismatches.add(mismatch_key)
        return []

    decls = collect_selector_decls(selector, rules)
    if not decls:
        return [f"{name} CSS: selector {selector!r} not found in src/styles"]

    errors: list[str] = []
    size_token = str(row["size_token"])
    font_size = decls.get("font-size", "")
    if size_token not in font_size:
        errors.append(
            f"{name} {selector}: font-size {font_size!r} missing token {size_token}"
        )

    if "font_weight" in row:
        fw = decls.get("font-weight", "")
        expected_fw = int(row["font_weight"])
        if not fw.strip():
            if expected_fw != 400:
                errors.append(
                    f"{name} {selector}: font-weight missing, expected {expected_fw}"
                )
        elif str(expected_fw) != fw.strip():
            errors.append(
                f"{name} {selector}: font-weight {fw!r} != {expected_fw}"
            )

    if "letter_spacing_pct" in row:
        expected_em = float(row["letter_spacing_pct"]) / 100.0
        ls = decls.get("letter-spacing", "")
        parsed = _parse_em(ls)
        if parsed is None:
            if abs(expected_em) > 0.0001:
                errors.append(
                    f"{name} {selector}: letter-spacing missing, expected {expected_em}em"
                )
        elif abs(parsed - expected_em) > 0.0001:
            errors.append(
                f"{name} {selector}: letter-spacing {ls!r} != {expected_em}em"
            )

    if row.get("text_case") == "UPPER":
        tt = decls.get("text-transform", "")
        if tt.lower() != "uppercase":
            errors.append(
                f"{name} {selector}: text-transform {tt!r} != uppercase"
            )

    return errors


def validate_text_styles(
    snapshot: dict,
    doc: str,
    styles_dir: Path,
) -> list[str]:
    errors: list[str] = []
    doc_rows = parse_text_style_table(doc)
    by_name = {item["name"]: item for item in snapshot.get("textStyles", [])}
    css_rules = parse_stylesheet_selectors(styles_dir)
    used_mismatches: set[tuple[str, str]] = set()
    used_gaps: set[str] = set()

    for row in doc_rows:
        name = str(row["name"])
        style = by_name.get(name)
        if style is None:
            errors.append(f"text style {name} missing from snapshot")
            continue
        errors.extend(_figma_style_matches_doc_fixed(style, row))
        if name in TEXT_STYLE_FIGMA_CSS_GAPS:
            used_gaps.add(name)
            continue
        for selector in row["selectors"]:
            errors.extend(
                _css_matches_row(selector, row, css_rules, used_mismatches)
            )

    unused_mismatch = set(ALLOWED_FIGMA_CSS_MISMATCHES.keys()) - used_mismatches
    if unused_mismatch:
        errors.append(
            "unused ALLOWED_FIGMA_CSS_MISMATCHES entries: "
            + ", ".join(f"{k[0]}/{k[1]}" for k in sorted(unused_mismatch))
        )
    unused_gaps = set(TEXT_STYLE_FIGMA_CSS_GAPS.keys()) - used_gaps
    if unused_gaps:
        errors.append(
            "unused TEXT_STYLE_FIGMA_CSS_GAPS entries: " + ", ".join(sorted(unused_gaps))
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
) -> list[str]:
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
    errors.extend(validate_text_styles(snapshot, doc, STYLES_DIR))

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
