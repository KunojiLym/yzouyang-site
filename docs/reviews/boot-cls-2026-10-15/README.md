# Boot CLS — header search slot (769–900px)

Measured with `scripts/measure_boot_cls_matrix.mjs` against local `dist` (same flow as `library boot CLS` e2e: `load` → active panel → `document.fonts.ready` → CLS stable). Budget **0.1**.

## Before / after CLS

| Route | Width | Theme | Before | After |
| --- | ---: | --- | ---: | ---: |
| notes | 769 | dark | 0.090 | 0.029 |
| notes | 769 | light | 0.090 | 0.029 |
| notes | 784 | dark | 0.087 | 0.029 |
| notes | 784 | light | 0.087 | 0.029 |
| notes | 800 | dark | 0.087 | 0.038 |
| notes | 800 | light | 0.088 | 0.038 |
| notes | 1024 | dark | 0.012 | 0.012 |
| notes | 1024 | light | 0.012 | 0.012 |
| systems | 769 | dark | 0.134 | 0.031 |
| systems | 769 | light | 0.004 | 0.031 |
| systems | 784 | dark | 0.080 | 0.030 |
| systems | 784 | light | 0.064 | 0.030 |
| systems | 800 | dark | 0.136 | 0.031 |
| systems | 800 | light | 0.091 | 0.031 |
| systems | 1024 | dark | 0.004 | 0.003 |
| systems | 1024 | light | 0.024 | 0.003 |
| credentials | 769 | dark | 0.148 | 0.035 |
| credentials | 769 | light | 0.149 | 0.035 |
| credentials | 784 | dark | 0.094 | 0.035 |
| credentials | 784 | light | 0.149 | 0.035 |
| credentials | 800 | dark | 0.069 | 0.038 |
| credentials | 800 | light | 0.152 | 0.038 |
| credentials | 1024 | dark | 0.025 | 0.025 |
| credentials | 1024 | light | 0.025 | 0.025 |

Before = pre-fix `chrome.css` @ `862e9d8` (Pagefind mount wrapped search at `width <= 900px`, shrinking the stacked library grid). After = fixed `12.5rem` search slot + `#search` min-height on the `48rem–900px` band.

Playwright gate (post-fix): `/systems/#SYS-03` @ **784**, **800**, **1024**, **769** and credentials deep link @ same widths — all **&lt; 0.1** in `library boot CLS`.

## Screenshots @ 784px (`/systems/#SYS-03`)

Stable-state header after load (visible layout change: search stays on the action row).

| | Light | Dark |
| --- | --- | --- |
| Before | `before-header-784-light.png` | `before-header-784-dark.png` |
| After | `after-header-784-light.png` | `after-header-784-dark.png` |

Full viewport: `before-systems-784-*.png` → `after-systems-784-*.png`.

Raw JSON: `cls-before.json`, `cls-after.json`.
