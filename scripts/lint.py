#!/usr/bin/env python3
"""Lightweight lint for Phase 1 static site inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml  # PyYAML — declared in pyproject.toml; run `uv sync` first.

# Reuse build.py's constants rather than duplicating the layout/kind lists —
# scripts/ is on sys.path[0] when this file is run directly, so this is a
# plain sibling import, not a package import.
from build import CJ_LAYOUTS, CJ_SLIDE_KINDS, CJ_SLIDES_DIR

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REQUIRED_PAGES = ("/", "/about/", "/portfolio/", "/credentials/")
NON_PUBLIC_VISIBILITY = {
    "PRIVATE_ONLY",
    "NEVER_EXPORT",
    "INTERVIEW_PREP_ONLY",
    "LIMITED",
    "INTERVIEW_ONLY",
    "NEVER",
    "PRIVATE",
}


def fail(msg: str) -> None:
    print(f"lint error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def validate_public_visibility(value, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"visibility", "visibility_policy"}:
                normalized = str(child).strip().upper()
                if normalized != "PUBLIC":
                    fail(f"non-PUBLIC visibility in export: {child_path}={child!r}")
            validate_public_visibility(child, child_path)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            validate_public_visibility(child, f"{path}[{i}]")
    elif isinstance(value, str) and value.strip().upper() in NON_PUBLIC_VISIBILITY:
        fail(f"non-public marker leaked into export: {path}={value!r}")


def main() -> None:
    export_path = DATA / "export_public.json"
    site_path = DATA / "site.json"
    if not export_path.is_file():
        fail(f"missing {export_path}")
    if not site_path.is_file():
        fail(f"missing {site_path}")

    export = json.loads(export_path.read_text(encoding="utf-8"))
    site = json.loads(site_path.read_text(encoding="utf-8"))
    validate_public_visibility(export)

    meta = export.get("_meta") or {}
    if meta:
        if meta.get("schema_version") != 1:
            fail("export._meta.schema_version must be 1")
        if meta.get("visibility") != "PUBLIC":
            fail("export._meta.visibility must be PUBLIC")
        if not meta.get("person_id"):
            fail("export._meta.person_id required")

    for key in ("projects", "certifications"):
        if key not in export or not isinstance(export[key], list):
            fail(f"export missing list: {key}")

    for row in export.get("projects", []) + export.get("certifications", []):
        if isinstance(row, dict):
            vis = row.get("visibility_policy")
            if vis and vis != "PUBLIC":
                fail(f"non-PUBLIC record in export: {row.get('id') or row.get('name')} ({vis})")

    contact = site.get("contact") or {}
    for field in ("email", "phone"):
        if not contact.get(field):
            fail(f"site.contact.{field} required")

    forbidden = ("prudential.com", "u.nus.edu", "gatech.edu")
    blob = json.dumps(site).lower()
    for needle in forbidden:
        if needle in blob:
            fail(f"site.json must not contain work/university contact domain: {needle}")

    nav = site.get("nav") or []
    hrefs = {item.get("href") for item in nav}
    for path in REQUIRED_PAGES:
        if path not in hrefs:
            fail(f"nav missing {path}")

    for item in nav:
        if item.get("label") == "Contact" or item.get("href") in ("/contact/", "/contact"):
            fail("Contact must not be a primary nav item (use Home #contact)")

    external_labels = {"Blog", "Medium", "LinkedIn"}
    for item in nav:
        if item.get("label") in external_labels and not item.get("external"):
            fail(f"{item.get('label')} nav entry must be external until C2b")

    highlights = site.get("writing_highlights")
    if highlights is not None:
        if not isinstance(highlights, list) or not highlights:
            fail("site.writing_highlights must be a non-empty list when set")
        for row in highlights:
            if not isinstance(row, dict):
                fail("writing_highlights entries must be objects")
            if not (row.get("title") and row.get("url")):
                fail("writing_highlights entries need title and url")

    outcomes = site.get("outcomes")
    if outcomes is not None:
        if not isinstance(outcomes, list):
            fail("site.outcomes must be a list when set")
        if len(outcomes) > 3:
            fail("site.outcomes must have at most 3 entries")
        for row in outcomes:
            if not isinstance(row, dict):
                fail("outcomes entries must be objects")
            if not (str(row.get("metric") or "").strip() and str(row.get("label") or "").strip()):
                fail("outcomes entries need metric and label")

    platforms = (site.get("person") or {}).get("platforms")
    if platforms is not None:
        if not isinstance(platforms, list):
            fail("site.person.platforms must be a list when set")
        if len(platforms) > 4:
            fail("site.person.platforms should have at most 4 entries for Home proof strip")

    analytics = site.get("analytics") or {}
    ga_id = (analytics.get("ga_measurement_id") or "").strip()
    if ga_id and not ga_id.startswith("G-"):
        fail("analytics.ga_measurement_id must be a GA4 id (G-…)")

    jetpack = analytics.get("jetpack") or {}
    if jetpack.get("enabled"):
        if not str(jetpack.get("blog_id") or "").strip():
            fail("analytics.jetpack.blog_id required when jetpack.enabled")
        pages = jetpack.get("pages") or {}
        for label in ("Home", "About", "Portfolio", "Credentials", "Contact"):
            if label not in pages:
                fail(f"analytics.jetpack.pages missing {label}")

    diy = analytics.get("diy") or {}
    if diy.get("enabled"):
        track = ROOT / "src" / "track.js"
        if not track.is_file():
            fail("analytics.diy.enabled but src/track.js missing")
        collect = diy.get("collect_url")
        if collect is not None and not isinstance(collect, str):
            fail("analytics.diy.collect_url must be a string")
        if isinstance(collect, str) and collect.strip():
            if not collect.startswith(("https://", "http://")):
                fail("analytics.diy.collect_url must be http(s)")

    cj_path = DATA / "career-journey.yaml"
    if cj_path.is_file():
        cj = yaml.safe_load(cj_path.read_text(encoding="utf-8")) or {}
        slides = cj.get("slides") or []
        if not isinstance(slides, list) or not slides:
            fail("career-journey.yaml: slides must be a non-empty list")
        seen_ids: set[str] = set()
        for slide in slides:
            if not isinstance(slide, dict):
                fail("career-journey.yaml: each slide must be an object")
            sid = str(slide.get("id") or "").strip()
            if not sid:
                fail("career-journey.yaml: every slide needs a non-empty id")
            if sid in seen_ids:
                fail(f"career-journey.yaml: duplicate slide id {sid!r}")
            seen_ids.add(sid)

            kind = slide.get("kind")
            if kind not in CJ_SLIDE_KINDS:
                fail(
                    f"career-journey.yaml: slide {sid!r} has unknown kind "
                    f"{kind!r} (known: {', '.join(CJ_SLIDE_KINDS)})"
                )

            if kind == "image" and not str(slide.get("image_alt") or "").strip():
                fail(f"career-journey.yaml: slide {sid!r} (image) is missing image_alt")

            if kind == "points":
                points = slide.get("points") or []
                if not isinstance(points, list) or not points:
                    fail(f"career-journey.yaml: slide {sid!r} points must be a non-empty list")

            if kind == "timeline":
                items = slide.get("items") or []
                if not isinstance(items, list) or not items:
                    fail(f"career-journey.yaml: slide {sid!r} items must be a non-empty list")
                for item in items:
                    if not isinstance(item, dict):
                        fail(f"career-journey.yaml: slide {sid!r} timeline items must be objects")
                    if not str(item.get("year") or "").strip():
                        fail(f"career-journey.yaml: slide {sid!r} timeline item missing year")
                    if not str(item.get("label") or "").strip():
                        fail(f"career-journey.yaml: slide {sid!r} timeline item missing label")

            if kind == "composed":
                layout_name = slide.get("layout")
                regions = CJ_LAYOUTS.get(str(layout_name))
                if regions is None:
                    fail(
                        f"career-journey.yaml: slide {sid!r} has unknown composed "
                        f"layout {layout_name!r} (known: {', '.join(CJ_LAYOUTS)})"
                    )
                for block in slide.get("blocks") or []:
                    if not isinstance(block, dict):
                        fail(f"career-journey.yaml: slide {sid!r} has a non-object block")
                    region = str(block.get("region") or "")
                    if regions is not None and region not in regions:
                        fail(
                            f"career-journey.yaml: slide {sid!r} block region {region!r} "
                            f"not valid for layout {layout_name!r} (valid: {', '.join(regions)})"
                        )
                    if block.get("type") == "image" and not str(
                        block.get("image_alt") or ""
                    ).strip():
                        fail(
                            f"career-journey.yaml: slide {sid!r} has an image block "
                            "missing image_alt"
                        )

            if kind == "partial":
                rel = str(slide.get("partial") or "")
                if not rel or not (CJ_SLIDES_DIR / rel).is_file():
                    fail(
                        f"career-journey.yaml: slide {sid!r} partial file not found: "
                        f"data/career-journey-slides/{rel}"
                    )

    dist = ROOT / "dist"
    if dist.is_dir():
        needs_search = (dist / "portfolio" / "index.html").is_file() or (
            dist / "credentials" / "index.html"
        ).is_file()
        pf = dist / "pagefind" / "pagefind-ui.js"
        if needs_search and not pf.is_file():
            fail(
                "dist has Portfolio/Credentials but missing pagefind/pagefind-ui.js "
                "(run python scripts/build.py without --skip-pagefind)"
            )

    print("lint ok")


if __name__ == "__main__":
    main()
