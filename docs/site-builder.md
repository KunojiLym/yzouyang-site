# Site builder

How the static site is produced and extended. Visual rules live in [design-system.md](design-system.md).

## Pipeline

```text
data/site.json  +  data/export_public.json  +  data/career-journey.yaml
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

- **Config / chrome / curated writing / outcomes:** [`data/site.json`](../data/site.json)
- **PUBLIC narrative + projects + certs:** vendored from [personal-content](https://github.com/KunojiLym/personal-content) `export_public.py` → [`data/export_public.json`](../data/export_public.json)
- **Career Journey slide content:** [`data/career-journey.yaml`](../data/career-journey.yaml) (+ Tier 3 partials in `data/career-journey-slides/`) — see [career-journey-native-plan.md](career-journey-native-plan.md) for the schema
- **Styles:** [`src/styles/`](../src/styles/) modules → assembled by build into `dist/styles.css` (see [`src/styles/README.md`](../src/styles/README.md))
- **No Jinja** — page HTML is built in [`scripts/build.py`](../scripts/build.py)
- **Python deps** (currently just PyYAML) managed with [uv](https://docs.astral.sh/uv/) — `pyproject.toml` is this repo's uv project file; run `uv sync` once before any script below

## Scripts

| Script | Role |
|---|---|
| `uv run python scripts/lint.py` | Input validation (`site.json` / export / `career-journey.yaml`); Pagefind presence if `dist/` exists |
| `uv run python scripts/build.py` | Write pages + assets; runs Pagefind unless `--skip-pagefind` |
| `uv run python scripts/preview.py` | Lint → build → local `http.server` |
| `uv run python scripts/test_site_build.py` | Contract checks on `dist/` |
| `npm run test:e2e` | Playwright usability (serves root-path `dist/`) |

Build flags:

- `--base-path /yzouyang-site` or env `SITE_BASE_PATH` — prefix asset/nav URLs for GitHub project Pages
- `--skip-pagefind` — HTML only (search UI will 404)

CI builds Pages with `SITE_BASE_PATH=/yzouyang-site`, uploads that artifact, then **rebuilds with empty base path** before Playwright so CSS/Pagefind resolve at `/`.

## `site.json` map

| Key | Purpose |
|---|---|
| `person` | Name, brand, headline, tagline, location, platforms (≤4 on Home), photo |
| `outcomes` | Curated Home proof: `{ "metric", "label" }` (2–3; public CV facts only) |
| `contact` | PUBLIC email + phone (never work/university domains) |
| `external` | Blog, Medium, LinkedIn, GitHub, Bitly shorts, digital card hub |
| `nav` | Primary links (internal + external). **No Contact item** |
| `writing_highlights` | Curated About list: `title`, `url`, `venue`, `date` |
| `analytics` | Jetpack / optional GA4 / DIY beacon |
| `base_path` | Overridden by CLI/env at build time |

## Page builders

| Route | Builder | Sources |
|---|---|---|
| `/` | `build_home` | `person` + `outcomes` + platform proof strip; `#contact` from `contact`/`external` |
| `/about/` | `build_about` | export `about` + `writing_highlights`; longform sidebar (no Pagefind) |
| `/portfolio/` | `build_portfolio` | export `portfolio` + `projects` + Pagefind (case rows: outcome → scope → tools) |
| `/credentials/` | `build_credentials` | export `credentials` + certs/edu + Pagefind |
| `/career-journey/` | `build_career_journey` | `data/career-journey.yaml`; only built if that file exists. Not in primary nav — reachable from an About link card + direct/shared URL, same tier as Contact. See [career-journey-native-plan.md](career-journey-native-plan.md) |
| `/contact/` | `build_contact_redirect` | Meta refresh + link to `/#contact` |

## IA rules

- Home is a **proof-led dossier**: headline → outcomes → location/platforms → CTAs → `#contact`
- **Sticky header** — always reachable; **Contact** control jumps to `/#contact`
- Portfolio / Credentials / About — **sticky sidebar TOC** (`.page-with-toc`) with nested subcategories; major sections are collapsible (`.section-fold`)
- Contact is **not** a primary nav page; no cert-count vanity chip on Home
- Writing bodies stay on Blog / Medium / LinkedIn until **C2b**; About shows curated external titles only (publications-style)
- Blog / Medium / LinkedIn remain external (`↗`)
- Public footer (© + mailto + social) — no migration changelog in chrome

## Progressive embeds

Figma (and similar) iframes are an implementation pattern, not brand chrome:

- Always pair the iframe with a visible **Open deck** / `.embed-fallback` link
- Prefer a direct Figma URL from project bullets when available
- Blank or blocked iframes must still leave the fallback usable
- Do not treat embeds as the primary proof signal — case copy (outcome → scope → tools) comes first

## Adding a new page or component

A checklist for adding a new page, section, or component without reintroducing the raw-value drift Phase 1–3 cleaned up. Read [design-system.md](design-system.md) first for the visual contract (palette, type/spacing/radius scales, IA rules); this section is the mechanical "what do I touch, in what order" companion.

1. **Reach for a token before writing a number.** Every `font-size` needs a `--text-*` (or `--text-display-*` if it's a fluid heading); every `margin`/`padding`/`gap` needs a `--space-*`; every `border-radius` needs a `--radius-*`. The full tables are in design-system.md's "Layer A" section. If nothing fits, that's a signal to reconsider the layout — don't invent a one-off. If a one-off is genuinely unavoidable (e.g. something intentionally relative to a parent font-size), add it with a `/* intentional one-off: why */` comment and register it in `.stylelintrc.json`'s `ignoreValues`, the same way the `chrome.css` arrow markers are handled.
2. **Reuse an existing breakpoint.** `--bp-sm` (800px, hero-style two-column collapse) and `--bp-md` (900px, nav/sidebar collapse) are the only two in use — see design-system.md's "Breakpoints" table. A new third breakpoint is a design decision to write down in design-system.md, not a silent `@media` addition (custom properties can't be read inside `@media`, so breakpoints are documented constants, not `var()`).
3. **Pick the right CSS module.** `src/styles/README.md` has the file-by-file responsibility table (chrome vs. home vs. components vs. longform vs. search vs. motion). Add rules to the module that already owns that concern rather than starting a new file.
4. **Colors and fonts come from `tokens.css` only.** No raw hex codes or `font-family` literals in any other CSS file — `scripts/check_token_drift.py` fails CI on both.
5. **Update `data/site.json` / builder in `scripts/build.py`**, not a hardcoded HTML string, if the new page/section needs new content fields — see the `site.json` map and Page builders tables above.
6. **Run the checks locally before opening a PR** (all also run in CI, `.github/workflows/ci.yml`):
   - `python scripts/lint.py` — data contract
   - `python scripts/check_token_drift.py` — raw hex/font-family outside `tokens.css`
   - `npm run lint:css` — raw font-size/spacing/radius outside `var(--...)`
   - `npm run test:e2e` — Playwright usability
   - `npm run test:a11y` — axe-core WCAG2A/AA
   - `npm run test:visual` — visual regression (currently non-blocking in CI until baseline screenshots exist; still worth running locally to see if your change moved anything)
7. **If the change is visually intentional**, regenerate visual baselines (`npx playwright test tests/e2e/visual.spec.mjs --update-snapshots`, see the header comment in that file) and commit the updated `__snapshots__` images alongside the change, so the diff is reviewed once rather than failing silently later.

## Agent / contributor rules

- Open **draft PRs only**; do not push or merge to `main`
- Do not decrypt SOPS or commit secrets
- Do not commit `qa-shots/`, `test-results/`, or `playwright-report/`
- Prefer `op://` for any credentials; never paste secret values into chat or commits
- Do not invent outcome metrics — only operator-curated public facts in `site.outcomes`

## Related ops docs

- [preview-uat.md](preview-uat.md) — offline + UAT publish
- [redirects.md](redirects.md) — WP → static map
- [cutover.md](cutover.md) — DNS operator gate
- [diy-tracking.md](diy-tracking.md) — first-party beacon
- [c2b-writing-inventory.md](c2b-writing-inventory.md) — deferred writing corpus
- [design-system.md](design-system.md) — visual / proof contract
