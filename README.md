# yzouyang-site

Public static site for [yzouyang.com](https://www.yzouyang.com/) — **WordPress migration**, Phase 1.

Agents open **draft PRs only**. No direct push to `main`.

## Phase 1

Routes: `/`, `/about/`, `/portfolio/`, `/credentials/`, `/contact/`.

Data: vendored PUBLIC JSON from [personal-content](https://github.com/KunojiLym/personal-content) `export_public.py` in `data/export_public.json` (no private token in CI).

**Writing** (Blog / Medium / LinkedIn articles & newsletter) stays on existing hosts until **C2b**. Nav links out with an external marker.

Preview: GitHub Pages (Actions deploy) while WordPress remains on the apex until operator cutover. See [docs/cutover.md](docs/cutover.md).

## Develop

```bash
python scripts/lint.py
python scripts/build.py
npx pagefind@1.3.0 --site dist
# optional: python -m http.server -d dist 8080
```

Refresh export:

```bash
# in personal-content
python3 scripts/export_public.py yingzhao --check
cp people/yingzhao/data/export_public.json ../yzouyang-site/data/export_public.json
```

## Docs

- [docs/redirects.md](docs/redirects.md) — WP → static map
- [docs/cutover.md](docs/cutover.md) — DNS operator gate
- [docs/c2b-writing-inventory.md](docs/c2b-writing-inventory.md) — deferred writing corpus
