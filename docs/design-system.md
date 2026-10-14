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
| `--accent` | Rules / CTA border | `#c49a5a` |
| `--accent-link` | Body links | `#6b4f10` |
| `--glow` | Soft amber wash | `rgb(212 163 92 / 10%)` |

Shared (both themes): `--font-display` Crimson Pro; `--font-body` Source Sans 3; `--max` `68rem`; `--max-longform` `80rem`; `--header-offset` `4.75rem`; `--gutter: clamp(1.25rem, 5vw, 1.5rem)`.

**Reading tokens (Notes only):** `--note-read-max` `34rem` (prose measure); `--note-read-lead` `1.72`; `--text-dropcap` (fluid first-letter size); `--note-image-bg` (neutral mat behind inline figures / covers). Notes prose italics use the real Crimson Pro italic.

`html` / `body` set `background-color: var(--bg-deep)`. Optional reading-size preference: `html[data-reading-size="large"|"xlarge"]` bumps global body line-height (`base.css`). Theme control: `.theme-toggle` (`aria-pressed`, visible Light/Dark label at ≥48rem; icon-only with an accessible name below 48rem, where reading size moves into the Menu; focus ring uses `--focus-ring`).

### Type scale

Fixed steps for UI/meta text; fluid `--text-display-*` for headings (see `tokens.css`). Display serif (**Crimson Pro**) is reserved for wordmark, Entrance `h1`, section titles, and **Notes panel titles** — not dense catalogue list rows or beat grids.

| Use | Face |
|---|---|
| `.brand`, `.entrance h1`, section `h2` on Home | Crimson Pro (serif) |
| `.library-panel--note .library-panel-title`, in-note section headings (`.note-section-heading--major`) | Crimson Pro (serif) |
| **Notes essay body** (`.note-body.prose` only) | Crimson Pro (serif) at `--text-md` — see [Reading mode](#reading-mode-notes-only) |
| Body, nav, TOC, chips, record IDs, search, buttons, SYS beat copy | Source Sans 3 (sans) |

Catalogue IDs (`SYS-01`, `NOTE-2026-014`) use Source Sans 3 with slightly tracked caps — not monospace.

Publication dates in the Notes index and byline use **full calendar dates** when `writing.yaml` stores `YYYY-MM-DD` (display: `22 Dec 2025`). Month-only `YYYY-MM` remains a fallback (`Dec 2025`).

### Spacing, radius, breakpoints

Same scales as before (`--space-*`, `--radius-*`). Breakpoints:

| Reference | Value | Applies to |
|---|---|---|
| `--bp-sm` | `800px` | Entrance layout stack (`home.css`) |
| `--bp-md` | `900px` | Primary nav collapse (`chrome.css`); legacy long-form `.page-with-toc` sidebar stack (`longform.css`) |
| `--bp-lg` | `1024px` (`64rem`) | Record impact grid (`home.css`); library shell stacks index above panel (`library.css`) |

---

## Layer B — Content hierarchy (library order)

Home reads as a personal systems library (four beats (no scroll-snap; no per-section rise)):

1. **Proposition** — token atmosphere; **identity line** (name on its own line, then current role · employer, sentence case, sans, readable size — not a caps eyebrow); thesis `h1`; practitioner lede (≥ body size); primary CTAs; **one quiet proof line** (see *Proof on Home*); a scroll arrow with no repeated section name. No scroll-snap; featured records peek below on laptop widths.
2. **Featured records** — horizontal strip of curated SYS / NOTE summaries (one card per enterprise record — SYS-01 / SYS-02 / SYS-03 — with the employer named on a muted line under the record id — plus one writing row)
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

**Proof on Home (one line, quiet).** The Entrance may carry **exactly one** proof sentence, placed after the CTAs, set in body sans at `--text-sm`, `--text-muted`, with an optional railway-green hairline rule (not brass). It must:
- cite only facts present in `data/site.json` or `data/export_public.json` (record the JSON paths in `home_proof_line.sources`);
- name the employer/context and keep a baseline for every number (e.g. "8 to 4 weeks", not "50%");
- never be enlarged, bolded, split into tiles, animated, or repeated elsewhere on Home.

**Still banned:** boardroom outcome strip; metric counters or big-number tiles; a metrics hero; more than one proof line; unit-less percentages.

### Library scanning (Catalogue mode)

**Catalogue mode** applies to **Systems**, **Credentials**, and the **Home** featured-record strip: scan, compare, and jump — not sustained reading. Typography stays sans-first; panels use the full library pane width (no `--note-read-max` cap).

- Split-pane catalogue: index list left (desktop) or full-width index (mobile overview); panel body right
- **Notes:** index **collapsed by default** (unpinned overlay); **Systems / Credentials:** index **expanded by default** (pinned). Hover peek when unpinned; **Escape** dismisses overlay without changing pin mode; rail expand control exposes `aria-expanded`
- **Sticky index headers** on Notes: `.library-index-group-label` tiers (category → series → part) stay pinned while scrolling the index — not in-article body headings
- **Reading context bar** (`.library-reading-context`): when the Notes index is collapsed, a compact title · section strip above the panel body orients the reader; hidden when the index is pinned open
- Case studies on `/systems/`: problem → role → decision → outcome → evidence at ~⅓ typical density (`.case-beats` grid)
- **Related Paths** on a record are semantic siblings from the system map — not repeated global nav (Credentials · Notes)
- **Library strip** footer switches collections (Systems · Notes · Credentials) — browsing chrome, not related evidence
- Writing index: publication rows with catalogue metadata (`NOTE-*`, formatted date in `.library-index-meta`), not blog card grid
- Header Pagefind + in-panel headings — no sticky long-form TOC on library routes (Notes use **in-index** in-article links via `data-inarticle-toc`, not a body TOC rail)

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
| `.entrance-proof` | single quiet proof line under Entrance CTAs |
| `.home-record-strip` / `.home-featured-records` | Featured SYS / NOTE rows (horizontal snap strip) |
| `.home-practice-grid` | Practice-area capability cards |
| `.home-context-strip` / `.home-platform-strip` | Location / platform proof meta |
| `.proof-strip` | Singapore + ≤4 platforms (legacy class; context strip on current Home) |
| `.library-card` / `.site-footer` / `.library-page-footer` | Footer: location · focus · mailto · social |
| `.site-nav` | **Systems · Notes · Credentials** |
| `.library-shell` | Split-pane catalogue on Systems / Notes / Credentials |
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
- Identity line on Home: name on its own line, then role · employer (from `person.job_title` / `person.employer`).
- One quiet proof line on Home, sourced (see *Proof on Home*).
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
