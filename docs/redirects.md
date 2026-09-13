# Redirect map (Phase 1)

WordPress (Responsive theme on Bluehost shared) → static paths. Blog/post permalinks stay on WP until C2b.

| Old WP path | New static | Notes |
|---|---|---|
| `/` | `/` | Home |
| `/about/` | `/` | Redirect stub |
| `/portfolio/` | `/systems/` | Also `bit.ly/3GGyiXF`. `/work/` → `/systems/` |
| `/perspectives/` | `/notes/` | Writing lives on `/notes/` after C2b |
| `/credentials/` | `/credentials/` | Also `bit.ly/4m4fqki` |
| `/contact/` | `/` | Redirect stub; email lives in the library-card footer |
| `/career-journey/` | `/` | Redirect stub |
| `/blog/` | *(keep WP)* | External until C2b |
| `/category/**` | *(keep WP)* | |
| Post permalinks | *(keep WP)* | e.g. `/a-chinese-open-weights-…/` |
| `/author/**`, feeds, `wp-json` | *(keep WP)* | Decommission with WP |

Build emits `dist/_redirects` for trailing-slash normalization on hosts that honor it (e.g. Cloudflare Pages). GitHub Pages relies on `/about/index.html` style paths.
