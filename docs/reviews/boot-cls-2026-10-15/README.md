# Boot CLS — library deep links

Measured with `scripts/measure_boot_cls_matrix.mjs` against local `dist` (same flow as `library boot CLS` e2e: `load` → active panel → `document.fonts.ready` → CLS stable). Tables below are generated from `cls-before.json` and `cls-after.json` via `scripts/generate_boot_cls_readme.mjs`. Budget **0.1**.

## What changed

- **Header (769–900px):** fixed `12.5rem` (200px) `.header-search` slot + `#search` min-height so Pagefind mount does not wrap the action row or shrink the library grid (`chrome.css`, pre-fix baseline `862e9d8`).
- **Library strip + footer:** `--library-strip-min-height` and `--library-page-footer-min-height` on `.library-strip` / `.library-page-footer` so strip and footer block size is stable before paint (no `max-height` reserve on `.library-frame` — that double-counted and left a ~52px gap under the footer).
- **Boot reading context:** note-panel boot reserve + `syncReadingContext()` before `is-booting` is cleared; `is-reading-context-visible` only shows the bar when it is not `[hidden]`.
- **Systems / credentials tablet pane (~56px):** layout-shift sources pointed at the index row snapping from `0.38fr/0.62fr` and a wrong SSR-first panel before hash boot — not the reading-context bar (it stays `display:none` on those routes). Fix: SSR-visible first index panel for no-JS, `html.js` hides extras, per-panel `yzLibraryRevealPanel`, pre-paint hash panel switch in `THEME_BOOT_SCRIPT` + `LIBRARY_HASH_BOOT_SCRIPT` (no `38dvh` grid override).
- **Notes (~36px):** reading-context bar without reserved slot on collapsed index; late index collapse. Fix: single notes-only `.library-reading-context[hidden]` reserve during boot, synchronous `is-index-collapsed` on wide hash boot, SSR expanded index (`html:not(.js)`).

Playwright gate (`library boot CLS`): deep links @ **375**, **768**, **769**, **784**, **800**, **900**, **1024**, and **1280** — all **< 0.1** in `cls-after.json` (After column below is sourced only from that file).

**Layout-shift sources (median of **3** runs, dark, 769–1024px):** see `layoutShiftSourcesMedian` and `layoutShiftJumpCounts` in `cls-after.json`.

## dark

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.004 → **0.004** | 0.030 → **0.038** | 0.029 → **0.003** | 0.029 → **0.038** | 0.028 → **0.038** | 0.010 → **0.015** | 0.008 → **0.002** | 0.009 → **0.009** |
| systems | 0.022 → **0.051** | 0.003 → **0.036** | 0.030 → **0.030** | 0.030 → **0.030** | 0.031 → **0.006** | 0.031 → **0.008** | 0.024 → **0.024** | 0.002 → **0.003** |
| credentials | 0.009 → **0.042** | 0.010 → **0.010** | 0.035 → **0.035** | 0.035 → **0.035** | 0.010 → **0.010** | 0.028 → **0.028** | 0.025 → **0.025** | 0.005 → **0.002** |

## light

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.003 → **0.004** | 0.030 → **0.001** | 0.039 → **0.039** | 0.038 → **0.038** | 0.028 → **0.038** | 0.010 → **0.002** | 0.008 → **0.012** | 0.005 → **0.001** |
| systems | 0.022 → **0.051** | 0.003 → **0.036** | 0.030 → **0.030** | 0.030 → **0.030** | 0.031 → **0.032** | 0.031 → **0.031** | 0.003 → **0.004** | 0.002 → **0.003** |
| credentials | 0.010 → **0.042** | 0.011 → **0.045** | 0.035 → **0.035** | 0.035 → **0.035** | 0.010 → **0.038** | 0.028 → **0.028** | 0.025 → **0.025** | 0.005 → **0.002** |

## Layout-shift sources (median, dark)

### notes

**769px** — `.library-panel-body` Δy=-65px (value 0.0387); `p.note-dek` Δy=-36px (value 0.0387); `p.note-byline.meta` Δy=-65px (value 0.0387); `div.header-actions` Δy=0px (value 0.0015)

**784px** — `.library-panel-body` Δy=-65px (value 0.0382); `p.note-dek` Δy=-36px (value 0.0382); `footer.library-page-footer.library-card` Δy=-5px (value 0.0382); `p.note-byline.meta` Δy=-65px (value 0.0382)

**800px** — `.library-panel-body` Δy=-65px (value 0.0377); `p.note-dek` Δy=-36px (value 0.0377); `p.note-byline.meta` Δy=-65px (value 0.0377); `div.header-actions` Δy=0px (value 0.0015)

**900px** — `.library-panel-body` Δy=-29px (value 0.0149); `footer.library-page-footer.library-card` Δy=-5px (value 0.0149); `footer.library-strip` Δy=-5px (value 0.0149); `p.note-byline.meta` Δy=-29px (value 0.0149)

**1024px** — `div.header-actions` Δy=0px (value 0.0011); `.library-index-control` Δy=-43px (value 0.0011); `footer.library-page-footer.library-card` Δy=-5px (value 0.0008); `footer.library-strip` Δy=-5px (value 0.0008)

### systems

**769px** — `div.library-pane` Δy=-54px (value 0.0254); `div.header-actions` Δy=0px (value 0.0035); `unknown` Δy=0px (value 0.0035); `a.external` Δy=0px (value 0.0035)

**784px** — `div.library-pane` Δy=-54px (value 0.0254); `unknown` Δy=0px (value 0.0035); `div.header-actions` Δy=0px (value 0.0035); `a.external` Δy=0px (value 0.0035)

**800px** — `div.library-pane` Δy=-54px (value 0.0255); `li` Δy=-26px (value 0.0053); `unknown` Δy=0px (value 0.0053); `div.header-actions` Δy=0px (value 0.0053)

**900px** — `div.library-pane` Δy=-54px (value 0.0228); `p.record-methods.meta` Δy=-26px (value 0.0073); `p.related-paths.meta` Δy=-26px (value 0.0073); `p.record-domains` Δy=-26px (value 0.0073)

**1024px** — `div.library-pane` Δy=-54px (value 0.0202); `unknown` Δy=0px (value 0.0030); `div.header-actions` Δy=0px (value 0.0030); `a.external` Δy=0px (value 0.0030)

### credentials

**769px** — `div.library-pane` Δy=-56px (value 0.0284); `div.header-actions` Δy=0px (value 0.0062); `unknown` Δy=0px (value 0.0062); `article.credential-card` Δy=-20px (value 0.0062)

**784px** — `div.library-pane` Δy=-56px (value 0.0284); `unknown` Δy=0px (value 0.0062); `div.header-actions` Δy=0px (value 0.0062); `article.credential-card` Δy=-20px (value 0.0062)

**800px** — `div.library-pane` Δy=-54px (value 0.0277); `article.credential-card` Δy=-44px (value 0.0090); `p.meta.credential-card-meta` Δy=-24px (value 0.0090); `p.links.credential-card-links` Δy=-44px (value 0.0090)

**900px** — `div.library-pane` Δy=-54px (value 0.0248); `unknown` Δy=0px (value 0.0024); `div.header-actions` Δy=0px (value 0.0024); `a.external` Δy=0px (value 0.0024)

**1024px** — `div.library-pane` Δy=-54px (value 0.0220); `unknown` Δy=0px (value 0.0021); `div.header-actions` Δy=0px (value 0.0021); `a.external` Δy=0px (value 0.0021)

## Screenshots @ 784px (`/systems/#SYS-03`)

Header: `before-header-784-*.png` → `after-header-784-*.png`. Viewport: `before-systems-784-*.png` → `after-systems-784-*.png`.
