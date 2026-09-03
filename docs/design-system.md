# Design system

Visual contract for yzouyang-site. Implementation: [`src/styles/`](../src/styles/) (assembled to `dist/styles.css`). Builder / IA / embeds: [site-builder.md](site-builder.md).

**Governing sentence:** Design the site like a senior enterprise architect’s public briefing document, with editorial polish and technical precision.

**Style direction:** Calm enterprise editorial — dark, restrained, slightly atmospheric, structured and businesslike. Mood = **boardroom-meets-technical-journal**, not futurist demo lab, AI-builder novelty, or startup theater. Optimize for **authority, scanability, and proof density** — not animation or decorative UI.

---

## Layer A — Brand tokens

**Positioning:** Senior Data and AI Transformation Leader. Platform, governance, FinOps, multi-cloud, and agentic AI appear as **disciplined capability signals**, not product theater.

**Palette:** Deep charcoal with a restrained green undertone (boardroom, not matrix/terminal); **one** muted gold accent; neutral text. Avoid generic blue-purple AI palettes. Gold-on-dark is allowed only with discipline (enterprise rigor, not boutique luxury). Large empty surfaces use `--bg-elevated` charcoal, not a saturated forest fill.

**Atmosphere:** **One** ambient glow layer maximum; solid `--bg-deep` under gradients. No particles, neon, glassmorphism, terminal motifs, gradient text, or oversized AI imagery.

### Semantic tokens (`:root`)

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
| `--accent` | Links / specialist line / primary CTA border | `#d4a35c` |
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
| `--font-display` | Hero title + brand wordmark only | Fraunces |
| `--font-body` | Everything else | Sora |
| `--max` | Content measure (Home; header/footer on non-TOC routes) | `68rem` |
| `--max-longform` | Content measure (Portfolio, Credentials, About dossier column) **and** matching header/footer on `.page-with-toc` routes | `80rem` |
| `--header-offset` | Sticky header height; used for `scroll-padding-top` and sidebar `max-height` math | `4.75rem` |

`html` / `body` set `background-color: var(--bg-deep)`. Gradients use `background-image` only.

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

1. **Headline** — name → role → specialist line
2. **Quantified proof** — 2–3 outcomes from `site.outcomes`
3. **Platform scope + location** — proof strip (≤4 platforms; **no cert wall / vanity counters on Home**)
4. **Selected systems / work** — Home `.selected-systems` editorial `.item-list` rows (enterprise cases) plus `/portfolio/` case rows
5. **Writing / speaking** — publications-style lists (About Selected writing; external Blog/Medium/LinkedIn under nav **Elsewhere**)
6. **Credentials** — issuer-grouped; curated on `/credentials/`
7. **Contact** — Home `#contact`; sticky header control; not primary nav

### Long-form scanning

- Narrow-to-medium measure (`--max`), **left-aligned** copy, strong section rhythm
- Prefer editorial rows, compact lists, proof/outcome strips — **cards sparingly**
- Metadata order: title → org/issuer → date → links
- Case studies: **business outcome → architecture scope → tools** (tools last; description stands in for outcome when export has no separate field)
- Writing/speaking: publications page density, not blog card grid
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
| `.btn` / `.btn-primary` | **One** primary accent CTA (Contact); other actions understated `.btn` |
| `.header-contact` | Sticky jump to `/#contact` |
| `.cta-row` | Home button group |
| `.selected-systems` | Home editorial case rows between CTAs and `#contact` (not cards) |
| `.site-nav` / `.nav-menu` / `.nav-elsewhere` | Primary dossier links; Blog/Medium/LinkedIn under Elsewhere (desktop disclosure / mobile label) |
| `.page-toc` / `.page-toc-sidebar` / `.page-toc-sub` | On-this-page anchors; sticky sidebar on **all** long pages (About, Portfolio, Credentials) via `.page-with-toc`; nested subcategory links |
| `.section-fold` | Collapsible long-form sections (default open); summary = section title |
| `.item-list` | Portfolio / credentials / contact rows (editorial, not cards) |
| `.issuer-group` | Credentials vendor subgroups |
| `.writing-list` | Publications rows (title / venue·date / external link) |
| `.embed-wrap` / `.embed-fallback` / `.embed-frame` | Visual surfaces only — embed **policy** in site-builder |
| `.contact-section` | Home contact block |
| `.site-footer` | © + mailto + social |
| `#search` + Pagefind vars | Dark panel search on portfolio/credentials |

**Sticky header:** `.site-header-wrap` — opaque ≥94% `--bg-deep`; blur additive only.

**Long-form TOC (design-system rule):** Every multi-section dossier page (About, Portfolio, Credentials) uses `.page-with-toc` with a sticky `.page-toc-sidebar`. Nested `.page-toc-sub` lists expose subcategories (e.g. portfolio child sections, credential issuers). Major sections use `.section-fold` (`<details open>`) so readers can collapse dense blocks without losing the sidebar map.

**Long-form alignment axes:** Dossier pages share **at most three text left edges**. This is a composition rule, not extra chrome.

1. **TOC top-level** — sidebar label + parent links (sidebar chrome). Nested `.page-toc-sub` links indent **once inside the sidebar only**; they must not create a fourth body axis.
2. **Main primary text** — page `h1` = `.page-lede` = Pagefind outer box = `.section-fold` summary text = fold body `h3`. The disclosure chevron (`summary::before`) is `position: absolute` in a `--space-5` (1.25rem) gutter so it does not invent an axis. Summary and `.section-fold-body` share that left padding; do not add a further `h3` indent.
3. **List hang** — bullets only (`.item-list ul` / `.competency-list` `padding-left: var(--space-5)`). One hang from the primary axis.

**Shell measure:** On `.page-with-toc` routes, `.site-header` and `.site-footer` use `--max-longform` with the same `--space-6` horizontal padding as `main.page`, so brand / Contact lock to the dossier column. Home keeps `--max`. At ≤`--bp-md` (900px) the Menu control is the rightmost header item; Contact matching main-right is a **≥1280** check (tolerance ±2px).

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
- Keep primary nav short; Contact stays a sticky control

**Don’t**

- Neon glows, glassmorphism, terminal motifs, particles, gradient text, oversized AI art
- Turn the homepage into a certification wall
- Overuse serif in dense sections
- SaaS conversion button stacks (one primary CTA is enough)
- Put migration / Phase 1 changelog in footer or header
- Reintroduce Contact as a primary nav page
- Invent proof metrics — derive from export / `site.json` only
