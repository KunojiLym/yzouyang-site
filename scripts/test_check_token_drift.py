#!/usr/bin/env python3
"""Unit tests for check_token_drift fixtures."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from check_token_drift import find_violations

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "scripts" / "fixtures"


def _assert_rejected(violations: list[str], needle: str, label: str) -> None:
    joined = "\n".join(violations)
    if needle not in joined:
        print(f"{label} was not rejected (need {needle!r}):", file=sys.stderr)
        print(joined or "(no violations)", file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    palette = FIXTURES / "token_drift_violation.css"
    if not palette.is_file():
        print(f"missing fixture {palette}", file=sys.stderr)
        raise SystemExit(1)

    with tempfile.TemporaryDirectory() as tmp:
        styles = Path(tmp)
        tokens = styles / "tokens.css"
        tokens.write_text(":root { --accent: #c49a5a; }\n", encoding="utf-8")
        allowed = styles / "overlay.css"
        allowed.write_text(
            ".overlay {\n"
            "  background: rgb(43 84 64 / 35%);\n"
            "  color: rgb(0 0 0 / 12%);\n"
            "}\n",
            encoding="utf-8",
        )
        bad = styles / "bad.css"
        bad.write_text(palette.read_text(encoding="utf-8"), encoding="utf-8")
        violations = find_violations(styles, tokens)
        _assert_rejected(violations, "rgb(196 154 90 / 10%)", "palette rgb")
        joined = "\n".join(violations)
        if "43 84 64" in joined or "0 0 0" in joined:
            print("allow-listed overlay was flagged:", file=sys.stderr)
            print(joined, file=sys.stderr)
            raise SystemExit(1)

    cases: list[tuple[str, str]] = [
        ("token_drift_hsl.css", "hsl("),
        ("token_drift_oklch.css", "oklch("),
        ("token_drift_named.css", "named color 'red'"),
        ("token_drift_universal_comment.css", "rgb(196 154 90 / 12%)"),
        ("token_drift_bg_deep_rgb.css", "rgb(10 11 10 / 90%)"),
    ]
    for fixture_name, needle in cases:
        with tempfile.TemporaryDirectory() as tmp:
            styles = Path(tmp)
            tokens = styles / "tokens.css"
            tokens.write_text(":root { --bg-deep: #0a0b0a; --accent: #c49a5a; }\n")
            bad = styles / "bad.css"
            bad.write_text((FIXTURES / fixture_name).read_text(encoding="utf-8"))
            _assert_rejected(find_violations(styles, tokens), needle, fixture_name)

    print("test_check_token_drift ok")


if __name__ == "__main__":
    main()
