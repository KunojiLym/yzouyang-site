# Redirect map (Phase 1)

WordPress (Responsive theme on Bluehost shared) → static paths. Individual post permalinks redirect to on-site notes after C2b (see [c2b-writing-inventory.md](c2b-writing-inventory.md)).

| Old WP path | New static | Notes |
|---|---|---|
| `/` | `/` | Home |
| `/about/` | `/` | Redirect stub |
| `/portfolio/`, `/work/`, `/systems/catalogue/` | `/systems/` | Also `bit.ly/3GGyiXF` |
| `/perspectives/`, `/blog/` | `/notes/` | Writing corpus on `/notes/`; library JS may append `#NOTE-*` |
| `/credentials/` | `/credentials/` | Also `bit.ly/4m4fqki` |
| `/contact/` | `/` | Redirect stub; email lives in the library-card footer |
| `/career-journey/` | `/` | Redirect stub (native page deferred — see [career-journey-native-plan.md](career-journey-native-plan.md)) |
| `/category/**` | *(keep WP until cutover)* | Decommission with WP |
| Post permalinks | `/notes/#NOTE-*` | Per-slug stubs under `dist/<slug>/` |
| `/author/**`, feeds, `wp-json` | *(keep WP until cutover)* | Decommission with WP |

Build emits `dist/_redirects` for trailing-slash normalization and bulk rules (e.g. `/blog/` → `/notes/`) on hosts that honor it (e.g. Cloudflare Pages). GitHub Pages relies on `/about/index.html` style paths plus meta refresh / JS redirect stubs where needed.
