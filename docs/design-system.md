# Design system

Visual contract for yzouyang-site. Implementation: [`src/styles/`](../src/styles/) (assembled to `dist/styles.css`). Builder / IA / embeds: [site-builder.md](site-builder.md).

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
| `--text-strong` | Emphasized text | `#f2ebe0` |
| `--text-default` / `--ink` | Primary text | `#e6dcc8` |
| `--text-muted` / `--muted` | Secondary text | `#a89a88` |
| `--text-faint` | Tertiary / chrome hints (AA on `--bg-deep` / `--bg-elevated`) | `#968a78` |
| `--accent` | CTA border / rules / TOC underline | `#c49a5a` |
| `--accent-link` | Body links (dark) | `#c49a5a` |
| `--accent-hover` | Link / accent hover | `#dbb06e` |
| `--line-strong` / `--line-soft` | Railway-green hairlines | `rgb(74 92 78 / …)` |
| `--glow` | Single amber pool (one layer max) | `rgb(212 163 92 / 12%)` |
| `--photo-scrim` / `--photo-chip` / `--photo-ink` | Entrance / atmosphere overlays | ink/walnut tuned |

#### Light (tobacco paper — AA-hardened)

Gold (`--accent`) is **decorative only** on light: CTA border, rules, TOC underline. Body links use `--accent-link` (`#6b4f10`, hover `#5c450e`). `--text-faint` is chrome/meta only — never body copy. No pure `#FFFFFF` page fill.

| Token | Role | Approx value |
|---|---|---|
| `--bg-deep` | Page fill | `#e8dfd0` |
| `--bg-mid` | Secondary surface | `#ddd2c0` |
| `--bg-elevated` | Lifted surface | `#f5efe4` |
| `--text-strong` | Emphasized text | `#171414` |
| `--text-default` / `--ink` | Primary text | `#2a2724` |
| `--text-muted` / `--muted` | Secondary text | `#5c5548` |
| `--text-faint` | Chrome/meta only (AA on `--bg-deep`) | `#5c5548` |
| `--accent` | Rules / CTA border | `#c49a5a` |
| `--accent-link` | Body links | `#6b4f10` |
| `--glow` | Soft amber wash | `rgb(212 163 92 / 10%)` |

Shared (both themes): `--font-display` Crimson Pro; `--font-body` Source Sans 3; `--max` `68rem`; `--max-longform` `80rem`; `--header-offset` `4.75rem`.

`html` / `body` set `background-color: var(--bg-deep)`. Theme control: `.theme-toggle` (`aria-pressed`, visible Light/Dark label, brass focus ring).

### Type scale

Fixed steps for UI/meta text; fluid `--text-display-*` for headings (see `tokens.css`). Display serif (**Crimson Pro**) is reserved for wordmark, Entrance `h1`, and section titles — not dense list rows.

| Use | Face |
|---|---|
| `.brand`, `.entrance h1`, section `h2` on Home | Crimson Pro (serif) |
| Body, nav, TOC, chips, record IDs, search, buttons | Source Sans 3 (sans) |

Catalogue IDs (`SYS-01`, `NOTE-2026-014`) use Source Sans 3 with slightly tracked caps — not monospace.

### Spacing, radius, breakpoints

Same scales as before (`--space-*`, `--radius-*`). Breakpoints:

| Reference | Value | Applies to |
|---|---|---|
| `--bp-sm` | `800px` | Entrance layout stack (`home.css`) |
| `--bp-md` | `900px` | Primary nav collapse (`chrome.css`); legacy long-form `.page-with-toc` sidebar stack (`longform.css`) |
| `--bp-lg` | `1024px` (`64rem`) | Record impact grid (`home.css`); library shell stacks index above panel (`library.css`) |

---

## Layer B — Content hierarchy (library order)

Home reads as a personal systems library:

1. **Entrance** — token atmosphere; thesis `h1`; practitioner lede; `current_index`; location/platforms proof strip
2. **Catalogue entries** — `home-entry-grid` to Systems / Notes / Credentials
3. **Competencies** — editorial list, not a system map or workshop

Inner pages:

| Route | Page title | Notes |
|---|---|---|
| `/systems/` | Systems | Library shell; Pagefind “Search catalogue” |
| `/notes/` | Notes | Library shell; PUBLIC writing corpus (C2b) |
| `/credentials/` | Professional record | Library shell + VERIFY |
| `/about/`, `/contact/`, `/career-journey/` | *(redirect)* | Home |
| `/portfolio/`, `/work/`, `/systems/catalogue/` | *(redirect)* | `/systems/` |
| `/perspectives/`, `/blog/` | *(redirect)* | `/notes/` |

**Credibility order:** thesis → documented systems → writing → experiments → professional record.

### Library scanning

- Split-pane catalogue: index list left (desktop) or full-width index (mobile overview); panel body right
- Case studies on `/systems/`: problem → role → decision → outcome → evidence at ~⅓ typical density
- Writing: publication rows with catalogue metadata (`NOTE-*`), not blog card grid
- Header Pagefind + in-panel headings — no sticky long-form TOC on library routes

---

## Layer C — Component rules

| Class / pattern | Use |
|---|---|
| `.entrance` / `.entrance-atmosphere` | Token atmosphere behind thesis |
| `.current-index` | Systems / notes highlight lines |
| `.home-entry-grid` | Catalogue doors to Systems / Notes / Credentials |
| `.proof-strip` | Singapore + ≤4 platforms |
| `.library-card` / `.site-footer` / `.library-page-footer` | Footer: location · focus · mailto · social |
| `.site-nav` | **Systems · Notes · Credentials** |
| `.library-shell` | Split-pane catalogue on Systems / Notes / Credentials |
| `.library-index-list` / `.library-index-trigger` | Catalogue index (buttons; opens panel) |
| `.library-panel` / `.library-back` | Record body + mobile return to index |
| `#search` + Pagefind | Catalogue search in the sticky header |

**Motion:** Map-node and record hover/focus only. **No** per-section `rise` on Home. Honor `prefers-reduced-motion` on library panel transitions.

External nav links use `.external` (↗ via CSS `::after`).

---

## Maintainability tooling (Phase 3)

| Gate | Command |
|---|---|
| Stylelint | `npm run lint:css` |
| Token drift | `python scripts/check_token_drift.py` |
| Contract tests | `uv run python scripts/test_site_build.py` |
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

**Don’t**

- Boardroom outcome strip in hero; portrait chip on Home
- Steampunk tropes (gears, rockets, chalkboard props); retired scroll-home “Workshop” crop
- Fraunces/Sora, cream `#f4f0e8`, or SaaS card kits
- Tracked ALL-CAPS eyebrows on every heading; decorative numbered `01 02 03`
- Invent metrics; cert wall on Home; visitor-facing phone
- Migration / Phase notes in footer
