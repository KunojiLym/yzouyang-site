# Boot CLS — library deep links

Measured with `scripts/measure_boot_cls_matrix.mjs` against local `dist` (same flow as `library boot CLS` e2e: `load` → active panel → `document.fonts.ready` → CLS stable). Tables below are generated from `cls-before.json` and `cls-after.json` via `scripts/generate_boot_cls_readme.mjs`. Budget **0.1**.

## What changed

- **Header (769–900px):** fixed `12.5rem` (200px) `.header-search` slot + `#search` min-height so Pagefind mount does not wrap the action row or shrink the library grid (`chrome.css`, pre-fix baseline `862e9d8`).
- **Library strip + footer:** `--library-strip-min-height` and `--library-page-footer-min-height` on `.library-strip` / `.library-page-footer` so strip and footer block size is stable before paint (no `max-height` reserve on `.library-frame` — that double-counted and left a ~52px gap under the footer).

Playwright gate (`library boot CLS`): deep links @ **375**, **768**, **769**, **784**, **800**, **900**, **1024**, and **1280** — all **< 0.1** in `cls-after.json`.

**Boot layout shifts:** `elementShiftMedian` in `cls-after.json` is the median of **3** Playwright runs (dark theme) at **769–1024px** for `div.library-pane`, `.library-panel-body`, and `.library-index-control`. Reading-context **boot-only** flex reserve applies to every library deep link during `.is-booting`, not only notes.

## dark

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.004 | 0.029 | 0.089 → **0.039** | 0.087 → **0.029** | 0.087 → **0.038** | 0.010 | 0.012 → **0.008** | 0.009 |
| systems | 0.021 | 0.003 | 0.134 → **0.046** | 0.080 → **0.045** | 0.136 → **0.048** | 0.045 | 0.004 → **0.037** | 0.014 |
| credentials | 0.009 | 0.010 | 0.148 → **0.052** | 0.094 → **0.052** | 0.069 → **0.027** | 0.044 | 0.025 → **0.016** | 0.017 |

## light

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.003 | 0.029 | 0.089 → **0.029** | 0.087 → **0.038** | 0.088 → **0.028** | 0.011 | 0.012 → **0.008** | 0.005 |
| systems | 0.021 | 0.003 | 0.004 → **0.046** | 0.064 → **0.046** | 0.091 → **0.048** | 0.023 | 0.024 → **0.016** | 0.014 |
| credentials | 0.009 | 0.010 | 0.149 → **0.024** | 0.149 → **0.052** | 0.152 → **0.055** | 0.019 | 0.025 → **0.039** | 0.017 |

## Screenshots @ 784px (`/systems/#SYS-03`)

Header: `before-header-784-*.png` → `after-header-784-*.png`. Viewport: `before-systems-784-*.png` → `after-systems-784-*.png`.
