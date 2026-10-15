#!/usr/bin/env python3
"""Regression tests for design-system sync (seeded token mutations)."""

from __future__ import annotations

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
    collect_text_style_css_mismatches,
    sync_snapshot,
    theme_maps,
)

REGRESSIONS: list[tuple[str, str, str, list[str]]] = [
    (
        "accent-cta-bg dark mix 8% -> 18%",
        r"--accent-cta-bg: color-mix\(in srgb, var\(--accent\) 8%, transparent\)",
        "--accent-cta-bg: color-mix(in srgb, var(--accent) 18%, transparent)",
        ["--accent-cta-bg", "8%", "18%"],
    ),
    (
        "light accent-cta-border 40% -> 90%",
        r'(\[data-theme="light"\][\s\S]*?color-mix\(in srgb, var\(--accent\) )40(%, var\(--accent-text\)\))',
        r"\g<1>90\g<2>",
        ["color/accent-cta-border", "90%", "--accent-cta-border"],
    ),
    (
        "dark accent-cta-border mix partner line-strong -> bg-deep",
        r"--accent-cta-border: color-mix\(in srgb, var\(--accent\) 55%, var\(--line-strong\)\)",
        "--accent-cta-border: color-mix(in srgb, var(--accent) 55%, var(--bg-deep))",
        ["color/accent-cta-border", "--accent-cta-border", "bg-deep"],
    ),
    (
        "light glow mix 16% -> 14%",
        r'(\[data-theme="light"\][\s\S]*?--glow: color-mix\(in srgb, var\(--accent\) )16(%, transparent\))',
        r"\g<1>14\g<2>",
        ["color/glow", "--glow", "14%, transparent"],
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

    gap_prefix = (
        "- **Text style CSS · Body/Large Dek · `.library-panel--note .note-dek` · line-height:**"
    )
    synthetic_gap = (
        gap_prefix
        + " shipped **9.99**; Figma **145%**. seeded test — "
        + "[issue #32](https://github.com/KunojiLym/yzouyang-site/issues/32).\n"
    )
    doc_with_fake_gap = doc.replace(
        "**Open (not enforced by sync; Yingzhao decides):**",
        synthetic_gap + "**Open (not enforced by sync; Yingzhao decides):**",
        1,
    )
    gap_errors = sync_snapshot(SNAPSHOT, base_css, doc_with_fake_gap)
    if not any("stale text style CSS gap" in item for item in gap_errors):
        print(
            "stale text style CSS gap bullet should fail when Body/Large Dek matches CSS",
            file=sys.stderr,
        )
        for item in gap_errors[:10]:
            print(f"  {item}", file=sys.stderr)
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
    if not any(
        "shipped text style assertion failed" in item
        and "Body/Large Dek" in item
        and "line-height" in item
        for item in lh_errors
    ):
        print(
            "Body/Large Dek line-height mutation should fail shipped assertion",
            file=sys.stderr,
        )
        for item in lh_errors[:10]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    with tempfile.TemporaryDirectory() as tmp_lede:
        styles_lede = Path(tmp_lede)
        for sheet in STYLES_DIR.glob("*.css"):
            shutil.copy(sheet, styles_lede / sheet.name)
        home_path = styles_lede / "home.css"
        home_path.write_text(
            home_path.read_text(encoding="utf-8").replace(
                ".entrance .lede {\n"
                "  max-width: 38rem;\n"
                "  color: var(--text-default);\n"
                "  margin: 0 0 var(--space-4);\n"
                "  font-size: var(--text-md);\n"
                "  line-height: 1.55;",
                ".entrance .lede {\n"
                "  max-width: 38rem;\n"
                "  color: var(--text-default);\n"
                "  margin: 0 0 var(--space-4);\n"
                "  font-size: var(--text-md);\n"
                "  line-height: 1.9;",
                1,
            ),
            encoding="utf-8",
        )
        lede_errors = sync_snapshot(SNAPSHOT, base_css, doc, styles_dir=styles_lede)
    if not any(
        "shipped text style assertion failed" in item
        and "Body/Large" in item
        and ".entrance .lede" in item
        for item in lede_errors
    ):
        print(
            "Body/Large lede line-height 1.9 should fail shipped assertion",
            file=sys.stderr,
        )
        for item in lede_errors[:10]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

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
        f"test_design_system_sync_regressions ok ({len(REGRESSIONS)} token cases + Label/Caps doc)"
    )


if __name__ == "__main__":
    main()
