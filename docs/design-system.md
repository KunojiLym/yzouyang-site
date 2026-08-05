# Design system

Visual contract for yzouyang-site Phase 1. Implementation: [`src/styles.css`](../src/styles.css). Builder / IA / embeds: [site-builder.md](site-builder.md).

**Governing sentence:** Design the site like a senior enterprise architect’s public briefing document, with editorial polish and technical precision.

**Style direction:** Calm enterprise editorial — dark, restrained, slightly atmospheric, structured and businesslike. Mood = **boardroom-meets-technical-journal**, not futurist demo lab, AI-builder novelty, or startup theater. Optimize for **authority, scanability, and proof density** — not animation or decorative UI.

---

## Layer A — Brand tokens

**Positioning:** Senior Data and AI Transformation Leader. Platform, governance, FinOps, multi-cloud, and agentic AI appear as **disciplined capability signals**, not product theater.

**Palette:** Deep charcoal-green / green-black; **one** muted gold accent; neutral text. Avoid generic blue-purple AI palettes. Gold-on-dark is allowed only with discipline (enterprise rigor, not boutique luxury).

**Atmosphere:** **One** ambient glow layer maximum; solid `--bg-deep` under gradients. No particles, neon, glassmorphism, terminal motifs, gradient text, or oversized AI imagery.

### Semantic tokens (`:root`)

| Token | Role | Approx value |
|---|---|---|
| `--bg-deep` | Page fill / sticky header base | `#0c1412` |
| `--bg-mid` | Secondary surface | `#152a24` |
| `--bg-elevated` | Slightly lifted surface | `#1a3028` |
| `--bg-panel` | TOC / search / panel fills | `rgba(255,255,255,0.03)` |
| `--bg-hover` | Hover wash | `rgba(255,255,255,0.06)` |
| `--text-strong` | Emphasized text | `#f2f7f3` |
| `--text-default` / `--ink` | Primary text | `#e8efe9` |
| `--text-muted` / `--muted` | Secondary text | `#9aada3` |
| `--text-faint` | Tertiary / chrome hints | `#6f8178` |
| `--accent` | Links / specialist line / primary CTA border | `#d4a35c` |
| `--accent-soft` | Soft accent fill | `rgba(212, 163, 92, 0.18)` |
| `--accent-hover` | Link / accent hover | `#f0c27a` |
| `--accent-active` | Pressed accent | `#c4924a` |
| `--focus-ring` | `:focus-visible` outline | `rgba(212, 163, 92, 0.65)` |
| `--line-strong` | Stronger dividers | `rgba(232, 239, 233, 0.22)` |
| `--line-soft` / `--line` | Hairline borders | `rgba(232, 239, 233, 0.12)` |
| `--success` / `--warning` / `--danger` | Status (reserved; use sparingly) | muted green / amber / rose |
| `--glow` | Single ambient green glow | `rgba(70, 140, 120, 0.35)` |
| `--font-display` | Hero title + brand wordmark only | Fraunces |
| `--font-body` | Everything else | Sora |
| `--max` | Content measure | `68rem` |

`html` / `body` set `background-color: var(--bg-deep)`. Gradients use `background-image` only.

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
4. **Selected systems / work** — portfolio case rows
5. **Writing / speaking** — publications-style lists (About Selected writing; external Blog/Medium/LinkedIn)
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
| `.site-nav` / `.nav-menu` | Primary nav + mobile menu |
| `.page-toc` | On-this-page anchors (panel surface) |
| `.item-list` | Portfolio / credentials / contact rows (editorial, not cards) |
| `.issuer-group` | Credentials vendor subgroups |
| `.writing-list` | Publications rows (title / venue·date / external link) |
| `.embed-wrap` / `.embed-fallback` / `.embed-frame` | Visual surfaces only — embed **policy** in site-builder |
| `.contact-section` | Home contact block |
| `.site-footer` | © + mailto + social |
| `#search` + Pagefind vars | Dark panel search on portfolio/credentials |

**Sticky header:** `.site-header-wrap` — opaque ≥94% `--bg-deep`; blur additive only.

**Motion:** Short, minimal entrance (`rise`); honor `prefers-reduced-motion`. No novelty animation.

External nav links use `.external` (↗ via CSS `::after`).

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
