#!/usr/bin/env python3
"""Unit test: a fixture with a palette rgb() literal must fail the drift check."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from check_token_drift import find_violations

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "scripts" / "fixtures" / "token_drift_violation.css"


def main() -> None:
    if not FIXTURE.is_file():
        print(f"missing fixture {FIXTURE}", file=sys.stderr)
        raise SystemExit(1)

    with tempfile.TemporaryDirectory() as tmp:
        styles = Path(tmp)
        tokens = styles / "tokens.css"
        tokens.write_text(":root { --accent: #c49a5a; }\n", encoding="utf-8")
        bad = styles / "bad.css"
        bad.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        allowed = styles / "overlay.css"
        allowed.write_text(
            ".overlay {\n"
            "  background: rgb(43 84 64 / 35%);\n"
            "  color: rgb(0 0 0 / 12%);\n"
            "}\n",
            encoding="utf-8",
        )
        violations = find_violations(styles, tokens)

    joined = "\n".join(violations)
    if "rgb(196 154 90 / 10%)" not in joined:
        print("token drift fixture was not rejected:", file=sys.stderr)
        print(joined or "(no violations)", file=sys.stderr)
        raise SystemExit(1)
    if "43 84 64" in joined or "0 0 0" in joined:
        print("allow-listed overlay was flagged:", file=sys.stderr)
        print(joined, file=sys.stderr)
        raise SystemExit(1)

    print("test_check_token_drift ok")


if __name__ == "__main__":
    main()
