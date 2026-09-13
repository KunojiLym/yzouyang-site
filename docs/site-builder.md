# Site builder

How the static site is produced and extended. Visual rules live in [design-system.md](design-system.md).

## Pipeline

```text
data/site.json  +  data/export_public.json  +  data/career-journey.yaml (lint-only; page deferred)
        │
        ▼
 scripts/build.py  (f-string HTML, copy assets/CSS)
        │
        ▼
     dist/**/index.html
        │
        ▼
 Pagefind index (systems + notes + credentials)
        │
        ▼
 preview.py  /  CI  /  GitHub Pages
```

- **Config / chrome / curated writing / outcomes:** [`data/site.json`](../data/site.json)
- **PUBLIC narrative + projects + certs:** vendored from [personal-content](https://github.com/KunojiLym/personal-content) `export_public.py` → [`data/export_public.json`](../data/export_public.json)
- **Career Journey (deferred):** [`data/career-journey.yaml`](../data/career-journey.yaml) is validated at lint time; `/career-journey/` currently **redirects to Home**. Native page plan: [career-journey-native-plan.md](career-journey-native-plan.md)
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
| `npm run test:e2e` | Playwright usability + theme (`tests/e2e/usability.spec.mjs`, `tests/e2e/theme.spec.mjs`) |
| `npm run test:a11y` | axe-core WCAG2A/AA on live routes |
| `npm run test:visual` | Screenshot regression (non-blocking in CI until baselines exist) |

Build flags:

- `--base-path /yzouyang-site` or env `SITE_BASE_PATH` — prefix asset/nav URLs for GitHub project Pages
- `--skip-pagefind` — HTML only (search UI will 404)

CI builds Pages with `SITE_BASE_PATH=/yzouyang-site`, uploads that artifact, then **rebuilds with empty base path** before Playwright so CSS/Pagefind resolve at `/`.

## `site.json` map

| Key | Purpose |
|---|---|
| `person` | Name, brand, headline (thesis), tagline, location, platforms (≤4 on Home) |
| `outcomes` | Curated proof metrics — used on matching SYS records, not a Home hero strip |
| `current_index` | Home highlight lines (systems / notes) |
| `nav` | Systems · Notes · Credentials; Blog/Medium/LinkedIn/GitHub are footer-only or `footer_only` |
| `page_meta` | Per-page meta descriptions (never reuse the role headline for every route) |
| `public_origin` | Canonical / OG origin (`https://www.yzouyang.com`) |
| `operating_themes` | *(deprecated on Home — empty)* |
| `contact` | PUBLIC email only (no visitor-facing phone) |
| `external` | Blog, Medium, LinkedIn, GitHub, Bitly shorts, digital card hub |
| `credentials_verify` | VERIFY panel links (issuer records already in export) |
| `home_selected` | Optional Home highlight pool: `{ id, record_id?, domains?, title, tools? }` |
| `enterprise_copy` | Work enterprise overlays keyed by stable `heading_id` (not the export title string). Extra keys not in the export are appended as additional cases. Optional `evidence_href` / `evidence_label` turn Evidence into a verification link. See deep-link note below |
| `project_copy` | Optional per-project `outcome` / `scope` / `tools` overrides (tools ≤5) |
| `section_copy` | Optional systems section intro overrides keyed by export section id |
| `analytics` | Jetpack / optional GA4 / DIY beacon |
| `base_path` | Overridden by CLI/env at build time |

### Enterprise heading ids

`enterprise_copy` is keyed by the Work heading `id`, not the live export title. Prudential keeps `prudential-singapore-senior-data-engineer-solutioning-architecture` so Home selected-systems links (and saved `#` URLs) stay valid after the visible title became Senior Manager (master CV). Lookup matches `slugify(export title)` first, then overlay `title` if the export string catches up. Do not rename that id without a redirect.

## Page builders

| Route | Builder | Sources |
|---|---|---|
| `/` | `build_home` | Token entrance + thesis + `current_index` + proof strip + `home-entry-grid` + competencies + library-card footer |
| `/systems/` | `build_systems` | Library shell from export + overlays; Pagefind “Search catalogue” |
| `/notes/` | `build_notes` | Library shell from PUBLIC writing; Pagefind |
| `/credentials/` | `build_credentials` | Library shell + VERIFY + Pagefind |
| `/about/`, `/contact/` | redirect stubs | 301 → `/` |
| `/portfolio/`, `/work/` | redirect stubs | 301 → `/systems/` |
| `/perspectives/`, `/blog/` | redirect stubs | 301 → `/notes/` (client may append first-panel hash) |
| `/career-journey/` | redirect stub | 301 → `/` |

## IA rules

- Home is a **Personal Systems Library entrance**: token atmosphere → thesis → current index → proof strip → catalogue entry grid → competencies. No system map, Reading room, Workshop, or `#contact` on Home
- **Sticky header** — always reachable; **theme toggle** in `.header-actions`
- Desktop primary nav is **Systems · Notes · Credentials**; Blog / Medium / LinkedIn / GitHub sit in the library-card footer
- Systems / Notes / Credentials use the **library split-pane** (`.library-shell`), not longform TOC
- No cert-count vanity chip on Home; no visitor-facing phone
- Writing bodies live on `/notes/` (PUBLIC export, C2b)
- Blog / Medium / LinkedIn / GitHub remain external (`↗`) except footer Blog → `/notes/`
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
3. **Pick the right CSS module.** `src/styles/README.md` has the file-by-file responsibility table (`chrome`, `home`, `library`, `components`, `longform`, `search`, `motion`). Add rules to the module that already owns that concern rather than starting a new file.
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

## Playwright

CI rebuilds with empty `SITE_BASE_PATH` before e2e so assets and Pagefind resolve at `/`. Config: [`playwright.config.mjs`](../playwright.config.mjs) — **desktop** and **mobile** projects; specs skip project-inappropriate cases (e.g. desktop layout tests on mobile, mobile back-button flow on desktop).

| Spec | Coverage |
|---|---|
| `tests/e2e/usability.spec.mjs` | Smoke on live routes; legacy redirect stubs; chrome (nav, skip-link, footer, reduced motion); home IA guardrails; library shell (systems hash, notes panel, credentials, Figma link, mobile index → panel → Back); header Pagefind; layout breakpoints |
| `tests/e2e/theme.spec.mjs` | Dark/light token paint without FOUC; `localStorage` theme persistence across reload; axe on themed routes |
| `tests/e2e/a11y.spec.mjs` | axe WCAG2A/AA on `/`, `/systems/`, `/notes/`, `/credentials/` (Pagefind `#search` excluded as third-party chrome) |
| `tests/e2e/visual.spec.mjs` | Full-page screenshots for `/`, `/systems/`, `/notes/`, `/credentials/` — **non-blocking** in CI until `__snapshots__/` is committed |

Redirect assertions allow optional panel hashes on `/systems/` and `/notes/` destinations because library JS may call `applyHash()` after navigation.

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
