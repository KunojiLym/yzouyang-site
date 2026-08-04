#!/usr/bin/env python3
"""Lightweight lint for Phase 1 static site inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REQUIRED_PAGES = ("/", "/about/", "/portfolio/", "/credentials/", "/contact/")


def fail(msg: str) -> None:
    print(f"lint error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    export_path = DATA / "export_public.json"
    site_path = DATA / "site.json"
    if not export_path.is_file():
        fail(f"missing {export_path}")
    if not site_path.is_file():
        fail(f"missing {site_path}")

    export = json.loads(export_path.read_text(encoding="utf-8"))
    site = json.loads(site_path.read_text(encoding="utf-8"))

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

    hrefs = {item.get("href") for item in site.get("nav") or []}
    for path in REQUIRED_PAGES:
        if path not in hrefs:
            fail(f"nav missing {path}")

    external_labels = {"Blog", "Medium", "LinkedIn"}
    for item in site.get("nav") or []:
        if item.get("label") in external_labels and not item.get("external"):
            fail(f"{item.get('label')} nav entry must be external until C2b")

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

    print("lint ok")


if __name__ == "__main__":
    main()
