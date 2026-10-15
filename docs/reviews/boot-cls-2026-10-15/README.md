# Boot CLS — library deep links

Measured with `scripts/measure_boot_cls_matrix.mjs` against local `dist` (same flow as `library boot CLS` e2e: `load` → active panel → `document.fonts.ready` → CLS stable). Tables below are generated from `cls-before.json` and `cls-after.json` via `scripts/generate_boot_cls_readme.mjs`. Budget **0.1**.

## What changed

- **Header (769–900px):** fixed `12.5rem` (200px) `.header-search` slot + `#search` min-height so Pagefind mount does not wrap the action row or shrink the library grid (`chrome.css`, pre-fix baseline `862e9d8`).
- **Library strip + footer:** `--library-strip-min-height` and `--library-page-footer-min-height` on `.library-strip` / `.library-page-footer` so strip and footer block size is stable before paint (no `max-height` reserve on `.library-frame` — that double-counted and left a ~52px gap under the footer).
- **Boot reading context:** note-panel boot reserve + `syncReadingContext()` before `is-booting` is cleared; `is-reading-context-visible` only shows the bar when it is not `[hidden]`.
- **Systems / credentials tablet pane (~56px):** layout-shift sources pointed at the index row snapping from `0.38fr/0.62fr` and a wrong SSR-first panel before hash boot — not the reading-context bar (it stays `display:none` on those routes). Fix: all panels SSR-hidden, per-panel `yzLibraryRevealPanel`, critical inline `38dvh` stacked grid, prioritize deep-link panels in DOM order (`SYS-03`, `google-cloud`).
- **Notes tablet `.library-panels` (~36px):** reading-context slot reserved from first paint via `data-library-boot=detail` + `data-index-default=collapsed` (before the hash panel is parsed); `NOTE-2026-005` moved first in the panel list for earlier reveal.

Playwright gate (`library boot CLS`): deep links @ **375**, **768**, **769**, **784**, **800**, **900**, **1024**, and **1280** — all **< 0.1** in `cls-after.json` (After column below is sourced only from that file).

**Layout-shift sources (median of **3** runs, dark, 769–1024px):** see `layoutShiftSourcesMedian` in `cls-after.json` (node, `previousRect`, `currentRect`, `value`).

## dark

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.004 → **0.002** | 0.030 → **0.038** | 0.029 → **0.009** | 0.029 → **0.009** | 0.028 → **0.009** | 0.010 → **0.001** | 0.008 → **0.007** | 0.009 → **0.006** |
| systems | 0.022 → **0.022** | 0.003 → **0.004** | 0.030 → **0.004** | 0.030 → **0.004** | 0.031 → **0.011** | 0.031 → **0.003** | 0.024 → **0.003** | 0.002 → **0.003** |
| credentials | 0.009 → **0.010** | 0.010 → **0.011** | 0.035 → **0.004** | 0.035 → **0.004** | 0.010 → **0.004** | 0.028 → **0.003** | 0.025 → **0.002** | 0.005 → **0.002** |

## light

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.003 → **0.001** | 0.030 → **0.038** | 0.039 → **0.009** | 0.038 → **0.009** | 0.028 → **0.009** | 0.010 → **0.001** | 0.008 → **0.007** | 0.005 → **0.008** |
| systems | 0.022 → **0.022** | 0.003 → **0.030** | 0.030 → **0.004** | 0.030 → **0.004** | 0.031 → **0.011** | 0.031 → **0.003** | 0.003 → **0.003** | 0.002 → **0.003** |
| credentials | 0.010 → **0.010** | 0.011 → **0.010** | 0.035 → **0.004** | 0.035 → **0.004** | 0.010 → **0.004** | 0.028 → **0.002** | 0.025 → **0.003** | 0.005 → **0.005** |

## Layout-shift sources (median, dark)

### notes

**769px** — `unknown` Δy=0px (value 0.0115); `button.library-reading-context-section` Δy=0px (value 0.0115); `p.note-dek` Δy=-36px (value 0.0110); `p.note-byline.meta` Δy=631px (value 0.0110)

**784px** — `footer.library-page-footer.library-card` Δy=-5px (value 0.0087); `footer.library-strip` Δy=-5px (value 0.0087); `div.header-actions` Δy=0px (value 0.0087)

**800px** — `p.note-dek` Δy=-36px (value 0.0207); `p.note-byline.meta` Δy=631px (value 0.0207); `footer.library-page-footer.library-card` Δy=-5px (value 0.0087); `footer.library-strip` Δy=-5px (value 0.0087)

**900px** — `footer.library-page-footer.library-card` Δy=-5px (value 0.0077); `footer.library-strip` Δy=-5px (value 0.0077); `div.header-actions` Δy=0px (value 0.0077)

**1024px** — `footer.library-page-footer.library-card` Δy=-5px (value 0.0068); `footer.library-strip` Δy=-5px (value 0.0068); `div.header-actions` Δy=0px (value 0.0068)

### systems

**769px** — `div.header-actions` Δy=0px (value 0.0029); `unknown` Δy=0px (value 0.0029); `a.external` Δy=0px (value 0.0029); `footer.library-page-footer.library-card` Δy=-5px (value 0.0010)

**784px** — `unknown` Δy=0px (value 0.0029); `div.header-actions` Δy=0px (value 0.0029); `a.external` Δy=0px (value 0.0029); `footer.library-page-footer.library-card` Δy=-5px (value 0.0010)

**800px** — `li` Δy=-26px (value 0.0105); `li.library-index-group.library-index-group--depth-0` Δy=-26px (value 0.0105); `unknown` Δy=0px (value 0.0105); `div.header-actions` Δy=0px (value 0.0105)

**900px** — `unknown` Δy=0px (value 0.0026); `div.header-actions` Δy=0px (value 0.0026); `p.record-domains` Δy=635px (value 0.0026); `a.external` Δy=0px (value 0.0026)

**1024px** — `unknown` Δy=0px (value 0.0021); `div.header-actions` Δy=0px (value 0.0021); `a.external` Δy=0px (value 0.0021); `footer.library-page-footer.library-card` Δy=-5px (value 0.0008)

### credentials

**769px** — `p.links.credential-card-links` Δy=303px (value 0.0041); `div.header-actions` Δy=0px (value 0.0029); `unknown` Δy=0px (value 0.0029); `a.external` Δy=0px (value 0.0029)

**784px** — `unknown` Δy=0px (value 0.0029); `div.header-actions` Δy=0px (value 0.0029); `a.external` Δy=0px (value 0.0029); `footer.library-page-footer.library-card` Δy=-5px (value 0.0010)

**800px** — `p.meta.credential-card-meta` Δy=-24px (value 0.0059); `unknown` Δy=0px (value 0.0059); `div.header-actions` Δy=0px (value 0.0059); `p.links.credential-card-links` Δy=291px (value 0.0059)

**900px** — `unknown` Δy=0px (value 0.0024); `div.header-actions` Δy=0px (value 0.0024); `a.external` Δy=0px (value 0.0024); `footer.library-page-footer.library-card` Δy=-5px (value 0.0009)

**1024px** — `unknown` Δy=0px (value 0.0021); `div.header-actions` Δy=0px (value 0.0021); `a.external` Δy=0px (value 0.0021); `footer.library-page-footer.library-card` Δy=-5px (value 0.0008)

## Screenshots @ 784px (`/systems/#SYS-03`)

Header: `before-header-784-*.png` → `after-header-784-*.png`. Viewport: `before-systems-784-*.png` → `after-systems-784-*.png`.
