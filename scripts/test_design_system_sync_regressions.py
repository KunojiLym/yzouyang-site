#!/usr/bin/env python3
"""Regression tests for design-system sync (seeded token mutations)."""

from __future__ import annotations

import copy
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from test_design_system_sync import (  # noqa: E402
    DOC,
    SNAPSHOT,
    STYLES_DIR,
    TOKENS,
    TEXT_STYLE_OPEN_CSS_ITEMS,
    collect_text_style_css_mismatches,
    sync_snapshot,
    theme_maps,
    validate_stale_open_css_skips,
    validate_stale_open_mapping_gaps,
    validate_text_style_open_css_items,
    validate_text_style_open_mapping_gaps,
)

MAPPING_GAP_PROBE_REASON = (
    "Probe: TEXT_STYLE_OPEN_MAPPING_GAPS allows only its documented gap_property mismatch."
)

LIGHT_DECL_MUTATIONS: list[tuple[str, str, str, list[str]]] = [
    (
        "light accent-cta-border 40% -> 90%",
        "--accent-cta-border: color-mix(in srgb, var(--accent) 40%, var(--accent-text))",
        "--accent-cta-border: color-mix(in srgb, var(--accent) 90%, var(--accent-text))",
        ["color/accent-cta-border", "90%", "--accent-cta-border"],
    ),
    (
        "light glow mix 16% -> 14%",
        "--glow: color-mix(in srgb, var(--accent) 16%, transparent)",
        "--glow: color-mix(in srgb, var(--accent) 14%, transparent)",
        ["color/glow", "--glow", "14%, transparent"],
    ),
]

REGRESSIONS: list[tuple[str, str, str, list[str]]] = [
    (
        "accent-cta-bg dark mix 8% -> 18%",
        r"--accent-cta-bg: color-mix\(in srgb, var\(--accent\) 8%, transparent\)",
        "--accent-cta-bg: color-mix(in srgb, var(--accent) 18%, transparent)",
        ["--accent-cta-bg", "8%", "18%"],
    ),
    (
        "dark accent-cta-border mix partner line-strong -> bg-deep",
        r"--accent-cta-border: color-mix\(in srgb, var\(--accent\) 55%, var\(--line-strong\)\)",
        "--accent-cta-border: color-mix(in srgb, var(--accent) 55%, var(--bg-deep))",
        ["color/accent-cta-border", "--accent-cta-border", "bg-deep"],
    ),
]


LABEL_CAPS_ROW = (
    "| Label/Caps | `.record-id` | Source Sans 3 | `--text-xs` | 600, 8%, caps |"
)
LABEL_CAPS_MUTATION = (
    "| Label/Caps | `.record-id` | Source Sans 3 | `--text-xs` | 900, 30%, caps |"
)


def _apply_mutation(css: str, pattern: str, repl: str) -> str:
    new_css, count = re.subn(pattern, repl, css, count=1)
    if count != 1:
        raise ValueError(f"pattern did not match once: {pattern!r}")
    return new_css


def _mutate_light_decl(css: str, needle: str, repl: str) -> str:
    marker = '[data-theme="light"]'
    start = css.find(marker)
    if start < 0:
        raise ValueError("missing light theme block")
    brace = css.find("{", start)
    end = css.find("}", brace)
    if brace < 0 or end < 0:
        raise ValueError("malformed light theme block")
    block = css[brace + 1 : end]
    if needle not in block:
        raise ValueError(f"needle not in light block: {needle!r}")
    new_block = block.replace(needle, repl, 1)
    return css[: brace + 1] + new_block + css[end:]


def _assert_expected_errors(label: str, errors: list[str], needles: list[str]) -> None:
    joined = "\n".join(errors)
    for needle in needles:
        if needle not in joined:
            print(
                f"regression {label}: expected error mentioning {needle!r}; got:",
                file=sys.stderr,
            )
            for item in errors[:12]:
                print(f"  {item}", file=sys.stderr)
            raise SystemExit(1)
    if len(errors) > 8:
        print(
            f"regression {label}: too many errors ({len(errors)}) — mutation likely too broad",
            file=sys.stderr,
        )
        for item in errors[:12]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)


def _assert_line_height_mismatch(
    errors: list[str],
    *,
    style: str,
    selector: str,
    label: str,
) -> None:
    if not any(
        "text style CSS mismatch" in item
        and style in item
        and selector in item
        and "line-height" in item
        for item in errors
    ):
        print(f"{label}: expected line-height export mismatch", file=sys.stderr)
        for item in errors[:10]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    base_css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    baseline_errors = sync_snapshot(SNAPSHOT, base_css, doc)
    if baseline_errors:
        print("baseline sync_snapshot should pass before regressions:", file=sys.stderr)
        for item in baseline_errors[:20]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    dark, light = theme_maps(base_css)
    export_mismatches = collect_text_style_css_mismatches(
        snapshot, doc, STYLES_DIR, dark, light
    )
    for item in export_mismatches:
        if item.style == "Body/Large Dek":
            print(
                f"Body/Large Dek should match .library-panel--note .note-dek: {item}",
                file=sys.stderr,
            )
            raise SystemExit(1)

    with tempfile.TemporaryDirectory() as tmp:
        styles_tmp = Path(tmp)
        for sheet in STYLES_DIR.glob("*.css"):
            shutil.copy(sheet, styles_tmp / sheet.name)
        library_path = styles_tmp / "library.css"
        library_text = library_path.read_text(encoding="utf-8")
        library_path.write_text(
            library_text.replace(
                ".library-panel--note .note-dek {\n"
                "  margin: 0 0 var(--space-4);\n"
                "  max-width: none;\n"
                "  font-family: var(--font-body);\n"
                "  font-size: var(--text-lg);\n"
                "  line-height: 1.45;",
                ".library-panel--note .note-dek {\n"
                "  margin: 0 0 var(--space-4);\n"
                "  max-width: none;\n"
                "  font-family: var(--font-body);\n"
                "  font-size: var(--text-lg);\n"
                "  line-height: 9.99;",
                1,
            ),
            encoding="utf-8",
        )
        lh_errors = sync_snapshot(SNAPSHOT, base_css, doc, styles_dir=styles_tmp)
    _assert_line_height_mismatch(
        lh_errors,
        style="Body/Large Dek",
        selector=".library-panel--note .note-dek",
        label="Body/Large Dek",
    )

    snapshot_mut = copy.deepcopy(snapshot)
    for style in snapshot_mut["textStyles"]:
        if style["name"] == "Label/Caps":
            style["lineHeight"] = {"unit": "PERCENT", "value": 300}
        if style["name"] == "Body/Small":
            style["lineHeight"] = {"unit": "PERCENT", "value": 300}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(snapshot_mut, handle)
        mut_path = Path(handle.name)
    try:
        snap_errors = sync_snapshot(mut_path, base_css, doc)
    finally:
        mut_path.unlink(missing_ok=True)
    _assert_line_height_mismatch(
        snap_errors,
        style="Label/Caps",
        selector=".record-id",
        label="Label/Caps snapshot lh 300%",
    )
    _assert_line_height_mismatch(
        snap_errors,
        style="Body/Small",
        selector=".site-nav a",
        label="Body/Small snapshot lh 300%",
    )

    for label, pattern, repl, needles in REGRESSIONS:
        mutated = _apply_mutation(base_css, pattern, repl)
        if mutated == base_css:
            print(f"regression {label}: mutation had no effect", file=sys.stderr)
            raise SystemExit(1)
        errors = sync_snapshot(SNAPSHOT, mutated, doc)
        if not errors:
            print(f"regression {label}: expected sync failure", file=sys.stderr)
            raise SystemExit(1)
        _assert_expected_errors(label, errors, needles)

    for label, needle, repl, needles in LIGHT_DECL_MUTATIONS:
        mutated = _mutate_light_decl(base_css, needle, repl)
        if mutated == base_css:
            print(f"regression {label}: mutation had no effect", file=sys.stderr)
            raise SystemExit(1)
        if '[data-theme="light"]' not in mutated:
            print(f"regression {label}: light theme block was removed", file=sys.stderr)
            raise SystemExit(1)
        errors = sync_snapshot(SNAPSHOT, mutated, doc)
        if not errors:
            print(f"regression {label}: expected sync failure", file=sys.stderr)
            raise SystemExit(1)
        _assert_expected_errors(label, errors, needles)

    bogus = dict(TEXT_STYLE_OPEN_CSS_ITEMS)
    bogus[("Nope/X", ".nope")] = {"reason": "stale probe", "skip_properties": frozenset()}
    import test_design_system_sync as sync_mod

    original = sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS
    sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = bogus
    try:
        stale_errors = validate_text_style_open_css_items(doc)
    finally:
        sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = original
    if not any("Nope/X" in item or "stale probe" in item for item in stale_errors):
        print("bogus TEXT_STYLE_OPEN_CSS_ITEMS should fail validation", file=sys.stderr)
        raise SystemExit(1)

    lh_skip = dict(TEXT_STYLE_OPEN_CSS_ITEMS)
    lh_skip[("Body/Large", ".entrance .lede")] = {
        "reason": "regression probe for forbidden line-height skip",
        "skip_properties": frozenset({"line-height", "line-height (ratio)"}),
    }
    original_open = sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS
    sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = lh_skip
    try:
        lh_errors = validate_text_style_open_css_items(doc, snapshot)
    finally:
        sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = original_open
    if not any("must not skip line-height" in item for item in lh_errors):
        print("Body/Large line-height skip should fail open-item validation", file=sys.stderr)
        raise SystemExit(1)

    lh_skip_h2 = dict(TEXT_STYLE_OPEN_CSS_ITEMS)
    lh_skip_h2[("Display/H2", ".home-plate h2")] = {
        "reason": "regression probe for forbidden Display/H2 line-height skip",
        "skip_properties": frozenset({"line-height", "line-height (ratio)"}),
    }
    sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = lh_skip_h2
    try:
        lh_h2_errors = validate_text_style_open_css_items(doc, snapshot)
    finally:
        sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = original_open
    if not any("must not skip line-height" in item for item in lh_h2_errors):
        print("Display/H2 line-height skip should fail open-item validation", file=sys.stderr)
        raise SystemExit(1)

    stale_font = dict(TEXT_STYLE_OPEN_CSS_ITEMS)
    stale_font[("Display/H2", "main.page h2")] = {
        "reason": "Display/H2 Page size/tracking with Display/H2 line height",
        "skip_properties": frozenset({"font-family"}),
    }
    sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = stale_font
    try:
        stale_font_errors = validate_stale_open_css_skips(
            snapshot, doc, STYLES_DIR, *theme_maps(base_css)
        )
    finally:
        sync_mod.TEXT_STYLE_OPEN_CSS_ITEMS = original_open
    if not any("stale skip" in item and "font-family" in item for item in stale_font_errors):
        print("matching font-family skip on main.page h2 should fail as stale", file=sys.stderr)
        for item in stale_font_errors[:8]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    snapshot_h2 = copy.deepcopy(snapshot)
    for style in snapshot_h2["textStyles"]:
        if style["name"] == "Display/H2":
            style["lineHeight"] = {"unit": "PERCENT", "value": 300}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(snapshot_h2, handle)
        h2_path = Path(handle.name)
    try:
        h2_errors = sync_snapshot(h2_path, base_css, doc)
    finally:
        h2_path.unlink(missing_ok=True)
    _assert_line_height_mismatch(
        h2_errors,
        style="Display/H2",
        selector="main.page h2",
        label="Display/H2 300% flags main.page h2",
    )

    with tempfile.TemporaryDirectory() as tmp_nav:
        styles_nav = Path(tmp_nav)
        for sheet in STYLES_DIR.glob("*.css"):
            shutil.copy(sheet, styles_nav / sheet.name)
        chrome_path = styles_nav / "chrome.css"
        chrome_path.write_text(
            chrome_path.read_text(encoding="utf-8")
            + "\n.header-actions .site-nav a { line-height: 3; }\n",
            encoding="utf-8",
        )
        nav_errors = sync_snapshot(SNAPSHOT, base_css, doc, styles_dir=styles_nav)
    _assert_line_height_mismatch(
        nav_errors,
        style="Body/Small",
        selector=".site-nav a",
        label="header-actions .site-nav a line-height 3",
    )

    doc_for_gap = doc.replace(
        "**Open (not enforced by sync; Yingzhao decides):**",
        "**Open (not enforced by sync; Yingzhao decides):**\n\n- "
        + MAPPING_GAP_PROBE_REASON
        + " (`Display/H2` · `.home-plate h2`, gap_property `line-height`).\n",
        1,
    )
    gap_spec = {
        ("Display/H2", ".home-plate h2"): {
            "reason": MAPPING_GAP_PROBE_REASON,
            "gap_property": "line-height",
        },
    }
    original_gaps = sync_mod.TEXT_STYLE_OPEN_MAPPING_GAPS
    sync_mod.TEXT_STYLE_OPEN_MAPPING_GAPS = gap_spec
    try:
        gap_doc_errors = validate_text_style_open_mapping_gaps(doc_for_gap, snapshot)
        if gap_doc_errors:
            print("mapping gap probe doc validation should pass", file=sys.stderr)
            for item in gap_doc_errors[:8]:
                print(f"  {item}", file=sys.stderr)
            raise SystemExit(1)
        stale_gap_errors = validate_stale_open_mapping_gaps(
            snapshot, doc_for_gap, STYLES_DIR, dark, light
        )
        if not any("stale gap" in item and "line-height" in item for item in stale_gap_errors):
            print(
                "aligned .home-plate h2 line-height should be a stale mapping gap",
                file=sys.stderr,
            )
            for item in stale_gap_errors[:8]:
                print(f"  {item}", file=sys.stderr)
            raise SystemExit(1)

        with tempfile.TemporaryDirectory() as tmp_plate:
            styles_plate = Path(tmp_plate)
            for sheet in STYLES_DIR.glob("*.css"):
                shutil.copy(sheet, styles_plate / sheet.name)
            home_path = styles_plate / "home.css"
            home_text = home_path.read_text(encoding="utf-8")
            home_path.write_text(
                home_text.replace(
                    ".home-plate h2 {\n"
                    "  margin: 0 0 var(--space-5);\n"
                    "  font-family: var(--font-display);",
                    ".home-plate h2 {\n"
                    "  margin: 0 0 var(--space-5);\n"
                    "  font-family: Times, serif;",
                    1,
                ),
                encoding="utf-8",
            )
            drift_errors = collect_text_style_css_mismatches(
                snapshot, doc_for_gap, styles_plate, dark, light
            )
        if not any(
            item.style == "Display/H2"
            and item.selector == ".home-plate h2"
            and item.property == "font-family"
            for item in drift_errors
        ):
            print(
                "non-gap property drift on gapped selector should still fail sync",
                file=sys.stderr,
            )
            for item in drift_errors[:12]:
                print(f"  {item}", file=sys.stderr)
            raise SystemExit(1)
    finally:
        sync_mod.TEXT_STYLE_OPEN_MAPPING_GAPS = original_gaps

    doc = DOC.read_text(encoding="utf-8")
    if LABEL_CAPS_ROW not in doc:
        print("missing Label/Caps row in design-system.md", file=sys.stderr)
        raise SystemExit(1)
    mutated_doc = doc.replace(LABEL_CAPS_ROW, LABEL_CAPS_MUTATION)
    doc_errors = sync_snapshot(SNAPSHOT, base_css, mutated_doc)
    if not doc_errors or not any("Label/Caps" in item for item in doc_errors):
        print("Label/Caps doc mutation should fail text-style validation", file=sys.stderr)
        for item in doc_errors[:10]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    print(
        "test_design_system_sync_regressions ok "
        f"({len(REGRESSIONS)} token cases + Label/Caps doc + mapping gaps)"
    )


if __name__ == "__main__":
    main()
