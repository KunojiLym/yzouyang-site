# Site builder

How the Phase 1 static site is produced and extended. Visual rules live in [design-system.md](design-system.md).

## Pipeline

```text
data/site.json  +  data/export_public.json
        │
        ▼
 scripts/build.py  (f-string HTML, copy assets/CSS)
        │
        ▼
     dist/**/index.html
        │
        ▼
 Pagefind index (portfolio + credentials only)
        │
        ▼
 preview.py  /  CI  /  GitHub Pages
```

- **Config / chrome / curated writing:** [`data/site.json`](../data/site.json)
- **PUBLIC narrative + projects + certs:** vendored from [personal-content](https://github.com/KunojiLym/personal-content) `export_public.py` → [`data/export_public.json`](../data/export_public.json)
- **Styles:** [`src/styles.css`](../src/styles.css) → `dist/styles.css`
- **No Jinja** — page HTML is built in [`scripts/build.py`](../scripts/build.py)

## Scripts

| Script | Role |
|---|---|
| `python scripts/lint.py` | Input validation (`site.json` / export); Pagefind presence if `dist/` exists |
| `python scripts/build.py` | Write pages + assets; runs Pagefind unless `--skip-pagefind` |
| `python scripts/preview.py` | Lint → build → local `http.server` |
| `python scripts/test_site_build.py` | Contract checks on `dist/` |
| `npm run test:e2e` | Playwright usability (serves root-path `dist/`) |

Build flags:

- `--base-path /yzouyang-site` or env `SITE_BASE_PATH` — prefix asset/nav URLs for GitHub project Pages
- `--skip-pagefind` — HTML only (search UI will 404)

CI builds Pages with `SITE_BASE_PATH=/yzouyang-site`, uploads that artifact, then **rebuilds with empty base path** before Playwright so CSS/Pagefind resolve at `/`.

## `site.json` map

| Key | Purpose |
|---|---|
| `person` | Name, brand, headline, tagline, location, platforms, photo |
| `contact` | PUBLIC email + phone (never work/university domains) |
| `external` | Blog, Medium, LinkedIn, GitHub, Bitly shorts, digital card hub |
| `nav` | Primary links (internal + external). **No Contact item** |
| `writing_highlights` | Curated About list: `title`, `url`, `venue`, `date` |
| `analytics` | Jetpack / optional GA4 / DIY beacon |
| `base_path` | Overridden by CLI/env at build time |

## Page builders

| Route | Builder | Sources |
|---|---|---|
| `/` | `build_home` | `person` + proof metrics from export certs; `#contact` from `contact`/`external` |
| `/about/` | `build_about` | export `about` + `writing_highlights` |
| `/portfolio/` | `build_portfolio` | export `portfolio` + `projects` + Pagefind |
| `/credentials/` | `build_credentials` | export `credentials` + certs/edu + Pagefind |
| `/contact/` | `build_contact_redirect` | Meta refresh + link to `/#contact` |

## IA rules (Phase 1)

- **Sticky header** — always reachable; **Contact** control jumps to `/#contact`
- Contact is **not** a primary nav page
- Writing bodies stay on Blog / Medium / LinkedIn until **C2b**; About shows curated external titles only
- Blog / Medium / LinkedIn remain external (`↗`)
- Public footer (© + mailto + social) — no migration changelog in chrome

## Agent / contributor rules

- Open **draft PRs only**; do not push or merge to `main`
- Do not decrypt SOPS or commit secrets
- Do not commit `qa-shots/`, `test-results/`, or `playwright-report/`
- Prefer `op://` for any credentials; never paste secret values into chat or commits

## Related ops docs

- [preview-uat.md](preview-uat.md) — offline + UAT publish
- [redirects.md](redirects.md) — WP → static map
- [cutover.md](cutover.md) — DNS operator gate
- [diy-tracking.md](diy-tracking.md) — first-party beacon
- [c2b-writing-inventory.md](c2b-writing-inventory.md) — deferred writing corpus
