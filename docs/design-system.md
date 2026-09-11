# Design system

Visual contract for yzouyang-site. Implementation: [`src/styles/`](../src/styles/) (assembled to `dist/styles.css`). Builder / IA / embeds: [site-builder.md](site-builder.md).

**Governing sentence:** Design the site like a carefully maintained personal systems library: warm, cinematic, and catalogued — a scholar-engineer’s archive of systems, notes, and experiments, not a boardroom slide, a cyberpunk demo, or a steampunk toy.

**Style direction:** Warm walnut/brass archive with Swiss grid discipline. Mood = **scholar-engineer systems library**, not boardroom deck, SaaS template, or novelty AI chrome. Optimize for **credibility, catalogue scanability, and proof discipline** — one cinematic Entrance moment; everything else quieter.

---

## Layer A — Brand tokens

**Positioning:** Platform leader for governed, cost-aware enterprise systems. Platform, governance, FinOps, multi-cloud, and agentic AI appear as **disciplined capability signals**, not product theatre. Do not use vague “Specialist” or claim CTO/CDAO.

**Palette:** Dual theme, same brand. **Dark** (default) is warm ink/walnut; **light** is tobacco-tinged parchment (`#e8dfd0` range — not cream `#f4f0e8`). **One** dull brass accent (`#c49a5a`), used sparingly (≤10% of surface). Railway green lives in **hairlines** (`--line-*`), not large fills. Avoid generic blue-purple AI palettes.

**Atmosphere:** Three **atmosphere stills** in `assets/atmosphere/` (Entrance LCP, Reading Room figure, Workshop figure). Figcaptions say “Atmosphere still” — never real-place names. **One** ambient glow layer maximum (`--glow` amber pool); solid `--bg-deep` under gradients. No particles, neon, glassmorphism, terminal motifs, gradient text, or steampunk tropes.

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
| `--text-faint` | Chrome/meta only | `#6e6658` |
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
| `--bp-md` | `900px` | Nav collapse + long-form sidebar collapse |
| `--bp-lg` | `1024px` | Record impact grid (`home.css`) |

---

## Layer B — Content hierarchy (library order)

Home reads as a personal systems library:

1. **Entrance** — full-bleed atmosphere still; thesis `h1`; practitioner lede; `current_index` (studying / building / writing); CTAs **View systems** + **Connect**; location/platforms proof strip (no outcome strip in hero)
2. **System map** — six domains as compact SVG; hover/focus highlights related SYS/NOTE/LAB via `data-domain`
3. **Selected systems** — `SYS-01`… records (context, domains, methods, impact on matching rows); full case beats on `/portfolio/`
4. **Reading room** — featured note + catalogue rows; shelf atmosphere figure
5. **Workshop** — curated `LAB-0n` rows; cropped desk figure (no chalkboard tropes)
6. **Connect** — Home `#contact` bookmark; primary nav **Connect** → `/contact/`

Inner pages (routes unchanged; labels archival):

| Route | Page title | Notes |
|---|---|---|
| `/portfolio/` | Systems | Pagefind label: “Search the catalogue” |
| `/perspectives/` | Notes | Start-here index until C2b |
| `/about/` | Profile | Portrait lives here |
| `/credentials/` | Professional record | VERIFY panel |
| `/contact/` | Connect | Email + Elsewhere |
| `/career-journey/` | *(inherit tokens only)* | Do not restage deck |

**Credibility order:** thesis → documented systems → writing → experiments → professional record.

### Long-form scanning

- Left-aligned copy, strong section rhythm; editorial rows over identical cards
- Case studies on `/portfolio/`: problem → role → decision → outcome → evidence at ~⅓ typical density
- Writing: publication rows with catalogue metadata, not blog card grid
- Search / TOC chrome must feel deliberate (`In this record` on long pages)

---

## Layer C — Component rules

| Class / pattern | Use |
|---|---|
| `.entrance` / `.entrance-atmosphere` / `.entrance-scrim` | Home LCP still + left scrim for AA thesis |
| `.current-index` | studying / building / writing status lines |
| `.system-map-section` / `.system-map-svg` | Six-domain map; no JS train |
| `.selected-systems` / `.system-record` / `.record-id` | Home SYS rows; impact lines from `outcomes` where matched |
| `.reading-room` / `.catalogue-line` | Featured note + index; shelf figure |
| `.workshop` / `.workshop-record` | LAB rows; desk figure (cropped) |
| `.proof-strip` | Singapore + ≤4 platforms |
| `.btn` / `.btn-primary` | **One** primary CTA on Home (**View systems**); Connect secondary |
| `.library-card` / `.site-footer` | Footer: location · focus · mailto · social |
| `.site-nav` / `.nav-elsewhere` | **Systems · Notes · Profile · Credentials · Connect**; Blog/Medium/LinkedIn/GitHub under Elsewhere |
| `.page-toc` / `.section-fold` | Long-form sidebar + collapsible folds (unchanged mechanics) |
| `#search` + Pagefind | Catalogue search on Systems + Professional record |

**Motion:** Map-node and record hover/focus only. **No** per-section `rise` on Home. Career Journey slides stay opacity-only under reduced motion.

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
- Keep primary nav short: **Systems · Notes · Profile · Credentials · Connect**
- Brass/gold ≤10%; railway green in hairlines only
- Derive proof from `site.json` / export only

**Don’t**

- Boardroom outcome strip in hero; portrait chip on Home
- Steampunk tropes (gears, rockets, chalkboard props in Workshop crop)
- Fraunces/Sora, cream `#f4f0e8`, or SaaS card kits
- Tracked ALL-CAPS eyebrows on every heading; decorative numbered `01 02 03`
- Invent metrics; cert wall on Home; visitor-facing phone
- Migration / Phase notes in footer
