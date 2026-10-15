# Design system

Visual contract for yzouyang-site. Implementation: [`src/styles/`](../src/styles/) (assembled to `dist/styles.css`). Builder / IA / embeds: [site-builder.md](site-builder.md).

## Source of truth

The Figma file https://www.figma.com/design/xr2asASU4M8amldS2Lm0hQ is the source of truth for tokens, text styles, components and page rules. This document mirrors it, and src/styles/tokens.css implements it. The committed copy agents and CI read is [`docs/figma/variables.json`](figma/variables.json) (last pulled **2026-10-15 14:05 SGT**; refresh when Figma changes — see [How the Figma source of truth reaches the repo](#how-the-figma-source-of-truth-reaches-the-repo)).

**Review on change.** Any PR that changes `tokens.css`, a component class in Layer C, a breakpoint or a page rule must (i) match the Figma snapshot and a Figma variable, style or component (or link the Figma change), and (ii) update this doc and `docs/figma/variables.json` in the same PR when design values change. If the code is right and Figma lags, file it for figma bro and record it under [Known Figma gaps](#known-figma-gaps) rather than diverging silently. A drift review runs whenever the snapshot, Figma or `tokens.css` changes.

## How the Figma source of truth reaches the repo

Figma remains the authoritative design file; **`docs/figma/variables.json`** is the repo’s machine-readable copy for automation. Someone with Figma access (figma bro or the Site Critic lane) refreshes that snapshot whenever variables or text styles change in the file.

**Cursor agents and CI cannot call the Figma MCP** and must never guess values from memory. They work only from `docs/figma/variables.json`, this document, and `tokens.css`.

A PR that changes design tokens, text styles, or other values covered by the snapshot **without** updating `docs/figma/variables.json` must call that out explicitly in the PR body so reviewers can reconcile before merge.

The **14:05 SGT** export changelog inside `variables.json` still says GitHub issue **#33**; that pull was **#34** (code-wins pass). Do not hand-edit `variables.json` — fix the issue number on the next verbatim re-export from `inbox/figma-vars-full.json`.

**Governing sentence:** Design the site like a carefully maintained personal systems library: warm, cinematic, and catalogued — a scholar-engineer’s archive of systems, notes, and experiments, not a boardroom slide, a cyberpunk demo, or a steampunk toy.

**Style direction:** Warm walnut/brass archive with Swiss grid discipline. Mood = **scholar-engineer systems library**, not boardroom deck, SaaS template, or novelty AI chrome. Optimize for **credibility, catalogue scanability, and proof discipline** — one cinematic Entrance moment; everything else quieter.

---

## Layer A — Brand tokens

**Positioning:** Platform leader for governed, cost-aware enterprise systems. Platform, governance, FinOps, multi-cloud, and agentic AI appear as **disciplined capability signals**, not product theatre. Do not use vague “Specialist” or claim CTO/CDAO.

**Palette:** Dual theme, same brand. **Dark** (default) is warm ink/walnut; **light** is tobacco-tinged parchment (`#e8dfd0` range — not cream `#f4f0e8`). **One** dull brass accent (`#c49a5a`), used sparingly (≤10% of surface). Railway green lives in **hairlines** (`--line-*`), not large fills. Avoid generic blue-purple AI palettes.

**Atmosphere:** Home Entrance uses a **token-atmosphere** block (no photo still required). Optional stills may live in `assets/atmosphere/` but are not wired into the current Home. **One** ambient glow layer maximum (`--glow` amber pool); solid `--bg-deep` under gradients. No particles, neon, glassmorphism, terminal motifs, gradient text, or steampunk tropes.

### Semantic tokens (`:root` / `[data-theme]`)

Default is **dark** (`data-theme="dark"` on `<html>`). If `localStorage` key `yz-theme` is empty, follow `prefers-color-scheme`. A blocking head script sets `data-theme` before CSS paint (FOUC-safe). Honor `prefers-reduced-motion`: theme changes are instant; no per-section rise on Home.

#### Dark (ink / walnut / brass)

| Token | Role | Approx value |
|---|---|---|
| `--bg-deep` | Page fill / sticky header base | `#0a0b0a` |
| `--bg-mid` | Secondary surface | `#1c1612` |
| `--bg-elevated` | Lifted surface | `#2a2118` |
| `--text-strong` | Emphasized text | `#f5efe6` |
| `--text-default` / `--ink` | Primary text | `#efe6d8` |
| `--text-muted` / `--muted` | Secondary text | `#b0a090` |
| `--text-faint` | Tertiary / chrome hints (AA on `--bg-deep` / `--bg-elevated`) | `#9a8e7c` |
| `--accent` | Rules / TOC underline | `#c49a5a` |
| `--accent-text` | Accent-colored text | `#c49a5a` |
| `--accent-link` | Body links (dark) | `#c49a5a` |
| `--accent-hover` | Link / accent hover | `#dbb06e` |
| `--accent-active` | Pressed accent | `#a88448` |
| `--focus-ring` | Focus outline | `#c49a5a` |
| `--rail-green` | Hairline green (same RGB as `--line-*`) | `#4a5c4e` |
| `--line-strong` / `--line-soft` | Railway-green hairlines | `color-mix` of `#4a5c4e` at 28% / 14% |
| `--success` | Positive status | `#6a9a7a` |
| `--warning` | Caution status | `#c4a35a` |
| `--danger` | Destructive status | `#c47a6a` |
| `--glow` | Amber pool on the body wash | `rgb(212 163 92 / 12%)` |
| `--bg-gradient-mid` | Body gradient stop | `#15110e` |
| `--bg-gradient-end` | Body gradient end | `#0a0b0a` |
| `--photo-ink` | Atmosphere ink | `#e8dfd0` |
| `--note-image-bg` | Neutral mat behind figures | `#fefefe` |

#### Light (tobacco paper — AA-hardened)

Gold (`--accent`) is **decorative only** on light: CTA border, rules, TOC underline. **Focus uses `--focus-ring`**: dark `#c49a5a`, light `#6b4f10`; 2px solid, 2px offset; ≥3:1 on every surface. Body links use `--accent-link` (`#6b4f10`, hover `#5c450e`). `--text-faint` is chrome/meta only — never body copy. No pure `#FFFFFF` page fill.

| Token | Role | Approx value |
|---|---|---|
| `--bg-deep` | Page fill | `#e8dfd0` |
| `--bg-mid` | Secondary surface | `#ddd2c0` |
| `--bg-elevated` | Lifted surface | `#f5efe4` |
| `--text-strong` | Emphasized text | `#171414` |
| `--text-default` / `--ink` | Primary text | `#2a2724` |
| `--text-muted` / `--muted` | Secondary text | `#5c5548` |
| `--text-faint` | Chrome/meta only (AA on `--bg-deep`) | `#5c5548` |
| `--accent` | Rules | `#c49a5a` |
| `--accent-text` | Accent-colored text | `#6b4f10` |
| `--accent-link` | Body links | `#6b4f10` |
| `--accent-hover` | Link hover | `#5c450e` |
| `--accent-active` | Pressed accent | `#6b4f10` |
| `--focus-ring` | Focus outline | `#6b4f10` |
| `--success` | Positive status | `#3d6b4d` |
| `--warning` | Caution status | `#8a6a2a` |
| `--danger` | Destructive status | `#9a4a3a` |
| `--glow` | Light glow on the Entrance and body wash; matches Figma `color/glow` (`#c49a5a29`, 16%) | `rgb(196 154 90 / 16%)` |
| `--bg-gradient-mid` | Body gradient stop | `#e2d8c8` |
| `--bg-gradient-end` | Body gradient end | `#ddd2c0` |
| `--photo-ink` | Atmosphere ink | `#e8dfd0` |
| `--note-image-bg` | Neutral mat behind figures | `#fefefe` |

#### Surfaces and status (dark | light)

Figma writes some alphas as 8-digit hex. `tokens.css` stores the same tokens as `rgb()` percentages (`#ffffff08` is alpha 8/255, which the stylesheet rounds to 3%; `#ffffff0f` to 6%; `#1c16120a` to 4%; `#1c161212` to 7%).

| Token | Dark | Light |
|---|---|---|
| `--bg-panel` | `#ffffff08` | `#1c16120a` |
| `--bg-hover` | `#ffffff0f` | `#1c161212` |
| `--header-bg` | `#0a0b0a` at 96% | `#e8dfd0` at 94% |
| `--search-surface` | `#0a0b0a` at 94% | `#f5efe4` at 96% |
| `--accent-text` | `#c49a5a` | `#6b4f10` |
| `--accent-soft` | `#c49a5a` at 18% | `#c49a5a` at 22% |
| `--accent-active` | `#a88448` | `#6b4f10` |
| `--success` | `#6a9a7a` | `#3d6b4d` |
| `--warning` | `#c4a35a` | `#8a6a2a` |
| `--danger` | `#c47a6a` | `#9a4a3a` |
| `--bg-gradient-mid` | `#15110e` | `#e2d8c8` |
| `--bg-gradient-end` | `#0a0b0a` | `#ddd2c0` |
| `--note-image-bg` | `#fefefe` | `#fefefe` |
| `--photo-scrim` | `#0a0b0a` at 72% | `#0a0b0a` at 55% |
| `--photo-chip` | `#1c1612` at 88% | `#1c1612` at 88% |
| `--photo-ink` | `#e8dfd0` | `#e8dfd0` |

#### CTA tokens

| Token | Dark | Light |
|---|---|---|
| `--accent-cta-border` | `color-mix(in srgb, var(--accent) 55%, var(--line-strong))` | `color-mix(in srgb, var(--accent) 40%, var(--accent-text))`, 3.62:1 |
| `--accent-cta-bg` | 8% brass (`color-mix(in srgb, var(--accent) 8%, transparent)`) | same 8% |
| `--accent-cta-bg-hover` | 10% brass | same 10% |

The Home primary (`.entrance-action--primary`) is an outlined primary with an 8% brass fill: 40px tall (`--space-10`), `radius-md`, weight 600.

Shared (both themes): `--font-display` Crimson Pro; `--font-body` Source Sans 3; `--max` `68rem`; `--max-longform` `80rem`; `--frame-max` aliases `--max-longform` (Home hero, header, and featured grid share this frame); `--text-proof` fluid 17–19px (17px at 1280, 19px at 1440); `--header-offset` `4.75rem` (~76px scroll/anchor offset — not the header’s painted height; see [Header](#header)); `--gutter: clamp(1.25rem, 5vw, 1.5rem)`.

**Reading tokens (Notes only):** `--note-read-max` `34rem` (prose measure); `--note-read-lead` `1.72`; `--text-dropcap` (fluid first-letter size); `--note-image-bg` (neutral mat behind inline figures / covers). Notes prose italics use the real Crimson Pro italic.

`html` / `body` set `background-color: var(--bg-deep)`. Optional reading-size preference: `html[data-reading-size="large"|"xlarge"]` bumps global body line-height (`base.css`). Theme control: `.theme-toggle` (`aria-pressed`, visible Light/Dark label at ≥48rem; icon-only with an accessible name below 48rem, where reading size moves into the Menu; focus ring uses `--focus-ring`).

### Type scale

Fixed steps for UI/meta text; fluid `--text-display-*` for headings (see `tokens.css`). Display serif (**Crimson Pro**) is reserved for the wordmark, Entrance `h1`, section titles, `.home-practice-title`, and **Notes panel titles** — not dense catalogue list rows or beat grids.

| Step | Token | Computed size (scale 1) |
|---|---|---|
| xs | `--text-xs` | 0.8125rem |
| sm | `--text-sm` | 0.875rem |
| base | `--text-base` | 1rem |
| md | `--text-md` | 1.1875rem |
| lg | `--text-lg` | 1.25rem |
| xl | `--text-xl` | 1.375rem |
| proof | `--text-proof` | fluid 17–19px (17px at 1280, 19px at 1440) |

| Fluid step | Token | Clamp (× `--text-scale`) |
|---|---|---|
| Hero | `--text-display-hero` | 2.75rem → 7.5vw → 4.75rem |
| Display 1 | `--text-display-1` | 1.9rem → 3.6vw → 2.5rem |
| Display 2 | `--text-display-2` | 1.35rem → 2.6vw → 1.7rem |
| Display 3 | `--text-display-3` | 1.2rem → 2.3vw → 1.45rem |
| Display 4 | `--text-display-4` | 1.1rem → 2.3vw → 1.4rem |

At `width >= 1280px`, `--text-scale` is `1.0625`. At `width >= 1440px`, `--text-scale` is `1.0833`. Reading-size `large` / `xlarge` set the scale to 1.25 / 1.5 and scale `--text-proof` with them.

Figma text styles (28) mapped to Layer C classes. Token columns reference `tokens.css` and [`docs/figma/variables.json`](figma/variables.json) `textStyles`. **Size / token** and **Weight / tracking** columns describe **shipped CSS** on the listed selectors (not a live Figma diff).

| Figma style | Class | Face | Size / token | Weight / tracking |
|---|---|---|---|---|
| Display/Hero | `main.page .entrance h1` | Crimson Pro | `--text-display-hero` | 600 |
| Display/H1 | `.library-panel--note .library-panel-title` | Crimson Pro | `--text-display-1` | 600, −2.5% |
| Display/H2 | `.library-panel-header .library-panel-title`, `.home-plate h2` | Crimson Pro | `--text-display-3` | 600, lh 1.2, 0% |
| Display/H2 Page | `.not-found h1` (404 heading) | Crimson Pro | `--text-display-2` | 600, lh 1.1, −1% |
| Display/Brand | `.brand` | Crimson Pro | `--text-xl` | 600, −2% |
| Display/Record Title | `.home-record-title` | Crimson Pro | `--text-md` | 600 |
| Display/Practice Title | `.home-practice-title` | Crimson Pro | `--text-sm` | 600 |
| Display/Dropcap | `.note-body.prose .note-dropcap` | Crimson Pro | `--text-dropcap` | 600 |
| Heading/H3 | `main.page h3` | Source Sans 3 | `--text-lg` | 600 |
| Label/Caps | `.record-id` | Source Sans 3 | `--text-xs` | 600, 8%, caps |
| Label/Xs Caps | `.library-strip-label`, `.related-paths-label` | Source Sans 3 | `--text-xs` | 400, 6%, caps |
| Label/Xs Group Caps | `.library-index-group--depth-0 > .library-index-group-label` | Source Sans 3 | `--text-xs` | 600, 8%, caps, lh 1.35 |
| Label/Xs Group | `.library-index-group--depth-1 > .library-index-group-label` | Source Sans 3 | `--text-xs` | 600, 2% |
| Label/Xs Group Light | `.library-index-group--depth-2 > .library-index-group-label` | Source Sans 3 | `--text-xs` | 400, 2% |
| Body/Base | `body` | Source Sans 3 | `--text-base` | 400 |
| Body/Large | `.entrance .lede` | Source Sans 3 | `--text-md` | 400, lh 155% |
| Body/Large Hero | `.home-snap-proposition .lede` | Source Sans 3 | `--text-md` | 400, lh 150% at ≥900px (`home.css`) — **computed font-size ~20.19px at 1280** while Figma **text-md** pins **19px** (token fluidity); note only, no CSS change |
| Body/Large Dek | `.library-panel--note .note-dek` | Source Sans 3 | `--text-lg` | 400, lh 145% — **matches shipped note dek sizing; not a visual change** |
| Body/Proof | `.entrance-proof` | Source Sans 3 | `--text-proof` | 400 |
| Body/Small | `.site-nav a` | Source Sans 3 | `--text-sm` | 400 |
| Body/Small Strong | `.library-index-text` | Source Sans 3 | `--text-sm` | 600 |
| Body/Prose | `.note-body.prose` | Crimson Pro | `--text-md` | 400, lh 172% |
| Body/Blockquote | `.note-body.prose .note-blockquote p` | Crimson Pro italic | `--text-lg` | 400, lh `var(--lh-blockquote)` |
| Meta/Small | `.credential-card-meta` | Source Sans 3 | `--text-sm` | 400 |
| Meta/Xs | `.library-index-meta` | Source Sans 3 | `--text-xs` | 400 |
| Meta/Record Domains | `.record-domains` | Source Sans 3 | `--text-xs` | 400 — **`var(--text-muted)` (B1)** — dark **~7.0:1** on `--bg-mid` panel; light **~4.7–4.9:1** on panel |
| Meta/Map Node Label | `.map-node-label` | Source Sans 3 | `--text-xs` | 400 |
| UI/Control | `.theme-toggle` | Source Sans 3 | `--text-sm` | 400 (label); icon-only below 48rem |

Doc-only aliases retired: Wordmark → Display/Brand.

| Use | Face |
|---|---|
| Display/Hero, Display/H1–H2, Display/H2 Page, Display/Brand, Display/Record Title, Display/Practice Title | Crimson Pro (serif) |
| **Notes essay body** (`.note-body.prose` only) | Crimson Pro (serif) at `--text-md` — see [Reading mode](#reading-mode-notes-only) |
| Label, body, meta, and UI styles in the table | Source Sans 3 (sans) |

Catalogue IDs (`SYS-01`, `NOTE-2026-014`) use Source Sans 3 with slightly tracked caps — not monospace.

Publication dates in the Notes index and byline use **full calendar dates** when `writing.yaml` stores `YYYY-MM-DD` (display: `22 Dec 2025`). Month-only `YYYY-MM` remains a fallback (`Dec 2025`).

### Spacing and radius

4px base (`1rem` = 16px). `--space-hairline` and `--space-tight` sit off that grid.

| Token | Value |
|---|---|
| `--space-hairline` | 0.15rem |
| `--space-tight` | 0.35rem |
| `--space-1` | 0.25rem |
| `--space-2` | 0.5rem |
| `--space-3` | 0.75rem |
| `--space-4` | 1rem |
| `--space-5` | 1.25rem |
| `--space-6` | 1.5rem |
| `--space-7` | 1.75rem |
| `--space-8` | 2rem |
| `--space-9` | 2.25rem |
| `--space-10` | 2.5rem (40px) |
| `--space-11` | 3rem |
| `--space-12` | 4rem |
| `--library-strip-min-height` | 3.2rem — catalogue strip (`.library-strip`) min block size before paint |
| `--library-page-footer-min-height` | 4.9rem — library shell footer (`.library-page-footer`) min block size before paint |
| `--library-index-control-size` | 2rem — pin/hide/rail index controls (`.library-index-control`) |
| `--radius-sm` | 0.15rem |
| `--radius-md` | 0.2rem |
| `--radius-lg` | 0.25rem |

### Breakpoints

`@media` queries cannot read custom properties without a build step, so these are documented constants. `--header-control-height` is `calc((var(--space-2) * 2) + (1.2 * var(--text-sm)))`, set on `.header-actions`. Desktop nav links, the theme toggle, the reading-size toggle, and the menu summary use that height. Below 48rem the theme toggle leaves that height and becomes a `--space-10` square.

| Width | Applies to |
|---|---|
| `640px` | Credentials featured grid becomes 2 columns (`library.css`, `width >= 640px`). Long-form `.case-beats` stacks at `width <= 640px` (`longform.css`). |
| `40rem` | Entrance actions stack below 40rem. Featured records are 2 columns from 40rem (`home.css`). |
| `<= 48rem` | Compact header: icon search, icon theme, reading size inside Menu (`chrome.css`). Library master-detail: index stacks above the pane (`library.css`). Systems split stacks (`home.css`). |
| `> 48rem` | Library index can collapse to a rail instead of hiding (`library.css`). |
| `64rem` / `1024px` (`--bp-lg`) | Between `> 48rem` and `<= 64rem` the library shell uses a stacked index row above the pane on narrow desktop/tablet. `tokens.css` still names this constant for the record impact grid; `home.css` has no `1024px` query. |
| `72rem` | Featured records are 4 columns (`home.css`). |
| `800px` (`--bp-sm`) | Entrance copy padding stack (`home.css`). Career-journey stack (`career-journey.css`). |
| `900px` (`--bp-md`) | Primary nav collapses to Menu (`chrome.css`). Practice grid is 2 columns from 900px (`home.css`). Long-form sidebar stacks (`longform.css`). Search drawer spans the header (`search.css`). |
| `1280px` | `--text-scale: 1.0625` |
| `1440px` | `--text-scale: 1.0833` |

---

## Layer B — Content hierarchy (library order)

Home reads as a personal systems library (four beats (no scroll-snap; no per-section rise)):

1. **Proposition** — token atmosphere; **identity line** (name on its own line, then current role · employer, sentence case, sans, readable size — not a caps eyebrow); thesis `h1`; practitioner lede (≥ body size); **one proof line** directly under the lede (see *Proof on Home*); one outlined primary action (“Explore selected systems”) and a text link (“Read the notes”). No scroll-snap and no scroll arrow. Hero, header, and featured grid share `--frame-max`.
2. **Featured records** — grid of curated SYS / NOTE summaries (1 column, 2 from `40rem`, 4 from `72rem`; no 3-column step). One card per enterprise record — SYS-01 / SYS-02 / SYS-03 — with the employer named on a muted line under the record id — plus one writing row. The grid does not scroll or clip horizontally.
3. **Operating principle** — editorial philosophy block
4. **Practice areas** — capability grid + split context / platform meta strips

Inner pages:

| Route | Page title | Notes |
|---|---|---|
| `/systems/` | Systems | Library shell; Pagefind “Search catalogue” |
| `/notes/` | Notes | Library shell; **Reading mode** for PUBLIC essays (masthead + cover + `.note-body.prose`); index collapsed by default |
| `/credentials/` | Professional record | Library shell + VERIFY |
| `/about/`, `/contact/`, `/career-journey/` | *(redirect)* | Home |
| `/portfolio/`, `/work/`, `/systems/catalogue/` | *(redirect)* | `/systems/` |
| `/perspectives/`, `/blog/` | *(redirect)* | `/notes/` |

**Credibility order:** thesis → documented systems → writing → experiments → professional record. Quantified proof lives on SYS records (sourced from the public CV via `site.outcomes` / `enterprise_copy`). **Home carries at most one quiet proof line**; there is no metrics hero and no outcome strip.

### Proof on Home

**Proof on Home (one line).** The Entrance carries **exactly one** proof sentence, placed directly under the lede and above the CTAs. Body sans at `--text-proof` (fluid 17–19px: 17px at 1280, 19px at 1440), in full `--text-default`, with the railway-green left rule (`--line-strong`, not brass). It must:
- cite only facts present in `data/site.json` or `data/export_public.json` (record the JSON paths in `home_proof_line.sources`);
- name the employer/context and keep a baseline for every number (e.g. "8 to 4 weeks", not "50%");
- stay one sentence: not bolded, not split into tiles, not animated, not repeated elsewhere on Home, and not promoted into a metrics hero.

**Still banned:** boardroom outcome strip; metric counters or big-number tiles; a metrics hero; more than one proof line; unit-less percentages.

### Library boot layout reserves

While `#library-split` carries `.is-booting`, CSS reserves block size so late-parsed shell chrome does not shrink the pane (DOM order: lede → frame → split → strip → page footer; no flex `order` hacks).

| Mechanism | Routes | Purpose |
|---|---|---|
| `.library-frame` **grid** row `var(--library-strip-min-height)` | Systems, Notes, Credentials (when `.library-strip` exists) | Strip row reserved before `.library-strip` parses |
| `.library-shell::after` placeholder | All library routes until `.library-page-footer` parses | Footer slot = `--library-page-footer-min-height` + `--space-3` |
| `.library-reading-context[hidden]` flex reserve | **Notes** only (`data-library-route="notes"`, collapsed index / hash boot) | Reading-context bar slot while `[hidden]` during boot (target for remaining ~36px panel shift when the bar appears above `.library-panels`) |

Tokens: `--library-strip-min-height`, `--library-page-footer-min-height`, `--library-index-control-size`. Route hook: `data-library-route` on `<main class="library-route">` (`notes` \| `systems` \| `credentials`) — not `aria-label`.

### Library scanning (Catalogue mode)

**Catalogue mode** applies to **Systems**, **Credentials**, and the **Home** featured-record grid: scan, compare, and jump — not sustained reading. Typography stays sans-first; panels use the full library pane width (no `--note-read-max` cap).

- Split-pane catalogue: index list left (desktop) or full-width index (mobile overview); panel body right
- **Notes:** index **collapsed by default** (unpinned overlay); **Systems / Credentials:** index **expanded by default** (pinned). Hover peek when unpinned; **Escape** dismisses overlay without changing pin mode; rail expand control exposes `aria-expanded`
- **Sticky index headers** on Notes: `.library-index-group-label` tiers (category → series → part) stay pinned while scrolling the index — not in-article body headings
- **Reading context bar** (`.library-reading-context`): when the Notes index is collapsed, a compact title · section strip above the panel body orients the reader; hidden when the index is pinned open
- Case studies on `/systems/`: problem → role → decision → outcome → evidence at ~⅓ typical density (`.case-beats` grid)
- **Related Paths** on a record are semantic siblings from the system map — not repeated global nav (Credentials · Notes)
- **Library strip** footer switches collections (Systems · Notes · Credentials) — browsing chrome, not related evidence
- Writing index: publication rows with catalogue metadata (`NOTE-*`, formatted date in `.library-index-meta`), not blog card grid
- Header Pagefind + in-panel headings — no sticky long-form TOC on library routes (Notes use **in-index** in-article links via `data-inarticle-toc`, not a body TOC rail)
- **Index rail controls (769–1024px):** collapsed-index **TOC rail** pin/expand buttons are **32×32px** (`--library-index-control-size`, 2rem). Earlier shipped chrome used **20×32px** controls; the second rail icon sits **12px** lower in the stacked layout — intentional, documented only (no CSS revert).

### Reading mode (Notes only)

**Reading mode** applies only to **PUBLIC writing** on `/notes/` (`.library-panel--note`). Do **not** port this stack to Systems, Credentials, or Home — those routes stay in Catalogue mode.

| Element | Pattern | Implementation |
|---|---|---|
| Measure | Narrow centered column | `--note-read-max` on panel header + body |
| Masthead | Category kicker → display title → optional dek → byline | `.note-kicker`, `.library-panel-title`, `.note-dek`, `.note-byline` |
| Byline | Full date · read time · series | `_format_note_date()`; NOTE id in `.visually-hidden` only |
| Cover | Featured image above body | `.note-cover` from export `images[]` with `role: cover` |
| Prose | Essay typography | `.note-body.prose`: `--text-md`, `--note-read-lead`, first-paragraph drop cap |
| Blockquotes | Editorial pull quotes | `.note-blockquote` (imported `> ` lines); brass rule + italic serif |
| Code | Wrapped blocks, line gutters | `.note-code` / `.note-code-line`; `pre-wrap` + `overflow-wrap: anywhere` — no horizontal scroll per line |
| Figures | Centered stack + caption | `.note-figure` / `.note-figure-caption`; `--note-image-bg` mat |
| In-index TOC | H3/H4 jump links in sidebar | `data-inarticle-toc` on panel; `.library-index-inarticle-*` when index open |

Builder: `scripts/build.py` (`build_perspectives`, `_markdown_to_html`). Content SoT: `personal-content` `writing.yaml` + markdown bodies; full dates via `--sync-dates` on import.

---

## Layer C — Component rules

| Class / pattern | Use |
|---|---|
| `.entrance` / `.entrance-atmosphere` | Token atmosphere behind thesis |
| `.entrance-identity` | Home identity: name stacked above role · employer at every width |
| `.entrance-proof` | single proof line under the lede, above Entrance CTAs |
| `.home-record-strip` / `.home-featured-records` | Featured SYS / NOTE grid (1 / 2 / 4 columns; no horizontal scroll) |
| `.home-practice-grid` | Practice-area capability cards |
| `.home-context-strip` / `.home-platform-strip` | Location / platform proof meta |
| `.library-card` / `.site-footer` / `.library-page-footer` | Footer: location · focus · mailto · social |
| `.site-nav` | **Systems · Notes · Credentials** |
| `.library-shell` | Split-pane catalogue on Systems / Notes / Credentials |
| `data-library-route` on `<main class="library-route">` | Route hook for CSS (`notes`, `systems`, `credentials`) — do not use `aria-label` for styling |
| `.library-index-list` / `.library-index-trigger` | Catalogue index (buttons; opens panel) |
| `.library-index-group` / `.library-index-group-label` | Sticky tiered headers in Notes index (category / series) |
| `.library-index-inarticle-*` | In-note heading jump links in sidebar when index open |
| `.library-reading-context` | Notes panel chrome when index collapsed (title · section) |
| `.library-panel` / `.library-back` | Record body + mobile return to index |
| `.library-panel--note` | Notes reading-mode panel (measure cap + masthead stack) |
| `.note-cover` / `.note-body.prose` | Cover hero + markdown essay body (Notes only) |
| `.note-blockquote` / `.note-figure` / `.note-code-*` | Prose block patterns inside Notes |
| `.case-beats` | Systems record beat grid (Catalogue mode — sans, scan density) |
| `#search` + Pagefind | Catalogue search in the sticky header |

**Motion:** Map-node and record hover/focus only. **No** per-section `rise` on Home. Honor `prefers-reduced-motion` on library panel transitions. Durations use three tokens only: `--dur-fast` 150ms, `--dur-base` 240ms, `--dur-slow` 400ms.

External nav links use `.external` (↗ via CSS `::after`).

### Figma component ↔ class

Shared focus rule: `:focus-visible` draws a 2px `--focus-ring` with a 2px offset (`base.css`). Dark ring `#c49a5a`, light ring `#6b4f10`.

| Figma component | Class |
|---|---|
| Button | `.entrance-action--primary` (outlined primary; text links stay `.entrance-action--secondary`) |
| Text Link | `.entrance-action--secondary`, body `a` |
| Entrance Action (Primary) | `.entrance-action--primary` |
| Nav Link | `.site-nav a` |
| Nav Link Active | `.site-nav a[aria-current="page"]`, `.site-nav a[aria-current="location"]` |
| Theme Toggle | `.theme-toggle` |
| Reading-size Toggle | `.reading-size-toggle` |
| Menu Button | `.nav-menu > summary` |
| Embed Frame | `.embed-frame` |
| Record Card | `.home-record-row` (Home); Systems record body uses `.library-panel` |
| Index Trigger | `.library-index-trigger` |
| Entrance Atmosphere (optional) | `.entrance-atmosphere` / `.entrance-atmosphere--tokens` |

#### Header

[`variables.json`](figma/variables.json) carries tokens only — no component tree. Header variants are mapped here (markup from `scripts/build.py` `layout()`; breakpoints in `chrome.css`). Figma **Header** component set **`3:2`**.

**Scroll offset:** `--header-offset` (`4.75rem`) is used for `scroll-padding-top`, TOC spy, and in-view `scroll-margin-top` — it is **not** the sticky header’s rendered block height.

**Figma padding:** Header vertical padding in the **Header** set (`3:2`) uses **literal px/rem values**, not `--space-*` tokens, so frames hit the measured heights below.

| Variant | Width | Controls (Figma order, left → right) | Rendered height |
|---|---|---|---|
| **Compact** | **375–768px** (`<= 48rem`) | **Brand** · **40px Search** · **40px Theme** · **Menu** | **64px** — node `3:25` |
| **Mid** | **769–900px** (`48rem < width <= 900px`) | **Brand** · **200px Search** · **Clear** (empty field: `opacity: 0`; visible once text is typed) · **Text size** · **Theme** · **Menu** | **59.19px** — node `21:16` |
| **Narrow desktop** | **901–1024px** | **Brand** · **Systems** · **Notes** · **Credentials** · **200px Search** · **Clear** (empty field: `opacity: 0`; visible once text is typed) · **Text size** · **Theme** | **59.19px** — node `32:292` |
| **Desktop** | **1025–1279px** (shipped chrome: **`width > 1024px`**; no dedicated frame in set `3:2`) | **Brand** · **Systems** · **Notes** · **Credentials** · **200px Search** · **Clear** (empty field: `opacity: 0`; visible once text is typed) · **Text size** · **Theme** — no **Menu** | **59.19px** — shipped chrome (Figma header variants confirm **Clear** behavior) |
| **Desktop** | **≥1280px** (Figma frame at **1280** — node `3:3`; shipped chrome breakpoint **`width > 1024px`**) | **Brand** · **Systems** · **Notes** · **Credentials** · **200px Search** · **Clear** (empty field: `opacity: 0`; visible once text is typed) · **Text size** · **Theme** — no **Menu** | **61.39px** — node `3:3` |

**Clear (Figma + shipped):** Header variants that include **Clear** model it **hidden (`opacity: 0`)** while the Pagefind search field is empty and **visible once text is typed** (shipped: `.pagefind-ui__search-clear` inside `.header-search`).

**Shipped chrome (for gap checks):** `.site-header` markup from `layout()` — **Brand** · `.site-nav-desktop` (Systems · Notes · Credentials when `> 900px`) · `.header-search` / `#search` (Pagefind **Clear** = `.pagefind-ui__search-clear` inside the search control) · `.reading-size-toggle` · `.theme-toggle` · `.nav-menu` (when `<= 900px`; **Text size** duplicate lives in the Menu panel at `<= 48rem` only).

`.proof-strip` and `.connect-card` are not part of this contract. Nothing in `scripts/build.py`, `src/*.js`, or the page templates emits them.

---

## Known Figma gaps

**Snapshot ↔ `tokens.css` (automated sync, pull 2026-10-15 20:45 SGT):** Variables with a `web` mapping in [`variables.json`](figma/variables.json) match the CSS implementation (including `color/record-domains` → `var(--text-muted)`). All **28** `textStyles` match the typography table and `test_design_system_sync.py`. Figma export fields vs shipped selectors are checked by `collect_figma_export_css_mismatches` (line-height includes inherited `body` rhythm when a selector omits it).

**Open (not enforced by sync; Yingzhao decides):**

- **`main.page h2` (Display/H2 — open hybrid).** Shipped **`--text-display-2`** and **−1%** tracking (`components.css`) match **Display/H2 Page** size/tracking; **`var(--lh-heading)` (1.2)** matches **Display/H2** line height. Not a single Figma text-style row — **Yingzhao** to confirm mapping. Sync skips **font-size** only for this selector (`TEXT_STYLE_OPEN_CSS_ITEMS`); **Display/H2 Page size/tracking with Display/H2 line height**.
- **`.home-plate h2` (Display/H2 — open mapping).** Shipped `.home-plate h2` inherits **body line-height (1.6)** while Figma **Display/H2** is **120%**. **Yingzhao** to align or retire the selector. Listed in the typography table; automated export checks omit this selector (no `skip_properties` / no line-height skip).
- **`home.css` `.note-dek` (line 485).** A second, global `.note-dek` rule sets **line-height 1.55**; Figma models note deks only via **Body/Large Dek** on `.library-panel--note .note-dek` (`library.css`, **145%** / `1.45`). No CSS change until decided.
- **Display/H1 line-height.** Figma **Display/H1** uses **Auto** line height; shipped `.library-panel--note .library-panel-title` sets **`var(--lh-heading)` (1.2)**. No CSS change until decided.
- **Header · Clear placement (Mid / desktop).** Figma lists **Clear** as its own control between **Search** and **Text size**; shipped chrome nests Clear inside the Pagefind **Search** slot (same row, not a separate DOM sibling).
- **Header · Compact Text size.** Figma **Compact** (`3:25`) omits **Text size** from the header row; shipped chrome keeps **Text size** inside the **Menu** panel only (`<= 48rem`) — matches intent, different surface than a header control.
- **C9.** `rgb(43 84 64 / 35%)` on `.system-map-svg circle` has no token. It stays as a literal, called out in `home.css`, until Figma names it.
- **Scrim ink.** `rgb(6 5 3 / …)` on the Entrance scrim has no token. The drift checker allow-lists it as an overlay.
- **Vignette alphas.** The Entrance vignette uses `rgb(10 11 10 / 90%)` in dark and `rgb(232 223 208 / 82%)` in light, not `--photo-scrim` (72% / 55%).
- **Unstyled in Figma textStyles (doc-only).** Entrance identity (`.entrance-name`, `.entrance-role`), featured kicker (`.home-section-label` / `.home-record-kind`), fallback index (`.current-index .index-entry`), monospace code (`.note-code`), and **`.library-index-label`** (400 / `0.08em` caps on the catalogue index header — not Label/Xs Caps or Label/Xs Group Caps).

---

## Maintainability tooling (Phase 3)

| Gate | Command |
|---|---|
| Static contracts (CI pre-build) | `uv run python scripts/lint.py` · `check_token_drift.py` · `test_design_system_sync.py` · `test_check_token_drift.py` |
| Stylelint | `npm run lint:css` |
| Dist contract tests | `uv run python scripts/test_site_build.py` (requires `dist/` after build) |
| axe-core | `npm run test:a11y` |
| Playwright | `npm run test:e2e` |

Pre-commit: husky + lint-staged on staged `src/styles/*.css`.

---

## Do / don’t

**Do**

- Warm ink/walnut/brass palette; catalogue language (`SYS-`, `NOTE-`, `LAB-`)
- One bold Entrance moment; quieter archive sections below
- Keep primary nav short: **Systems · Notes · Credentials**
- Brass/gold ≤10%; railway green in hairlines only
- Derive proof from `site.json` / export only
- Identity line on Home: name on its own line, then role · employer (from `person.job_title` / `person.employer`).
- One proof line on Home, under the lede and above the CTAs, sourced (see *Proof on Home*).
- Use **Reading mode** typography only on `/notes/` essay bodies; keep **Catalogue mode** on Systems / Credentials / Home strips
- Store and display **full publication dates** (`YYYY-MM-DD`) for writing records

**Don’t**

- Boardroom outcome strip, metric counters, or metrics hero on Home; more than one proof line; portrait chip on Home
- Steampunk tropes (gears, rockets, chalkboard props); retired scroll-home “Workshop” crop
- Fraunces/Sora, cream `#f4f0e8`, or SaaS card kits
- Tracked ALL-CAPS eyebrows on every heading; decorative numbered `01 02 03`
- Invent metrics; cert wall on Home; visitor-facing phone
- Migration / Phase notes in footer
- Port Notes drop caps, narrow measure, or serif prose to SYS panels, credential cards, or Home featured rows
- Horizontal per-line code scroll in Notes; blog-card grids for the writing index
