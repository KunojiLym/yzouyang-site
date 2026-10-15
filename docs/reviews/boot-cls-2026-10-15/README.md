# Boot CLS — library deep links

Measured with `scripts/measure_boot_cls_matrix.mjs` against local `dist` (same flow as `library boot CLS` e2e: `load` → active panel → `document.fonts.ready` → CLS stable). Tables below are generated from `cls-before.json` and `cls-after.json` via `scripts/generate_boot_cls_readme.mjs`. Budget **0.1**.

## What changed

- **Header (769–900px):** fixed `12.5rem` (200px) `.header-search` slot + `#search` min-height so Pagefind mount does not wrap the action row or shrink the library grid (`chrome.css`, pre-fix baseline `862e9d8`).
- **Split-pane frame:** `--library-foot-reserve` on `.library-shell` plus strip/footer `min-height` so the painted grid no longer jumps **~376px → ~322px** when strip + footer parse after the frame (`library.css`).

Playwright gate (`library boot CLS`): deep links @ **769**, **784**, **800**, **900**, and **1024** — all **< 0.1**.

## dark

| Route | 769 | 784 | 800 | 900 | 1024 |
| --- | ---: | ---: | ---: | ---: | ---: |
| notes | 0.089 → **0.012** | 0.087 → **0.018** | 0.087 → **0.011** | 0.008 | 0.012 → **0.006** |
| systems | 0.134 → **0.013** | 0.080 → **0.013** | 0.136 → **0.006** | 0.016 | 0.004 → **0.003** |
| credentials | 0.148 → **0.006** | 0.094 → **0.005** | 0.069 → **0.008** | 0.011 | 0.025 → **0.003** |

## light

| Route | 769 | 784 | 800 | 900 | 1024 |
| --- | ---: | ---: | ---: | ---: | ---: |
| notes | 0.089 → **0.011** | 0.087 → **0.018** | 0.088 → **0.018** | 0.015 | 0.012 → **0.012** |
| systems | 0.004 → **0.013** | 0.064 → **0.003** | 0.091 → **0.005** | 0.016 | 0.024 → **0.011** |
| credentials | 0.149 → **0.015** | 0.149 → **0.015** | 0.152 → **0.018** | 0.002 | 0.025 → **0.002** |

## Screenshots @ 784px (`/systems/#SYS-03`)

Header: `before-header-784-*.png` → `after-header-784-*.png`. Viewport: `before-systems-784-*.png` → `after-systems-784-*.png`.
