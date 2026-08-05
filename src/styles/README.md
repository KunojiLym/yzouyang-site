# Styles modules

Source of truth for Phase 1 CSS. [`scripts/build.py`](../../scripts/build.py) concatenates these files (in the order below) into `dist/styles.css`. Do not edit a monolithic `src/styles.css` — it is a pointer only.

| File | Responsibility |
|---|---|
| `tokens.css` | Semantic design tokens (`:root`) |
| `base.css` | Document defaults, links, focus, scroll padding |
| `chrome.css` | Sticky header, brand, nav, footer |
| `home.css` | Hero, outcomes, proof strip, CTAs, contact section |
| `components.css` | Page headings, lists, embeds, about blocks |
| `longform.css` | Portfolio/credentials sticky sidebar TOC |
| `search.css` | Pagefind dark theme |
| `motion.css` | `rise` + `prefers-reduced-motion` |

Visual contract: [docs/design-system.md](../../docs/design-system.md).
