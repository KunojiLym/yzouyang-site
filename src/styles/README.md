# Styles modules

Source of truth for the site's CSS. [`scripts/build.py`](../../scripts/build.py) concatenates these files (in the order below) into `dist/styles.css`. Do not edit a monolithic `src/styles.css` — it is a pointer only.

| File | Responsibility |
|---|---|
| `tokens.css` | Semantic design tokens (`:root`): color, type scale, spacing scale, radius scale, documented breakpoints |
| `base.css` | Document defaults, links, focus, scroll padding |
| `chrome.css` | Sticky header, brand, nav, footer |
| `home.css` | Hero, outcomes, proof strip, CTAs, contact section |
| `components.css` | Page headings, lists, embeds, about blocks |
| `longform.css` | Portfolio/credentials sticky sidebar TOC |
| `search.css` | Pagefind dark theme |
| `motion.css` | `rise` + `prefers-reduced-motion` |
| `career-journey.css` | `/career-journey/` slide chrome + Tier 2 composed-layout grid recipes (see [docs/career-journey-native-plan.md](../../docs/career-journey-native-plan.md)) |

Visual contract: [docs/design-system.md](../../docs/design-system.md).

All font-size/margin/padding/gap/border-radius values in these files are tokenized — see [docs/token-migration-checklist.md](../../docs/token-migration-checklist.md) for the original raw-value → token mapping. New code must use the tokens in `tokens.css` too; this isn't just convention, it's enforced:

- **`.stylelintrc.json`** (`scale-unlimited/declaration-strict-value`) fails `npm run lint:css` if `font-size`, `border-radius`, `margin*`, `padding*`, or `*gap` use a raw value instead of `var(--...)`. A handful of genuine one-offs (e.g. `0.75em` relative-to-parent arrow markers in `chrome.css`) are allow-listed in `ignoreValues` with an inline comment explaining why — add to that list rather than disabling the rule if you hit a real exception.
- **`scripts/check_token_drift.py`** fails CI if a raw hex color or a `font-family` not wrapped in `var()` shows up in any CSS file other than `tokens.css`.

Both run in `.github/workflows/ci.yml` alongside the existing Playwright suite, which also now includes an axe-core accessibility check (`npm run test:a11y`, WCAG2A/AA) and a visual-regression scaffold (`npm run test:visual`) — the latter runs non-blocking in CI until baseline screenshots are generated and committed (see the comment header in `tests/e2e/visual.spec.mjs` for the one-time setup steps).

Adding a new page or component? [docs/site-builder.md](../../docs/site-builder.md#adding-a-new-page-or-component) has the step-by-step checklist (which token to reach for, which file to touch, which checks to run before opening a PR).
