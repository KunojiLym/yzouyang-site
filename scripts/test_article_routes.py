"""Publication identity, metadata, search and migration contracts for real built pages."""

from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
from html import unescape
from pathlib import Path
from unittest.mock import patch

from build import (article_json_ld, article_path, build_article, layout,
                   publication_routes, resolve_site_base_path)

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def meta(html: str, key: str) -> str:
    match = re.search(rf'<meta (?:name|property)="{re.escape(key)}" content="([^"]*)"', html)
    return unescape(match[1]) if match else ""


def canonical(html: str) -> str:
    return unescape(re.search(r'<link rel="canonical" href="([^"]+)"', html)[1])


class ArticleTests(unittest.TestCase):
    def test_ids_survive_reordering_and_title_changes(self):
        rows = [{"id": "NOTE-2026-001", "title": "Before"}, {"id": "NOTE-2026-002"}]
        original, _ = publication_routes(rows)
        rows[0]["title"] = "Completely different title"
        reordered, _ = publication_routes(list(reversed(rows)))
        self.assertEqual({n: article_path(n) for _, n in original}, {n: article_path(n) for _, n in reordered})

    def test_ambiguous_and_unsafe_publication_inputs_fail(self):
        for rows in ([{}], [{"id": "NOTE-../escape"}], [{"id": "NOTE-2026-1"}] * 2,
                     [{"id": "NOTE-X"}, {"id": "NOTE-x"}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                publication_routes(rows)
        for url in ("https://example.org/article/", "https://www.yzouyang.com/../outside/",
                    "https://www.yzouyang.com/notes/", "https://www.yzouyang.com/%2e%2e/",
                    "https://www.yzouyang.com/article/?p=1"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                publication_routes([{"id": "NOTE-2026-1", "syndication": {"wordpress": url}}])
        with self.assertRaises(ValueError):
            publication_routes([{"id": nid, "syndication": {"wordpress": "https://www.yzouyang.com/same/"}}
                                for nid in ("NOTE-1", "NOTE-2")])

    def test_metadata_for_preview_live_and_root_preview(self):
        source = json.loads((ROOT / "data/site.json").read_text(encoding="utf-8"))
        row = {"id": "NOTE-2026-001", "title": 'A <system> & "judgment"',
               "teaser": "Specific article description.", "date": "2026-10-25", "body_md": "A paragraph."}
        for preview, uat, root_override in ((True, "", False), (True, "1", True), (False, "", False), (False, "1", False)):
            with self.subTest(preview=preview, uat=uat, root=root_override):
                site = deepcopy(source)
                site["deploy"]["preview_mode"] = preview
                site["base_path"] = resolve_site_base_path(site, explicit="" if root_override else None,
                                                          explicit_set=root_override)
                with patch.dict("os.environ", {"SITE_UAT_BUILD": uat, "PREVIEW_INCLUDE_DRAFTS": ""}):
                    page = layout(site, row["title"], "Notes", build_article(site, row, row["id"]),
                                  path=article_path(row["id"]), article=row,
                                  extra_head=article_json_ld(site, row, row["id"]))
                origin = site["deploy"]["preview_origin"] if preview else site["public_origin"]
                self.assertEqual(canonical(page), origin + "/notes/note-2026-001/")
                self.assertEqual(meta(page, "og:url"), canonical(page))
                self.assertEqual(meta(page, "og:type"), "article")
                self.assertEqual(meta(page, "description"), row["teaser"])
                self.assertEqual(meta(page, "robots"), "noindex, nofollow" if uat else ("noindex, follow" if preview else ""))
                self.assertIn('data-standalone-article="true"', page)
                self.assertNotIn('data-panel-id="NOTE-2026-001" hidden', page)
                self.assertIn('href="' + site["base_path"] + '/notes/">All notes', page)

    def test_article_schema_escapes_script_end_and_uses_own_url(self):
        site = {"public_origin": "https://example.org", "person": {"full_name": "Author"}}
        raw = article_json_ld(site, {"title": "</script><script>bad</script>", "url": "https://syndication.example/article"}, "NOTE-1")
        self.assertEqual(raw.count("</script>"), 1)
        data = json.loads(re.search(r'>(.*)</script>', raw)[1])
        self.assertEqual(data["url"], "https://example.org/notes/note-1/")
        self.assertEqual(data["mainEntityOfPage"], data["url"])

    def test_all_real_articles_sitemap_and_legacy_targets(self):
        export = json.loads((ROOT / "data/export_public.json").read_text(encoding="utf-8"))
        site = json.loads((DIST / "data/site.json").read_text(encoding="utf-8"))
        origin = site["deploy"]["preview_origin"] if site["deploy"]["preview_mode"] else site["public_origin"]
        sitemap = ET.parse(DIST / "sitemap.xml")
        locations = [el.text for el in sitemap.findall(".//{*}loc")]
        self.assertEqual(len(locations), len(set(locations)))
        mapping = json.loads((DIST / "url-map.json").read_text(encoding="utf-8"))
        self.assertEqual(len(mapping["articles"]), len(export["writing"]))
        notes = (DIST / "notes/index.html").read_text(encoding="utf-8")
        self.assertNotIn("data-pagefind-body", notes)
        self.assertNotIn('"@type":"Article"', notes)
        rules = (DIST / "_redirects").read_text(encoding="utf-8").splitlines()
        for row in export["writing"]:
            note_id = row["id"]
            path = article_path(note_id)
            html = (DIST / path.strip("/") / "index.html").read_text(encoding="utf-8")
            with self.subTest(note=note_id):
                self.assertEqual(canonical(html), origin + path)
                self.assertIn(origin + path, locations)
                self.assertEqual(meta(html, "description"), row.get("teaser") or row.get("summary") or row["title"])
                self.assertEqual(meta(html, "og:title"), row["title"] + " — " + site["person"]["full_name"])
                self.assertEqual(meta(html, "og:type"), "article")
                self.assertEqual(html.count('class="notes-entry"'), 1)
                self.assertIn("data-pagefind-body", html)
                self.assertIn(f'href="{site["base_path"]}{path}"', notes)
                schema = [json.loads(text) for text in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html)]
                article = next(block for block in schema if block["@type"] == "Article")
                self.assertEqual(article["headline"], row["title"])
                self.assertEqual(article["url"], canonical(html))
                self.assertEqual(article["datePublished"], row["date"])
        for old, new in mapping["redirects"].items():
            html = (DIST / old.strip("/") / "index.html").read_text(encoding="utf-8")
            self.assertEqual(canonical(html), origin + new)
            self.assertIn(f'content="0;url={site["base_path"]}{new}"', html)
            self.assertIn(f'{site["base_path"]}{old} {site["base_path"]}{new} 301', rules)


if __name__ == "__main__":
    unittest.main()
