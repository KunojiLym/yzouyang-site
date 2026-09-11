# Redirect map (Phase 1)

WordPress (Responsive theme on Bluehost shared) → static paths. Blog/post permalinks stay on WP until C2b.

| Old WP path | New static | Notes |
|---|---|---|
| `/` | `/` | Home |
| `/about/` | `/about/` | |
| `/portfolio/` | `/portfolio/` | Nav label **Systems**. Also `bit.ly/3GGyiXF`. `/work/` → `/portfolio/` |
| `/perspectives/` | `/perspectives/` | Nav label **Notes** — start-here writing index |
| `/credentials/` | `/credentials/` | Also `bit.ly/4m4fqki` |
| `/contact/` | `/contact/` | Nav label **Connect**. Own page (email + profiles). Home still has `#contact` for old bookmarks. `_redirects` 301 `/contact` → `/contact/` |
| `/blog/` | *(keep WP)* | External until C2b |
| `/category/**` | *(keep WP)* | |
| Post permalinks | *(keep WP)* | e.g. `/a-chinese-open-weights-…/` |
| `/author/**`, feeds, `wp-json` | *(keep WP)* | Decommission with WP |

Build emits `dist/_redirects` for trailing-slash normalization on hosts that honor it (e.g. Cloudflare Pages). GitHub Pages relies on `/about/index.html` style paths.
