# Boot CLS — library deep links

Measured with `scripts/measure_boot_cls_matrix.mjs` against local `dist` (same flow as `library boot CLS` e2e: `load` → active panel → `document.fonts.ready` → CLS stable). Tables below are generated from `cls-before.json` and `cls-after.json` via `scripts/generate_boot_cls_readme.mjs`. Budget **0.1**.

## What changed

- **Header (769–900px):** fixed `12.5rem` (200px) `.header-search` slot + `#search` min-height so Pagefind mount does not wrap the action row or shrink the library grid (`chrome.css`, pre-fix baseline `862e9d8`).
- **Library strip + footer:** `--library-strip-min-height` and `--library-page-footer-min-height` on `.library-strip` / `.library-page-footer` so strip and footer block size is stable before paint (no `max-height` reserve on `.library-frame` — that double-counted and left a ~52px gap under the footer).

Playwright gate (`library boot CLS`): deep links @ **375**, **768**, **769**, **784**, **800**, **900**, **1024**, and **1280** — all **< 0.1** in `cls-after.json`.

**Pane shift (Visual Design):** Removing `.library-frame` `max-height` reserve fixes the ~52px empty band under the footer and the ~19px Credentials pane jump from double-counting strip/footer. Index-control and notes reading-context **boot-only** reserves (scoped to `.library-panel--note.is-active`, not all mid-band widths) replace the round-4 regression that forced `display:flex` on `[hidden]` reading context for every notes route.

## dark

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.007 | 0.038 | 0.089 → **0.039** | 0.087 → **0.029** | 0.087 → **0.028** | 0.010 | 0.012 → **0.014** | 0.005 |
| systems | 0.022 | 0.003 | 0.134 → **0.030** | 0.080 → **0.030** | 0.136 → **0.031** | 0.008 | 0.004 → **0.024** | 0.002 |
| credentials | 0.010 | 0.010 | 0.148 → **0.040** | 0.094 → **0.035** | 0.069 → **0.009** | 0.003 | 0.025 → **0.025** | 0.005 |

## light

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.003 | 0.027 | 0.089 → **0.029** | 0.087 → **0.038** | 0.088 → **0.028** | 0.010 | 0.012 → **0.008** | 0.005 |
| systems | 0.022 | 0.003 | 0.004 → **0.030** | 0.064 → **0.003** | 0.091 → **0.031** | 0.007 | 0.024 → **0.024** | 0.002 |
| credentials | 0.009 | 0.010 | 0.149 → **0.035** | 0.149 → **0.007** | 0.152 → **0.010** | 0.028 | 0.025 → **0.025** | 0.005 |

## Screenshots @ 784px (`/systems/#SYS-03`)

Header: `before-header-784-*.png` → `after-header-784-*.png`. Viewport: `before-systems-784-*.png` → `after-systems-784-*.png`.
