# Design system

Visual contract for yzouyang-site. Implementation: [`src/styles/`](../src/styles/) (assembled to `dist/styles.css`). Builder / IA / embeds: [site-builder.md](site-builder.md).

**Governing sentence:** Design the site like a senior enterprise architect’s public briefing document, with editorial polish and technical precision.

**Style direction:** Calm enterprise editorial — dark, restrained, slightly atmospheric, structured and businesslike. Mood = **boardroom-meets-technical-journal**, not futurist demo lab, AI-builder novelty, or startup theater. Optimize for **authority, scanability, and proof density** — not animation or decorative UI.

---

## Layer A — Brand tokens

**Positioning:** Platform leader for governed, cost-aware enterprise systems. Platform, governance, FinOps, multi-cloud, and agentic AI appear as **disciplined capability signals**, not product theatre. Do not use vague “Specialist” or claim CTO/CDAO.

**Palette:** Dual theme, same brand. **Dark** (default) is deep charcoal with a restrained green undertone; **light** is paper/ink parchment. **One** muted gold accent, used sparingly (≤10% of the surface) — CTA borders, hairline rules, TOC/chapter underlines. Avoid generic blue-purple AI palettes and WordPress blue. Gold-on-dark is allowed only with discipline. Large empty surfaces use `--bg-elevated`, not a saturated forest fill (dark) or pure `#FFFFFF` (light).

**Atmosphere:** **One** ambient glow layer maximum; solid `--bg-deep` under gradients. Light glow is a soft sage wash (10%) or none — not a spotlight. No particles, neon, glassmorphism, terminal motifs, gradient text, or oversized AI imagery. Light must read as the same brand, not a second product.

### Semantic tokens (`:root` / `[data-theme]`)

Default is **dark** (`data-theme="dark"` on `<html>`). If `localStorage` key `yz-theme` is empty, follow `prefers-color-scheme` (light only when that media query matches; otherwise dark). A blocking head script sets `data-theme` before CSS paint (FOUC-safe). Honor `prefers-reduced-motion`: theme changes are instant — no hue theatre.

#### Dark (Keep & Tighten — live tokens, unchanged)

| Token | Role | Approx value |
|---|---|---|
| `--bg-deep` | Page fill / sticky header base | `#0c1412` |
| `--bg-mid` | Secondary surface | `#15201c` |
| `--bg-elevated` | Slightly lifted surface | `#1a2420` |
| `--bg-panel` | TOC / search / panel fills | `rgb(255 255 255 / 3%)` |
| `--bg-hover` | Hover wash | `rgb(255 255 255 / 6%)` |
| `--text-strong` | Emphasized text | `#f2f7f3` |
| `--text-default` / `--ink` | Primary text | `#e8efe9` |
| `--text-muted` / `--muted` | Secondary text | `#9aada3` |
| `--text-faint` | Tertiary / chrome hints (AA on `--bg-deep` / `--bg-elevated`) | `#8a9c94` |
| `--accent` | Specialist line / primary CTA border / TOC underline | `#d4a35c` |
| `--accent-link` | Body links (same gold on dark) | `#d4a35c` |
| `--accent-soft` | Soft accent fill | `rgb(212 163 92 / 18%)` |
| `--accent-hover` | Link / accent hover | `#f0c27a` |
| `--accent-active` | Pressed accent | `#c4924a` |
| `--focus-ring` | `:focus-visible` outline | `rgb(212 163 92 / 65%)` |
| `--line-strong` | Stronger dividers | `rgb(232 239 233 / 22%)` |
| `--line-soft` / `--line` | Hairline borders | `rgb(232 239 233 / 12%)` |
| `--success` / `--warning` / `--danger` | Status (reserved; use sparingly) | muted green / amber / rose |
| `--glow` | Single ambient glow (one layer max) | `rgb(55 90 78 / 22%)` |
| `--bg-gradient-mid` | Body background gradient, 45% stop | `#121a17` |
| `--bg-gradient-end` | Body background gradient, 100% stop | `#0e1412` |

#### Light (paper/ink — AA-hardened parchment)

Gold (`--accent`) is **decorative only** on light: CTA border, rules, TOC underline. Body links use `--accent-link`. `--text-faint` is chrome/meta only — never body copy.

| Token | Role | Approx value |
|---|---|---|
| `--bg-deep` | Page fill / sticky header base | `#F4F0E8` |
| `--bg-mid` | Secondary / fold surface | `#EBE6DC` |
| `--bg-elevated` | Lifted surface (not `#FFFFFF`) | `#FFFBF5` |
| `--bg-panel` | TOC / panel fills | `rgb(12 20 18 / 4%)` |
| `--bg-hover` | Hover wash | `rgb(12 20 18 / 7%)` |
| `--text-strong` | Emphasized text | `#171414` |
| `--text-default` / `--ink` | Primary text | `#2A2724` |
| `--text-muted` / `--muted` | Secondary text | `#5C6B63` |
| `--text-faint` | Chrome/meta only (never body) | `#7A877F` |
| `--accent` | CTA border / rules / TOC underline | `#d4a35c` |
| `--accent-link` | Body links | `#856012` |
| `--accent-hover` / `--accent-active` | Link hover / press | `#7A5A12` |
| `--accent-soft` | Soft accent fill | `rgb(212 163 92 / 22%)` |
| `--focus-ring` | `:focus-visible` outline | `rgb(212 163 92 / 65%)` |
| `--line-strong` | Sage hairlines (stronger) | `rgb(55 90 78 / 22%)` |
| `--line-soft` / `--line` | Sage hairlines | `rgb(55 90 78 / 12%)` |
| `--glow` | Soft sage wash (not spotlight) | `rgb(55 90 78 / 10%)` |
| `--bg-gradient-mid` | Warm parchment mid stop | `#EDE8DF` |
| `--bg-gradient-end` | Warm parchment end stop | `#E8E2D8` |

Shared (both themes): `--font-display` Fraunces; `--font-body` Sora; `--max` `68rem`; `--max-longform` `80rem`; `--header-offset` `4.75rem`. Photo overlays use `--photo-scrim` / `--photo-chip` / `--photo-ink` so the portrait stays charcoal in both themes.

`html` / `body` set `background-color: var(--bg-deep)`. Gradients use `background-image` only. Theme control: `.theme-toggle` (`aria-pressed`, visible Light/Dark label, gold focus ring).

### Type scale

Fixed steps for UI/meta text (page titles, section headings, nav, meta, chips — everything that isn't a fluid display heading):

| Token | Value | Replaces (pre-Phase 1 raw sizes) |
|---|---|---|
| `--text-xs` | `0.75rem` | `0.7rem`, `0.75rem` |
| `--text-sm` | `0.85rem` | `0.8rem`, `0.85rem` |
| `--text-base` | `0.9rem` | `0.9rem` |
| `--text-md` | `1.05rem` | `1.05rem`, `1.1rem` |
| `--text-lg` | `1.2rem` | `1.1rem`–`1.2rem` |
| `--text-xl` | `1.35rem` | `1.35rem` |

Fluid display headings (viewport-responsive, not on the fixed ramp):

| Token | Value | Use |
|---|---|---|
| `--text-display-hero` | `clamp(2.6rem, 7vw, 4.6rem)` | Home hero `h1` |
| `--text-display-1` | `clamp(1.85rem, 3.5vw, 2.35rem)` | Page `h1` (About, Portfolio, Credentials) |
| `--text-display-2` | `clamp(1.3rem, 2.5vw, 1.65rem)` | Section `h2` |
| `--text-display-3` | `clamp(1.15rem, 2.2vw, 1.4rem)` | Sub-section `h3` (long-form) |
| `--text-display-4` | `clamp(1.05rem, 2.2vw, 1.35rem)` | Small fluid headings |

### Spacing scale

Base-4px rhythm (`1rem` = 16px root), plus two named exceptions for chrome-level hairline gaps that predate the grid and don't sit on it cleanly:

| Token | Value | Token | Value |
|---|---|---|---|
| `--space-hairline` | `0.15rem` | `--space-6` | `1.5rem` |
| `--space-tight` | `0.35rem` | `--space-7` | `1.75rem` |
| `--space-1` | `0.25rem` | `--space-8` | `2rem` |
| `--space-2` | `0.5rem` | `--space-9` | `2.25rem` |
| `--space-3` | `0.75rem` | `--space-10` | `2.5rem` |
| `--space-4` | `1rem` | `--space-11` | `3rem` |
| `--space-5` | `1.25rem` | `--space-12` | `4rem` |

Full raw-value → token mapping (with drift notes) for the Phase 2 migration: [token-migration-checklist.md](token-migration-checklist.md).

### Radius scale

Formalizes the 3 values already in use — no visual drift:

| Token | Value |
|---|---|
| `--radius-sm` | `0.15rem` |
| `--radius-md` | `0.2rem` |
| `--radius-lg` | `0.25rem` |

### Breakpoints

`--bp-sm` and `--bp-md` stay distinct because the hero's two-column layout and the chrome/sidebar collapse are different layout concerns that happen to sit close in width. `--bp-lg` only locks the Home outcome-strip to three columns:

| Reference | Value | Applies to |
|---|---|---|
| `--bp-sm` | `800px` | Hero two-column → stacked (`home.css`) |
| `--bp-md` | `900px` | Nav collapse (`chrome.css`) + long-form sidebar collapse (`longform.css` — converged from its pre-migration `960px`) |
| `--bp-lg` | `1024px` | Outcome-strip 3-column row (`home.css`) — keeps three metrics on one line instead of a 2+1 wrap |

These are documented constants, not live custom properties — `@media` conditions can't consume `var()` without a preprocessing step. Treat the table above as the source of truth until/unless the build adds one.

### Typography

| Use | Face |
|---|---|
| `.brand`, `.hero h1` | Fraunces (serif) |
| Page titles, section headings, body, UI, nav, meta, chips, lists, search, buttons | Sora (sans) |

No serif in dense scanning contexts (portfolio rows, writing lists, credentials, TOC, search).

---

## Layer B — Content hierarchy (dossier order)

Site reads as a senior professional dossier:

1. **Headline** — name → platform-leader proposition → lede
2. **Quantified proof** — 2–3 outcomes from `site.outcomes` (metric + system + intervention)
3. **Platform scope + location** — proof strip (≤4 platforms; **no cert wall / vanity counters on Home**)
4. **Selected systems / work** — Home `.selected-systems` editorial `.folio-deck` rows (problem → role → decision → outcome → evidence) plus `/portfolio/` (nav label **Work**)
5. **Operating themes** — four Bassem-shaped rows (cloud economics; governed data platforms; AI-enabled engineering; operational observability). Public architectures / mentoring are contribution, not corporate scale.
6. **Writing / speaking** — `/perspectives/` start-here index; About Selected writing; external Blog/Medium/LinkedIn/GitHub under nav **Elsewhere**
7. **Credentials** — issuer-grouped; curated on `/credentials/` with a VERIFY panel under the lede
8. **Contact** — Home `#contact`; primary nav item; email + elsewhere (no visitor-facing phone)

### Long-form scanning

- Narrow-to-medium measure (`--max`), **left-aligned** copy, strong section rhythm
- Prefer editorial rows, compact lists, proof/outcome strips — **cards sparingly**
- Metadata order: title → org/issuer → date → links
- Case studies: **problem → role → decision → outcome → evidence** at about one-third typical case-study density (**rows, not cards**). Tools last.
- Writing/speaking: publications page density, not blog card grid; Perspectives is a start-here index until C2b
- Search / TOC / archive chrome must feel deliberate
- Emphasize measurable outcomes and platform breadth **before** tool buzzwords

### Proof components

| Component | Rule |
|---|---|
| Outcome block (`.outcome-strip`) | Metric + short label; from `site.outcomes` only; never invent |
| Proof strip (`.proof-strip`) | Location + ≤4 platforms; no inventing counts |
| Credibility modules | Speaking / newsletter / certs / community on About or Credentials — not hero chrome |

---

## Layer C — Component rules

| Class / pattern | Use |
|---|---|
| `.brand` | Wordmark `yzouyang` (serif) |
| `.hero` / `.hero-copy` / `.hero-visual` | Name first, role, specialist line, outcomes, proof, CTAs; copy before photo on mobile |
| `.outcome-strip` | 2–3 quantified proof points |
| `.proof-strip` | Location + platforms |
| `.portrait-chip` | Role · location over photo |
| `.btn` / `.btn-primary` | **One** primary accent CTA on Home (**View selected work**); Contact is the secondary `.btn` |
| `.theme-toggle` | Accessible Light/Dark control in `.header-actions` (`aria-pressed`, visible label, gold focus ring) |
| `.cta-row` | Home button group |
| `.selected-systems` | Home editorial case rows between CTAs and operating themes (not cards) |
| `.operating-themes` / `.theme-list` | Four operating-theme rows + contribution note |
| `.case-beats` | Problem / role / decision / outcome / evidence definition list |
| `.verify-panel` | Credentials VERIFY block under the page lede |
| `.folio-deck` | List / View all default for case and credential rows; deck is progressive enhancement |
| `.site-nav` / `.nav-menu` / `.nav-elsewhere` | Work · Perspectives · About · Credentials · Contact; Blog/Medium/LinkedIn/GitHub under Elsewhere |
| `.page-toc` / `.page-toc-sidebar` / `.page-toc-sub` | On-this-page anchors; gold underline on `aria-current="location"` |
| `.section-fold` | Collapsible long-form sections (default open); summary = section title |
| `.item-list` | Portfolio / credentials / contact rows (editorial, not cards) |
| `.issuer-group` | Credentials vendor subgroups |
| `.writing-list` | Publications rows (title / venue·date / external link) |
| `.embed-wrap` / `.embed-fallback` / `.embed-frame` | Visual surfaces only — embed **policy** in site-builder |
| `.contact-section` | Home contact block |
| `.site-footer` | © + mailto + social |
| `#search` + Pagefind vars | Dark panel search on portfolio/credentials |

**Sticky header:** `.site-header-wrap` — opaque ≥94% `--header-bg`; blur additive only. Theme toggle is the rightmost compact control beside Menu at `--bp-md`.

**Long-form TOC (design-system rule):** Every multi-section dossier page (About, Portfolio, Credentials) uses `.page-with-toc` with a sticky `.page-toc-sidebar`. Nested `.page-toc-sub` lists expose subcategories (e.g. portfolio child sections, credential issuers). Major sections use `.section-fold` (`<details open>`) so readers can collapse dense blocks without losing the sidebar map.

**Long-form alignment axes:** Dossier pages share **at most three text left edges**. This is a composition rule, not extra chrome.

1. **TOC top-level** — sidebar label + parent links (sidebar chrome). Nested `.page-toc-sub` links indent **once inside the sidebar only**; they must not create a fourth body axis.
2. **Main primary text** — page `h1` = `.page-lede` = Pagefind outer box = `.section-fold` summary text = fold body `h3`. The disclosure chevron (`summary::before`) is `position: absolute` in a `--space-5` (1.25rem) gutter so it does not invent an axis. Summary and `.section-fold-body` share that left padding; do not add a further `h3` indent.
3. **List hang** — bullets only (`.item-list ul` / `.competency-list` `padding-left: var(--space-5)`). One hang from the primary axis.

**Shell measure:** On `.page-with-toc` routes, `.site-header` and `.site-footer` use `--max-longform` with the same `--space-6` horizontal padding as `main.page`, so brand / theme toggle lock to the dossier column. Home keeps `--max`. At ≤`--bp-md` (900px) the Menu control is the rightmost header item; theme toggle matching main-right is a **≥1280** check (tolerance ±2px).

**Optical top:** `.page-toc-sidebar` uses `padding-top: var(--space-1)` (one token, overriding `.page-toc`’s `--space-3`) so “ON THIS PAGE” caps optically align with the page `h1` caps at 1280. Do not add a second offset.

**Motion:** Short, minimal entrance (`rise`); honor `prefers-reduced-motion`. No novelty animation. Career Journey slide chrome is **opacity-only** (≤0.25s, no `scale()`, no `translateY` snap). Under `prefers-reduced-motion`, `.cj-slide` is `opacity: 1` / `transform: none` and every `[data-step]` is revealed — resting dim/scale must not survive `animation: none`.

External nav links use `.external` (↗ via CSS `::after`).

---

## Maintainability tooling (Phase 3)

The token system above is enforced by CI, not just convention:

| Gate | What it catches | Command | Config |
|---|---|---|---|
| Stylelint | Raw `font-size`/`border-radius`/`margin*`/`padding*`/`*gap` instead of `var(--...)` | `npm run lint:css` | `.stylelintrc.json` |
| Token drift check | Raw hex colors or un-tokenized `font-family` outside `tokens.css` | `python scripts/check_token_drift.py` | `scripts/check_token_drift.py` |
| Accessibility (axe-core) | WCAG2A/AA violations (contrast, landmarks, ARIA) on the 4 core routes | `npm run test:a11y` | `tests/e2e/a11y.spec.mjs` |
| Visual regression | Unintended layout/style drift on the 4 core routes × 2 viewports | `npm run test:visual` | `tests/e2e/visual.spec.mjs` |

All four run in `.github/workflows/ci.yml`. Visual regression is currently **non-blocking** (`continue-on-error: true`) because no baseline screenshots are committed yet — see the setup steps in `tests/e2e/visual.spec.mjs`'s header comment. Once baselines exist and are committed, remove `continue-on-error` so it becomes a real gate.

A handful of documented one-off values are intentionally exempt from the stylelint rule (e.g. `0.75em` external-link arrow markers in `chrome.css`, which are relative to their parent font-size rather than the fixed type ramp) — see `ignoreValues` in `.stylelintrc.json`.

### Pre-commit hook

A `husky` + `lint-staged` pre-commit hook runs Stylelint and the token-drift check against staged `src/styles/*.css` files before a commit is created, so a violation is caught locally instead of in CI. It activates automatically the first time you run `npm install` (the `prepare` script wires up `.husky/pre-commit`). Bypass with `git commit --no-verify` if you deliberately want CI to be the first gate.

The hook is not a substitute for CI: `stylelint-config-standard` is pinned with a caret range (`^36.0.0`), so a semver-minor release can add new rules the codebase has never been checked against — the hook only catches drift once `node_modules` reflects that new version. Treat a sudden batch of new lint errors after `npm install` as a ruleset change, not a regression in the code.

---

## Do / don’t

**Do**

- Quiet contrast, clean borders, disciplined spacing, long-page readability
- Keep solid `--bg-deep` under gradients
- Deliberate TOC, search, and metadata chrome
- Outcomes + platform breadth before tool buzzwords
- Curate platforms and writing highlights; fewer strong signals
- Keep primary nav short: **Work · Perspectives · About · Credentials · Contact**
- Keep gold at ≤10%; sage/green hairlines; chapter air on long pages

**Don’t**

- Neon glows, glassmorphism, terminal motifs, particles, gradient text, oversized AI art
- Turn the homepage into a certification wall
- Overuse serif in dense sections
- SaaS conversion button stacks (one primary CTA is enough)
- Put migration / Phase 1 changelog in footer or header
- Reintroduce a sticky header Contact that duplicates the primary nav item
- Invent proof metrics — derive from export / `site.json` only
- Use `--text-faint` for body copy on light
- Recolor light as cool grey/blue or WordPress blue
