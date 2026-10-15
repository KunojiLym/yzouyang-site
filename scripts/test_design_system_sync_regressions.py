#!/usr/bin/env python3
"""Regression tests for design-system sync (seeded token mutations)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from test_design_system_sync import (  # noqa: E402
    DOC,
    SNAPSHOT,
    TOKENS,
    sync_snapshot,
)

REGRESSIONS: list[tuple[str, str, str]] = [
    (
        "accent-cta-bg dark mix 8% -> 18%",
        r"--accent-cta-bg: color-mix\(in srgb, var\(--accent\) 8%, transparent\)",
        "--accent-cta-bg: color-mix(in srgb, var(--accent) 18%, transparent)",
    ),
    (
        "light accent-cta-border 40% -> 90%",
        r"\[data-theme=\"light\"\][\s\S]*?var\(--accent\) 40%",
        "var(--accent) 90%",
    ),
    (
        "dark accent-cta-border mix partner line-strong -> bg-deep",
        r"--accent-cta-border: color-mix\(in srgb, var\(--accent\) 55%, var\(--line-strong\)\)",
        "--accent-cta-border: color-mix(in srgb, var(--accent) 55%, var(--bg-deep))",
    ),
    (
        "light glow mix 16% -> 14%",
        r"\[data-theme=\"light\"\][\s\S]*?--glow: color-mix\(in srgb, var\(--accent\) 16%, transparent\)",
        "--glow: color-mix(in srgb, var(--accent) 14%, transparent)",
    ),
]

NEEDLES: list[str] = [
    "--accent-cta-bg",
    "accent-cta-border",
    "accent-cta-border",
    "--glow",
]

LABEL_CAPS_ROW = (
    "| Label/Caps | `.record-id` | Source Sans 3 | `--text-xs` | 600, 8%, caps |"
)
LABEL_CAPS_MUTATION = (
    "| Label/Caps | `.record-id` | Source Sans 3 | `--text-xs` | 900, 30%, caps |"
)


def _apply_light_block_mutation(css: str, pattern: str, repl: str) -> str:
    if pattern.startswith("[data-theme"):
        light_start = css.find('[data-theme="light"]')
        if light_start < 0:
            raise ValueError("missing light theme block")
        head = css[:light_start]
        tail = css[light_start:]
        new_tail, count = re.subn(pattern, repl, tail, count=1)
        if count != 1:
            raise ValueError(f"pattern did not match once in light block: {pattern!r}")
        return head + new_tail
    new_css, count = re.subn(pattern, repl, css, count=1)
    if count != 1:
        raise ValueError(f"pattern did not match once: {pattern!r}")
    return new_css


def main() -> None:
    base_css = TOKENS.read_text(encoding="utf-8")
    doc = DOC.read_text(encoding="utf-8")
    baseline_errors = sync_snapshot(SNAPSHOT, base_css, doc)
    if baseline_errors:
        print("baseline sync_snapshot should pass before regressions:", file=sys.stderr)
        for item in baseline_errors[:20]:
            print(f"  {item}", file=sys.stderr)
        raise SystemExit(1)

    for (label, pattern, repl), needle in zip(REGRESSIONS, NEEDLES, strict=True):
        mutated = _apply_light_block_mutation(base_css, pattern, repl)
        if mutated == base_css:
            print(f"regression {label}: mutation had no effect", file=sys.stderr)
            raise SystemExit(1)
        errors = sync_snapshot(SNAPSHOT, mutated, doc)
        if not errors:
            print(f"regression {label}: expected sync failure", file=sys.stderr)
            raise SystemExit(1)
        if not any(needle in item for item in errors):
            print(
                f"regression {label}: errors missing {needle!r}:",
                file=sys.stderr,
            )
            for item in errors[:10]:
                print(f"  {item}", file=sys.stderr)
            raise SystemExit(1)

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
