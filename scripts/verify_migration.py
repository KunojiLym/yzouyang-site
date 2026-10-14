#!/usr/bin/env python3
"""C2a/C2c migration smoke checks — run after build, before DNS cutover or WP decommission.

Usage:
  python scripts/build.py
  python scripts/verify_migration.py
  python scripts/verify_migration.py --dist dist --expect-stubs 18
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DEFAULT_DIST = ROOT / "dist"

WP_SLUG_RE = re.compile(r"https?://(?:www\.)?yzouyang\.com/([^/?#]+)/?")


def fail(msg: str) -> None:
    print(f"verify_migration: FAIL — {msg}", file=sys.stderr)
    raise SystemExit(1)


def ok(msg: str) -> None:
    print(f"verify_migration: ok — {msg}")


def load_export() -> dict:
    path = DATA / "export_public.json"
    if not path.is_file():
        fail(f"missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def check_export_writing(export: dict) -> list[dict]:
    writing = export.get("writing") or []
    if len(writing) < 18:
        fail(f"export.writing has {len(writing)} essays — expected 18 PUBLIC notes")
    ok(f"export.writing count={len(writing)}")
    for row in writing:
        if not isinstance(row, dict):
            fail("export.writing row is not an object")
        note_id = str(row.get("id") or "")
        if not note_id.startswith("NOTE-"):
            fail(f"export.writing row missing NOTE-* id: {row!r}")
        body = str(row.get("body_md") or "")
        if "wp-content/uploads" in body:
            fail(f"{note_id} body_md still hotlinks wp-content/uploads")
        synd = row.get("syndication") if isinstance(row.get("syndication"), dict) else {}
        if not (synd.get("medium") or synd.get("linkedin")):
            fail(f"{note_id} missing syndication.medium/linkedin")
    ok("no wp-content hotlinks in export bodies")
    return writing


def wp_slug_from_url(url: str) -> str | None:
    match = WP_SLUG_RE.match(url.strip())
    if not match:
        return None
    slug = match.group(1).strip("/")
    if slug in {"blog", "wp-json", "feed", "category", "author", "notes", "systems", "credentials"}:
        return None
    return slug


def check_wp_stubs(dist: Path, writing: list[dict], expect_stubs: int) -> None:
    stubs: dict[str, str] = {}
    for row in writing:
        note_id = str(row.get("id") or "")
        synd = row.get("syndication") if isinstance(row.get("syndication"), dict) else {}
        wp = str(synd.get("wordpress") or "")
        slug = wp_slug_from_url(wp)
        if slug:
            stubs[slug] = note_id
    if len(stubs) < expect_stubs:
        fail(f"only {len(stubs)} wordpress slugs in export — expected >= {expect_stubs}")
    missing = []
    bad_target = []
    for slug, note_id in sorted(stubs.items()):
        stub = dist / slug / "index.html"
        if not stub.is_file():
            missing.append(slug)
            continue
        html = stub.read_text(encoding="utf-8")
        target = f"/notes/#{note_id}"
        if target not in html and f"#{note_id}" not in html:
            bad_target.append(slug)
    if missing:
        fail(f"missing dist stubs for slugs: {', '.join(missing[:5])}" + (" …" if len(missing) > 5 else ""))
    if bad_target:
        fail(f"stub HTML missing notes hash for: {', '.join(bad_target[:5])}")
    ok(f"WP slug stubs present for {len(stubs)} permalinks")

    blog_stub = dist / "blog" / "index.html"
    if not blog_stub.is_file():
        fail("dist/blog/index.html missing")
    blog_html = blog_stub.read_text(encoding="utf-8")
    if "/notes/" not in blog_html:
        fail("blog stub must redirect to /notes/")
    ok("blog stub redirects to /notes/")


def check_vendored_assets(writing: list[dict]) -> None:
    assets_root = ROOT / "assets" / "notes"
    if not assets_root.is_dir():
        fail("assets/notes/ missing — run export_public.py --vendor-assets")
    with_images = 0
    for row in writing:
        note_id = str(row.get("id") or "")
        body = str(row.get("body_md") or "")
        if f"assets/{note_id}/" in body or f"/assets/notes/{note_id}/" in body:
            with_images += 1
            note_dir = assets_root / note_id
            if not note_dir.is_dir() or not any(note_dir.iterdir()):
                fail(f"assets/notes/{note_id}/ missing but body references local images")
    ok(f"vendored assets present ({with_images} notes reference local images)")


def check_site_json() -> None:
    site = json.loads((DATA / "site.json").read_text(encoding="utf-8"))
    blog = next(
        (item for item in site.get("nav") or [] if isinstance(item, dict) and item.get("label") == "Blog"),
        None,
    )
    if not blog:
        fail("site.json nav missing Blog footer entry")
    if blog.get("href") != "/notes/" or blog.get("external"):
        fail("footer Blog must be internal /notes/")
    ok("footer Blog -> /notes/")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=DEFAULT_DIST)
    parser.add_argument("--expect-stubs", type=int, default=18)
    args = parser.parse_args()
    if not args.dist.is_dir():
        fail(f"dist missing: {args.dist} — run scripts/build.py first")

    export = load_export()
    writing = check_export_writing(export)
    check_vendored_assets(writing)
    check_wp_stubs(args.dist, writing, args.expect_stubs)
    check_site_json()
    print("verify_migration: all checks passed")


if __name__ == "__main__":
    main()
