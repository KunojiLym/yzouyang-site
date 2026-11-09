# Redirect map (Phase 1)

WordPress (Responsive theme on Bluehost shared) → static paths. Individual post permalinks redirect to on-site notes after C2b (see [c2b-writing-inventory.md](c2b-writing-inventory.md)).

| Old WP path | New static | Notes |
|---|---|---|
| `/` | `/` | Home |
| `/about/` | `/` | Redirect stub |
| `/portfolio/`, `/work/`, `/systems/catalogue/` | `/systems/` | Also `bit.ly/3GGyiXF` |
| `/perspectives/`, `/blog/` | `/notes/` | Library index; JS may append `#NOTE-*` for a panel. Essays also have `/notes/note-*/` |
| `/credentials/` | `/credentials/` | Also `bit.ly/4m4fqki` |
| `/contact/` | `/` | Redirect stub; email lives in the library-card footer |
| `/career-journey/` | `/` | Redirect stub (native page deferred — see [career-journey-native-plan.md](career-journey-native-plan.md)) |
| `/category/**` | *(keep WP until cutover)* | Decommission with WP |
| Post permalinks | `/notes/note-*/` | Per-slug stubs and `_redirects` rules; exact map in generated `url-map.json` |
| Saved `/notes/#NOTE-*` links | Existing library view | Preserved; each panel links to its independent article |
| `/author/**`, feeds, `wp-json` | *(keep WP until cutover)* | Decommission with WP |

Build emits `dist/_redirects` for trailing-slash normalization and bulk rules (e.g. `/blog/` → `/notes/`) on hosts that honor it (e.g. Cloudflare Pages). GitHub Pages relies on `/about/index.html` style paths plus meta refresh / JS redirect stubs where needed.

Article paths use the lowercase stable export ID, e.g. `NOTE-2026-005` → `/notes/note-2026-005/`. Changing a title or category does not change the URL. Duplicate IDs and unsafe/colliding legacy paths fail the build. Do not rename a published ID without an explicit migration. Each article has its own server-rendered metadata, canonical and Article schema; `/notes/` retains the library but is excluded from Pagefind to avoid duplicate search results. `sitemap.xml` lists primary pages and all article URLs. Previews remain noindex even though robots.txt permits crawling so crawlers can read that directive.

This follows Google's guidance on [crawlable links](https://developers.google.com/search/docs/crawling-indexing/links-crawlable) and [canonical URLs without fragments](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls). Inclusion in the sitemap does not guarantee indexing.
