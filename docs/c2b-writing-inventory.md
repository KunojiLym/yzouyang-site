# C2b — writing inventory (2026-09)

**Status:** 18 PUBLIC essays in `personal-content` `writing.yaml`; bodies vendored via export; site reads `export.writing` only.

## Corpus (deduped)

| NOTE id | Title | Medium | WP slug |
|---|---|---|---|
| NOTE-2026-005 | AI Disruption Part 1 | yes | `the-ai-disruption-part-1-…` |
| NOTE-2026-006-2 | AI Disruption Part 2 | yes | `the-ai-disruption-part-2-…` |
| NOTE-2026-006 | AI Disruption Part 3 | yes | `the-ai-disruption-part-3-…` |
| NOTE-2026-002 | Chips, Cells and Code | yes | `chips-cells-and-code-…` |
| NOTE-2026-007 | Graphify × Databricks | yes | `teaching-graphify-to-understand-databricks-notebooks` |
| NOTE-2026-007-2 | Hugging Face open-weights | yes | `a-chinese-open-weights-model-…` |
| NOTE-2025-010 … NOTE-2025-021 | BYOLA Parts 1–12 | yes | `build-your-own-linkedin-analytics-part-*` |

LinkedIn article URLs: operator paste into `syndication.linkedin` when available (no scrape in CI).

## Site behaviour

- Notes panels render on-site markdown + **Discuss on Medium** (or LinkedIn when set).
- Footer **Blog** → `/notes/` (`footer_only` — not in header nav).
- WP permalinks → `/notes/#NOTE-*` via `dist/<slug>/` stubs + Cloudflare `_redirects` for `/blog/`.
- `site.json` **must not** contain `writing_highlights`.

## Operator tools

| Task | Command / location |
|---|---|
| Import / refresh bodies from WP | `python scripts/import_writing_bodies.py yingzhao` (Mac; not public CI) |
| Export + check | `python scripts/export_public.py yingzhao --check` |
| Vendor to site | copy `export_public.json` → `yzouyang-site/data/` |
| Draft preview | `python scripts/preview.py --include-drafts ../personal-content` |
| Weekly new URL scan | Dagster job `writing_weekly_ingest` (`agentic-services/writing_pipeline/`) |

## Still operator-owned (C2a / C2c)

- DNS apex cutover, Bitly repoint, `online-presence.yaml` Bitly removal
- Smoke WP slug redirects, then decommission Bluehost WP
- Medium / LinkedIn stay live — do not 301 or unpublish

See Homelab [yzouyang-wordpress-replacement runbook](https://github.com/KunojiLym/Homelab/blob/main/docs/runbooks/yzouyang-wordpress-replacement.md).
