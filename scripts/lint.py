#!/usr/bin/env python3
"""Lightweight lint for Phase 1 static site inputs."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Reuse build.py's constants rather than duplicating the layout/kind lists —
# scripts/ is on sys.path[0] when this file is run directly, so this is a
# plain sibling import, not a package import.
from build import compose_home_selected_row

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCROLL_NAV = {
    "Systems": "/systems/",
    "Notes": "/notes/",
    "Credentials": "/credentials/",
}
REQUIRED_PAGES = ("/systems/", "/notes/", "/credentials/")
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

    for key in ("projects", "certifications", "writing"):
        if key not in export or not isinstance(export[key], list):
            fail(f"export missing list: {key}")

    writing = export.get("writing") or []
    if len(writing) < 7:
        fail(f"export.writing must include at least 7 PUBLIC essays (found {len(writing)})")
    for row in writing:
        if not isinstance(row, dict):
            fail("export.writing entries must be objects")
        if not str(row.get("id") or "").startswith("NOTE-"):
            fail("export.writing entries need pinned NOTE-* id")
        if not row.get("title"):
            fail("export.writing entries need title")
        synd = row.get("syndication")
        if not isinstance(synd, dict) or not (synd.get("medium") or synd.get("linkedin")):
            fail(f"export.writing {row.get('id')} needs syndication.medium or syndication.linkedin")

    if site.get("writing_highlights") is not None:
        fail("site.writing_highlights must be removed — writing SoT is export.writing")

    for row in export.get("projects", []) + export.get("certifications", []):
        if isinstance(row, dict):
            vis = row.get("visibility_policy")
            if vis and vis != "PUBLIC":
                fail(f"non-PUBLIC record in export: {row.get('id') or row.get('name')} ({vis})")

    contact = site.get("contact") or {}
    if not contact.get("email"):
        fail("site.contact.email required")

    forbidden = ("prudential.com", "u.nus.edu", "gatech.edu")
    blob = json.dumps(site).lower()
    for needle in forbidden:
        if needle in blob:
            fail(f"site.json must not contain work/university contact domain: {needle}")

    nav = site.get("nav") or []
    nav_by_label = {
        item.get("label"): item for item in nav if isinstance(item, dict)
    }
    for label, anchor in SCROLL_NAV.items():
        item = nav_by_label.get(label)
        if not item or item.get("href") != anchor:
            fail(f"nav {label} must scroll to {anchor}")

    nav_labels = [item.get("label") for item in nav if not item.get("external")]
    for label in ("Systems", "Notes", "Credentials"):
        if label not in nav_labels:
            fail(f"nav missing primary item {label}")
    if "Portfolio" in nav_labels or "Work" in nav_labels:
        fail("nav must label /portfolio/ as Systems, not Work or Portfolio")
    if "Home" in nav_labels:
        fail("Home must be the brand mark, not a primary nav item")

    themes = site.get("operating_themes")
    if not isinstance(themes, list) or len(themes) != 4:
        fail("site.operating_themes must be a list of 4")
    for row in themes:
        if not isinstance(row, dict) or not (row.get("title") and row.get("body")):
            fail("operating_themes entries need title and body")

    if not (site.get("page_meta") or {}).get("Home"):
        fail("site.page_meta.Home required (do not reuse the role headline as every description)")
    if not str(site.get("public_origin") or "").startswith("http"):
        fail("site.public_origin must be an absolute http(s) origin")

    external_labels = {"Medium", "LinkedIn", "GitHub"}
    for item in nav:
        if item.get("label") in external_labels and not item.get("external"):
            fail(f"{item.get('label')} nav entry must be external")
        if item.get("label") == "Blog":
            if not item.get("footer_only"):
                fail("Blog nav entry must be footer_only (not in header nav)")
            if item.get("href") != "/notes/":
                fail("Blog nav entry href must be /notes/")
            if item.get("external"):
                fail("Blog nav entry must be on-site (/notes/, external=false)")
    seen_external = {item.get("label") for item in nav if item.get("external")}
    if "GitHub" not in seen_external:
        fail("nav external links must include GitHub")

    current_index = site.get("current_index")
    highlights = site.get("home_highlights")
    if highlights is not None and not isinstance(highlights, dict):
        fail("site.home_highlights must be an object when set")
    rotation = "weekly"
    if isinstance(highlights, dict):
        rotation = str(highlights.get("rotation") or "weekly").strip().lower()
        if rotation not in {"weekly", "pinned"}:
            fail("home_highlights.rotation must be weekly or pinned")
    if rotation == "pinned":
        if not isinstance(current_index, list) or not current_index:
            fail("current_index required when home_highlights.rotation is pinned")
        allowed_topics = {"notes", "systems"}
        for row in current_index:
            if not isinstance(row, dict):
                fail("current_index entries must be objects")
            topic = str(row.get("topic") or "").strip().lower()
            if topic not in allowed_topics:
                fail(
                    "current_index entries need topic "
                    "(notes or systems)"
                )
            href = str(row.get("href") or "").strip()
            if not (str(row.get("label") or "").strip() and href):
                fail("current_index entries need label and href")
            if topic in {"notes", "systems"} and "#" not in href:
                fail(f"pinned current_index {topic} href must deep-link to a record (#NOTE-* / #SYS-*)")

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

    enterprise_copy = site.get("enterprise_copy")
    if enterprise_copy is not None:
        if not isinstance(enterprise_copy, dict):
            fail("site.enterprise_copy must be an object when set")
        for eid, overlay in enterprise_copy.items():
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(eid)):
                fail(
                    f"enterprise_copy key {eid!r} must be a heading_id slug, "
                    "not an export title string"
                )
            if not isinstance(overlay, dict):
                fail(f"enterprise_copy[{eid!r}] must be an object")
            href = str(overlay.get("evidence_href") or "").strip()
            if href and not href.startswith("https://"):
                fail(f"enterprise_copy[{eid!r}] evidence_href must be an https URL")
        if len(enterprise_copy) < 3:
            fail("enterprise_copy must include at least three cases")

    home_selected = site.get("home_selected")
    if home_selected is not None:
        if not isinstance(home_selected, list) or not (2 <= len(home_selected) <= 3):
            fail("site.home_selected must be a list of 2–3 rows when set")
        for row in home_selected:
            if not isinstance(row, dict):
                fail("home_selected entries must be objects")
            case_id = str(row.get("id") or "").strip()
            if not case_id:
                fail("home_selected entries need id pointing at enterprise_copy or project_copy")
            copy_ids = set()
            if isinstance(enterprise_copy, dict):
                copy_ids.update(enterprise_copy)
            pc = site.get("project_copy")
            if isinstance(pc, dict):
                copy_ids.update(pc)
            if case_id not in copy_ids:
                fail(
                    f"home_selected id {case_id!r} is not in enterprise_copy or project_copy"
                )
            for beat in ("problem", "role", "decision", "outcome"):
                if str(row.get(beat) or "").strip():
                    fail(
                        f"home_selected[{case_id!r}] must not re-author {beat}; "
                        "compose from enterprise_copy / project_copy"
                    )
            composed = compose_home_selected_row(site, row)
            if not (str(composed.get("title") or "").strip() and (
                str(composed.get("outcome") or "").strip()
                or str(composed.get("problem") or "").strip()
            )):
                fail("home_selected entries need title and a composed outcome or problem")
            tools = composed.get("tools") or []
            if tools and (not isinstance(tools, list) or len(tools) > 5):
                fail("home_selected tools must be a list of at most 5 labels")
            href = str(composed.get("href") or "")
            if href and not href.startswith("/systems"):
                fail("home_selected href must link through to /systems/")

    project_copy = site.get("project_copy")
    if project_copy is not None:
        if not isinstance(project_copy, dict):
            fail("site.project_copy must be an object when set")
        for pid, override in project_copy.items():
            if not isinstance(override, dict):
                fail(f"project_copy[{pid!r}] must be an object")
            tools = override.get("tools")
            if tools is not None and (not isinstance(tools, list) or len(tools) > 5):
                fail(f"project_copy[{pid!r}] tools must be a list of at most 5 labels")

    section_copy = site.get("section_copy")
    if section_copy is not None:
        if not isinstance(section_copy, dict):
            fail("site.section_copy must be an object when set")

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
        for label in ("Home", "About", "Work", "Portfolio", "Perspectives", "Credentials", "Contact"):
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

    dist = ROOT / "dist"
    if dist.is_dir():
        needs_search = (dist / "systems" / "index.html").is_file() or (
            dist / "credentials" / "index.html"
        ).is_file()
        pf = dist / "pagefind" / "pagefind-ui.js"
        if needs_search and not pf.is_file():
            fail(
                "dist has Systems/Credentials but missing pagefind/pagefind-ui.js "
                "(run python scripts/build.py without --skip-pagefind)"
            )

    print("lint ok")


if __name__ == "__main__":
    main()
