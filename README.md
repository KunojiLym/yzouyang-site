# yzouyang-site

Public static site for [yzouyang.com](https://www.yzouyang.com/) — **WordPress migration**, Phase 1.

Agents open **draft PRs only**. No direct push to `main`.

## Phase 1

Routes: `/`, `/about/`, `/portfolio/`, `/credentials/`. Contact lives on Home as `#contact` (sticky header CTA); `/contact/` redirects there.

Data: vendored PUBLIC JSON from [personal-content](https://github.com/KunojiLym/personal-content) `export_public.py` in `data/export_public.json` (no private token in CI).

**Writing** stays on Blog / Medium / LinkedIn until **C2b**. About shows a curated **Selected writing** list of external links. Nav groups those destinations under **Elsewhere**, still marked external.

Preview / UAT: **offline** via `python scripts/preview.py`; **UAT publish** via branch `uat` (GitHub Pages) before promoting to `main`. See [docs/preview-uat.md](docs/preview-uat.md). Apex stays on WordPress until [docs/cutover.md](docs/cutover.md).

## Develop

Python deps (currently just PyYAML, for `data/career-journey.yaml`) are managed with [uv](https://docs.astral.sh/uv/) — see `pyproject.toml`. Run `uv sync` once (creates `.venv/`) before any of the commands below.

```bash
uv sync

# Offline preview (lint + build + Pagefind + local server)
uv run python scripts/preview.py

uv run python scripts/lint.py
uv run python scripts/build.py          # includes Pagefind (use --skip-pagefind to omit)
uv run python scripts/test_site_build.py
npm install
npx playwright install chromium
npm run serve:dist -- 8765              # optional local static server for dist/
npm run test:e2e
npm run test:motion                     # career journey slide motion, records video
```

The `serve:dist` server logs timestamped startup, listening, signal, close-start,
close-complete, timeout, and bind-error events. Playwright e2e starts and stops
the same Node server through global setup/teardown so lifecycle events are
visible during normal test runs.

`npm run test:e2e` includes the Career Journey motion check. That spec records
a Playwright video artifact and fails if the deck no longer advances
horizontally with active-slide animation.

CI builds with `SITE_BASE_PATH=/yzouyang-site` for https://kunojilym.github.io/yzouyang-site/. Local preview defaults to root (`base_path` empty). Contract tests + Playwright usability e2e run on every PR.

Optional repo secret **`NTFY_TOPIC_URL`** (full ntfy HTTPS URL; same topic as Alertmanager is fine): on `lint-build` or Pages `deploy` **failure**, CI POSTs the Actions run URL only. Unset = skip, job stays green. Never commit the URL.

Refresh export:

```bash
# in personal-content
python3 scripts/export_public.py yingzhao --check
cp people/yingzhao/data/export_public.json ../yzouyang-site/data/export_public.json
```

`data/export_public.json` must include `_meta.schema_version == 1` and
`_meta.visibility == "PUBLIC"`. `scripts/lint.py` recursively rejects
non-public visibility markers anywhere in the vendored export.

## Analytics

Configured in `data/site.json` → `analytics`:

| Provider | Status | Notes |
|---|---|---|
| **DIY** (supplement) | on | First-party beacon → your collector; see [docs/diy-tracking.md](docs/diy-tracking.md) |
| **Jetpack Stats** | on (default) | Same WordPress.com blog id as live WP (`34802711`); page ids mapped from WP REST |
| **GA4** | optional | Set `ga_measurement_id` to `G-…` to inject gtag (IP anonymized) |

Live yzouyang.com today uses Jetpack Stats (`stats.wp.com`), not GA. Preview hosts report with `srv = location.hostname`. DIY is additive — set `analytics.diy.collect_url` after deploying `collect/` Worker or local `diy_collect.py`.

## Docs

- [docs/site-builder.md](docs/site-builder.md) — build pipeline, config map, IA rules
- [docs/design-system.md](docs/design-system.md) — senior enterprise briefing contract (tokens, proof hierarchy, components)
- [docs/preview-uat.md](docs/preview-uat.md) — offline preview + UAT branch publish
- [docs/diy-tracking.md](docs/diy-tracking.md) — first-party beacon + collectors
- [docs/redirects.md](docs/redirects.md) — WP → static map
- [docs/cutover.md](docs/cutover.md) — DNS operator gate
- [docs/c2b-writing-inventory.md](docs/c2b-writing-inventory.md) — deferred writing corpus
