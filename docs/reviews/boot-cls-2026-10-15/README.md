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
| notes | 0.004 → **0.001** | 0.030 → **0.001** | 0.029 → **0.001** | 0.029 → **0.001** | 0.028 → **0.038** | 0.010 → **0.001** | 0.008 → **0.012** | 0.009 → **0.001** |
| systems | 0.022 → **0.051** | 0.003 → **0.036** | 0.030 → **0.004** | 0.030 → **0.004** | 0.031 → **0.006** | 0.031 → **0.008** | 0.024 → **0.004** | 0.002 → **0.003** |
| credentials | 0.009 → **0.042** | 0.010 → **0.045** | 0.035 → **0.007** | 0.035 → **0.007** | 0.010 → **0.009** | 0.028 → **0.003** | 0.025 → **0.003** | 0.005 → **0.005** |

## light

| Route | 375 | 768 | 769 | 784 | 800 | 900 | 1024 | 1280 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| notes | 0.003 → **0.001** | 0.030 → **0.001** | 0.039 → **0.001** | 0.038 → **0.001** | 0.028 → **0.001** | 0.010 → **0.001** | 0.008 → **0.001** | 0.005 → **0.001** |
| systems | 0.022 → **0.051** | 0.003 → **0.036** | 0.030 → **0.004** | 0.030 → **0.004** | 0.031 → **0.006** | 0.031 → **0.008** | 0.003 → **0.004** | 0.002 → **0.003** |
| credentials | 0.010 → **0.042** | 0.011 → **0.045** | 0.035 → **0.007** | 0.035 → **0.007** | 0.010 → **0.010** | 0.028 → **0.003** | 0.025 → **0.003** | 0.005 → **0.005** |

## Layout-shift sources (median, dark)

### notes

**769px** — `.library-panel-body` Δy=-65px (value 0.0387); `p.note-dek` Δy=-36px (value 0.0387); `p.note-byline.meta` Δy=-65px (value 0.0387); `footer.library-page-footer.library-card` Δy=-5px (value 0.0010)

**784px** — `.library-panel-body` Δy=-65px (value 0.0382); `p.note-dek` Δy=-36px (value 0.0382); `footer.library-page-footer.library-card` Δy=-5px (value 0.0382); `p.note-byline.meta` Δy=-65px (value 0.0382)

**800px** — `p.note-dek` Δy=-36px (value 0.0255); `.library-panel-body` Δy=-65px (value 0.0181); `footer.library-page-footer.library-card` Δy=-5px (value 0.0181); `p.note-byline.meta` Δy=-65px (value 0.0181)

**900px** — `.library-panel-body` Δy=-29px (value 0.0124); `p.note-byline.meta` Δy=-29px (value 0.0124); `div.header-actions` Δy=0px (value 0.0099); `unknown` Δy=0px (value 0.0099)

**1024px** — `footer.library-page-footer.library-card` Δy=-5px (value 0.0120); `.library-panel-body` Δy=-29px (value 0.0120); `footer.library-strip` Δy=-5px (value 0.0120); `p.note-byline.meta` Δy=-29px (value 0.0120)

### systems

**769px** — `div.header-actions` Δy=0px (value 0.0035); `unknown` Δy=0px (value 0.0035); `a.external` Δy=0px (value 0.0035); `footer.library-page-footer.library-card` Δy=-5px (value 0.0010)

**784px** — `unknown` Δy=0px (value 0.0035); `div.header-actions` Δy=0px (value 0.0035); `a.external` Δy=0px (value 0.0035); `footer.library-page-footer.library-card` Δy=-5px (value 0.0010)

**800px** — `li` Δy=-26px (value 0.0053); `unknown` Δy=0px (value 0.0053); `div.header-actions` Δy=0px (value 0.0053); `a.external` Δy=0px (value 0.0053)

**900px** — `p.record-methods.meta` Δy=-26px (value 0.0073); `p.related-paths.meta` Δy=-26px (value 0.0073); `p.record-domains` Δy=-26px (value 0.0073); `unknown` Δy=0px (value 0.0073)

**1024px** — `unknown` Δy=0px (value 0.0030); `div.header-actions` Δy=0px (value 0.0030); `a.external` Δy=0px (value 0.0030); `footer.library-page-footer.library-card` Δy=-5px (value 0.0008)

### credentials

**769px** — `div.header-actions` Δy=0px (value 0.0062); `unknown` Δy=0px (value 0.0062); `article.credential-card` Δy=-20px (value 0.0062); `p.links.credential-card-links` Δy=-20px (value 0.0062)

**784px** — `unknown` Δy=0px (value 0.0062); `div.header-actions` Δy=0px (value 0.0062); `article.credential-card` Δy=-20px (value 0.0062); `p.links.credential-card-links` Δy=-20px (value 0.0062)

**800px** — `article.credential-card` Δy=-44px (value 0.0090); `p.meta.credential-card-meta` Δy=-24px (value 0.0090); `p.links.credential-card-links` Δy=-44px (value 0.0090); `unknown` Δy=0px (value 0.0090)

**900px** — `unknown` Δy=0px (value 0.0024); `div.header-actions` Δy=0px (value 0.0024); `a.external` Δy=0px (value 0.0024); `footer.library-page-footer.library-card` Δy=-5px (value 0.0009)

**1024px** — `unknown` Δy=0px (value 0.0021); `div.header-actions` Δy=0px (value 0.0021); `a.external` Δy=0px (value 0.0021); `footer.library-page-footer.library-card` Δy=-5px (value 0.0008)

## Screenshots @ 784px (`/systems/#SYS-03`)

Header: `before-header-784-*.png` → `after-header-784-*.png`. Viewport: `before-systems-784-*.png` → `after-systems-784-*.png`.
