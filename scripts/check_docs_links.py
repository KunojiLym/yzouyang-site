#!/usr/bin/env python3
"""Validate relative markdown links and optional doc freshness front-matter."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"\]\(([^)\s#][^)\s]*?)(#[^)]*)?\)")
SKIP_PREFIXES = ("http:", "https:", "mailto:")
SKIP_DIRS = ("graphify-out", ".venv", "node_modules", "dist", ".git")
FRONT_MATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL | re.MULTILINE
)


def repo_root(script: Path) -> Path:
    if script.parent.name == "docs" and script.parent.parent.name == "scripts":
        return script.parents[2]
    return script.parents[1]


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        files.append(path)
    return files


def parse_front_matter(text: str) -> dict[str, str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}
    block = match.group(1)
    values: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def check_links(root: Path) -> list[tuple[str, str]]:
    broken: list[tuple[str, str]] = []
    for md_file in iter_markdown_files(root):
        text = md_file.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            raw_target = match.group(1)
            if raw_target.startswith(SKIP_PREFIXES):
                continue
            target = unquote(raw_target.split("#", 1)[0])
            if not target:
                continue
            try:
                resolved = (md_file.parent / target).resolve()
            except OSError:
                rel_file = md_file.relative_to(root).as_posix()
                broken.append((rel_file, raw_target))
                continue
            if not resolved.exists():
                rel_file = md_file.relative_to(root).as_posix()
                broken.append((rel_file, raw_target))
    return broken


def check_stale(root: Path, today: date | None = None) -> list[tuple[str, str]]:
    today = today or date.today()
    stale: list[tuple[str, str]] = []
    for md_file in iter_markdown_files(root):
        text = md_file.read_text(encoding="utf-8")
        fm = parse_front_matter(text)
        if "last_verified" not in fm or "verify_cadence_days" not in fm:
            continue
        try:
            verified = datetime.strptime(fm["last_verified"], "%Y-%m-%d").date()
            cadence = int(fm["verify_cadence_days"])
        except ValueError:
            rel_file = md_file.relative_to(root).as_posix()
            stale.append((rel_file, "invalid last_verified or verify_cadence_days"))
            continue
        if verified + timedelta(days=cadence) < today:
            rel_file = md_file.relative_to(root).as_posix()
            stale.append(
                (
                    rel_file,
                    f"last_verified={fm['last_verified']} cadence={cadence}d",
                )
            )
    return stale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root (default: auto-detect from script location)",
    )
    parser.add_argument(
        "--stale",
        action="store_true",
        help="Report docs with expired last_verified front-matter",
    )
    args = parser.parse_args()
    script = Path(__file__).resolve()
    root = (args.root or repo_root(script)).resolve()

    broken = check_links(root)
    if broken:
        print(f"BROKEN LINKS: {len(broken)}", file=sys.stderr)
        for rel_file, target in broken:
            print(f"  {rel_file} -> {target}", file=sys.stderr)
    else:
        print("OK: all relative markdown links resolve")

    exit_code = 1 if broken else 0

    if args.stale:
        stale = check_stale(root)
        if stale:
            print(f"\nSTALE DOCS: {len(stale)}", file=sys.stderr)
            for rel_file, detail in stale:
                print(f"  {rel_file}: {detail}", file=sys.stderr)
            exit_code = 1
        else:
            print("OK: no stale docs with last_verified front-matter")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
