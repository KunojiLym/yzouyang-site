# Design system

Visual contract for yzouyang-site Phase 1. Implementation source of truth: [`src/styles.css`](../src/styles.css). Builder / IA rules: [site-builder.md](site-builder.md).

## Principles

- **Dark atmospheric field** — deep green-black base with soft radial glows; never rely on transparent body fill alone
- **Brand-first home** — name as hero signal; specialist line in gold; portrait as visual anchor
- **Type pairing** — Fraunces (display) + Sora (UI/body)
- **Gold accent sparingly** — links, primary CTAs, specialist line; not rainbow chrome
- **Calm enterprise persona** — no neon, glassmorphism dashboards, CLI splash screens, or junior template illustration heroes
- **Progressive embeds** — Figma iframes always paired with an Open deck / fallback link

## Tokens (`:root`)

| Token | Role | Approx value |
|---|---|---|
| `--bg-deep` | Page fill / sticky header base | `#0c1412` |
| `--bg-mid` | Secondary surface | `#152a24` |
| `--ink` | Primary text | `#e8efe9` |
| `--muted` | Secondary text | `#9aada3` |
| `--accent` | Links / emphasis | `#d4a35c` |
| `--accent-soft` | Soft fills / primary button wash | `rgba(212, 163, 92, 0.18)` |
| `--line` | Hairline borders | `rgba(232, 239, 233, 0.12)` |
| `--glow` | Ambient green glow | `rgba(70, 140, 120, 0.35)` |
| `--font-display` | Headings / brand | Fraunces, serif fallbacks |
| `--font-body` | Body / UI | Sora, system sans |
| `--max` | Content measure | `68rem` |

`html` and `body` set `background-color: var(--bg-deep)`. Gradients use `background-image` on `body` with `background-attachment: fixed`.

## Typography

| Element | Notes |
|---|---|
| `.brand` | Display, ~1.35rem, wordmark `yzouyang` |
| Hero `h1` | Display, clamp ~2.6–4.6rem, tight tracking |
| `.subtitle` | Accent color, specialist line |
| `.lede` / `.page-lede` | Muted, max ~36–40rem |
| `main.page h1–h3` | Display scale for long pages |
| `.meta` | Small muted metadata |
| `.proof-strip` | Compact chips; strong for location / counts |

## Layout

- **Sticky header** — `.site-header-wrap` (`position: sticky; top: 0`) with translucent deep fill + blur; contains brand, desktop nav, Contact control, mobile `details.nav-menu`
- **Main** — `.page` capped at `--max`, horizontal padding
- **Home hero** — two-column grid; mobile stacks **copy before photo** (no photo-first order)
- **Long pages** — `.page-toc` jump links before Pagefind search
- **Contact** — Home `#contact` section (not a nav destination)

## Components

| Class | Use |
|---|---|
| `.btn` / `.btn-primary` | CTA row; primary = accent border + soft fill |
| `.header-contact` | Sticky Contact jump to `/#contact` |
| `.cta-row` | Home button group |
| `.proof-strip` | Home proof chips (location, cert count, platforms) |
| `.portrait-chip` | Role · location over photo |
| `.hero-visual` / `.hero-photo` | Portrait + vignette overlay |
| `.site-nav` / `.site-nav-desktop` | Desktop primary links |
| `.nav-menu` | Mobile hamburger (`details`/`summary`) |
| `.page-toc` | On-this-page anchors |
| `.item-list` | Portfolio / credentials / writing rows |
| `.issuer-group` | Credentials `h3` vendor subgroups |
| `.writing-list` | About selected writing titles |
| `.embed-wrap` / `.embed-fallback` / `.embed-frame` | Figma progressive enhancement |
| `.contact-section` | Home contact block |
| `.site-footer` | © + mailto + social |
| `#search` + Pagefind UI vars | Dark-themed search on portfolio/credentials |

External nav links use `.external` (↗ via CSS `::after`).

## Motion

- `.hero` / `.page` use short `rise` entrance
- Honor `prefers-reduced-motion: reduce` (animations/transitions off)

## Do / don’t

**Do**

- Keep solid `--bg-deep` under gradients
- Keep Figma Open deck / fallback visible even when the iframe is blank
- Curate platforms and writing highlights; prefer fewer strong signals
- Keep primary nav short; Contact stays a sticky control

**Don’t**

- Put migration / Phase 1 changelog in the footer or header
- Reintroduce Contact as a primary nav page
- Add neon particles, glass OS shells, or terminal boot gates
- Ship bare `build.py` without Pagefind when portfolio/credentials expect search
- Invent proof metrics — derive from export / `site.json` only
