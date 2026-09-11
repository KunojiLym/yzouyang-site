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
| `person` | Name, brand, headline (thesis), tagline, location, platforms (≤4 on Home), photo (Profile page) |
| `outcomes` | Curated proof metrics — surfaced on matching SYS records on Home, not hero strip |
| `atmosphere` | Three still slots: `entrance`, `reading`, `workshop` (`src`, `alt`, `width`, `height`, `object_position`) |
| `current_index` | Home status lines: studying / building / writing |
| `system_map` | Six domain nodes for Home SVG map |
| `workshop` | Home LAB rows: `record_id`, constraint, lesson, optional link |
| `nav` | Systems · Notes · Profile · Credentials · Connect, then external Blog/Medium/LinkedIn/GitHub under **Elsewhere** |
| `page_meta` | Per-page meta descriptions (never reuse the role headline for every route) |
| `public_origin` | Canonical / OG origin (`https://www.yzouyang.com`) |
| `operating_themes` | *(deprecated on Home — empty)* |
| `contact` | PUBLIC email only (no visitor-facing phone) |
| `external` | Blog, Medium, LinkedIn, GitHub, Bitly shorts, digital card hub |
| `credentials_verify` | VERIFY panel links (issuer records already in export) |
| `writing_highlights` | Curated About / Perspectives list: `title`, `url`, `venue`, `date`, optional `start_here` |
| `home_selected` | Home SYS records (2–3): `{ id, record_id?, domains?, title, tools? }`. Context/methods/impact compose from `enterprise_copy` / `project_copy` / `outcomes`; `href` defaults to `/portfolio/#{id}` |
| `enterprise_copy` | Work enterprise overlays keyed by stable `heading_id` (not the export title string). Extra keys not in the export are appended as additional cases. Optional `evidence_href` / `evidence_label` turn Evidence into a verification link. See deep-link note below |
| `project_copy` | Optional per-project `outcome` / `scope` / `tools` overrides (tools ≤5) |
| `section_copy` | Optional portfolio section intro overrides keyed by export section id |
| `analytics` | Jetpack / optional GA4 / DIY beacon |
| `base_path` | Overridden by CLI/env at build time |

### Enterprise heading ids

`enterprise_copy` is keyed by the Work heading `id`, not the live export title. Prudential keeps `prudential-singapore-senior-data-engineer-solutioning-architecture` so Home selected-systems links (and saved `#` URLs) stay valid after the visible title became Senior Manager (master CV). Lookup matches `slugify(export title)` first, then overlay `title` if the export string catches up. Do not rename that id without a redirect.

## Page builders

| Route | Builder | Sources |
|---|---|---|
| `/` | `build_home` | Entrance atmosphere + thesis + `current_index` + CTAs (View systems / Connect) + system map + SYS records + Reading room + Workshop + `#contact`; library-card footer |
| `/about/` (nav **Profile**) | `build_about` | export `about` + portrait + `writing_highlights`; longform sidebar (no Pagefind) |
| `/portfolio/` (nav **Systems**; `/work/` redirects here) | `build_portfolio` | Page title **Systems**; Pagefind label “Search the catalogue”; export + overlays |
| `/perspectives/` (nav **Notes**) | `build_perspectives` | Page title **Notes**; `writing_highlights` start-here + index; no Pagefind |
| `/credentials/` | `build_credentials` | Page title **Professional record**; export + VERIFY + Pagefind |
| `/contact/` (nav **Connect**) | `build_contact` | Page title **Connect**; `contact` + `external` |
| `/career-journey/` | `build_career_journey` | `data/career-journey.yaml`; only built if that file exists. Not in primary nav — reachable from Profile link + direct/shared URL. See [career-journey-native-plan.md](career-journey-native-plan.md) |

## IA rules

- Home is a **Personal Systems Library**: Entrance → system map → selected SYS records → Reading room → Workshop → `#contact` (bookmark; primary Connect is `/contact/`)
- **Sticky header** — always reachable; **theme toggle** in `.header-actions`; Connect is a primary nav item to `/contact/`
- Desktop primary nav is **Systems · Notes · Profile · Credentials · Connect**; Blog / Medium / LinkedIn / GitHub sit under **Elsewhere**
- Portfolio / Credentials / About / Perspectives — **sticky sidebar TOC** (`.page-with-toc`) with nested subcategories; major sections are collapsible (`.section-fold`)
- No cert-count vanity chip on Home; no visitor-facing phone
- Writing bodies stay on Blog / Medium / LinkedIn until **C2b**; `/perspectives/` is a start-here index (phase 1 tags + 3 start-here)
- Blog / Medium / LinkedIn / GitHub remain external (`↗`)
- Public footer is a **library card** (© + location/focus + mailto + social) — no migration changelog in chrome

## Progressive embeds

Figma (and similar) embeds are an implementation pattern, not brand chrome:

- Always keep a visible **Open deck** / `.embed-fallback` **or** the project’s existing Figma `.links` row (do not drop the compact link)
- Prefer a direct Figma URL from project bullets when available
- Do **not** load a live Figma iframe (the embed canvas paints white on the dark dossier)
- **Empty static frames are forbidden.** Do not emit `a.embed-frame-static` without a real `<img>` poster. A fill-only `aspect-ratio` box on `var(--bg-elevated)` is not a preview
- If a poster asset exists (`poster` on the project row / `site.json` `project_copy`), render a real `<img>` (max-height ~12–14rem / `13rem`), never a 16/10 empty panel
- Without a poster, keep the compact Figma link row only
- Do not treat embeds as the primary proof signal — case copy (outcome → scope → tools) comes first

## Adding a new page or component

A checklist for adding a new page, section, or component without reintroducing the raw-value drift Phase 1–3 cleaned up. Read [design-system.md](design-system.md) first for the visual contract (palette, type/spacing/radius scales, IA rules); this section is the mechanical "what do I touch, in what order" companion.

1. **Reach for a token before writing a number.** Every `font-size` needs a `--text-*` (or `--text-display-*` if it's a fluid heading); every `margin`/`padding`/`gap` needs a `--space-*`; every `border-radius` needs a `--radius-*`. The full tables are in design-system.md's "Layer A" section. If nothing fits, that's a signal to reconsider the layout — don't invent a one-off. If a one-off is genuinely unavoidable (e.g. something intentionally relative to a parent font-size), add it with a `/* intentional one-off: why */` comment and register it in `.stylelintrc.json`'s `ignoreValues`, the same way the `chrome.css` arrow markers are handled.
2. **Reuse an existing breakpoint.** `--bp-sm` (800px, entrance stack), `--bp-md` (900px, nav/sidebar collapse), `--bp-lg` (1024px, record grid) — see design-system.md.
3. **Pick the right CSS module.** `src/styles/README.md` has the file-by-file responsibility table (chrome vs. home vs. components vs. longform vs. search vs. motion). Add rules to the module that already owns that concern rather than starting a new file.
4. **Colors and fonts come from `tokens.css` only.** Dual-theme color tokens live in `:root, [data-theme="dark"]` and `[data-theme="light"]`. No raw hex codes or `font-family` literals in any other CSS file — `scripts/check_token_drift.py` fails CI on both.
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
