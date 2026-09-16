# Styles modules

Source of truth for the site's CSS. [`scripts/build.py`](../../scripts/build.py) concatenates these files (in the order below) into `dist/styles.css`. Do not edit a monolithic `src/styles.css` — it is a pointer only.

| File | Responsibility |
|---|---|
| `tokens.css` | Semantic design tokens (`:root` / `[data-theme]`): dual-theme color, type scale, spacing scale, radius scale, documented breakpoints |
| `base.css` | Document defaults, links, focus, scroll padding |
| `chrome.css` | Sticky header, brand, primary nav, theme toggle, Pagefind header slot (`#search`), library-card footer |
| `home.css` | Home entrance (token atmosphere), viewport-paced snap sections, featured record strip, operating principle, practice areas |
| `library.css` | Personal Systems Library split-pane shell (`.library-shell`, index list, overlay rail when unpinned, panels, mobile back) on `/systems/`, `/notes/`, `/credentials/` |
| `components.css` | Shared page patterns: headings, lists, credential cards, embed fallbacks, proof blocks |
| `longform.css` | Legacy long-form dossier layout (`.page-with-toc`, sticky sidebar TOC) — retained for any remaining TOC-style panels, not the primary library chrome |
| `search.css` | Pagefind dark theme |
| `motion.css` | `rise` + `prefers-reduced-motion` |
| `career-journey.css` | *(not assembled)* — WIP slide chrome for the deferred native `/career-journey/` page; see [docs/career-journey-native-plan.md](../../docs/career-journey-native-plan.md) |

Visual contract: [docs/design-system.md](../../docs/design-system.md).

All font-size/margin/padding/gap/border-radius values in assembled modules are tokenized — see [docs/token-migration-checklist.md](../../docs/token-migration-checklist.md) for the original raw-value → token mapping. New code must use the tokens in `tokens.css` too; this isn't just convention, it's enforced:

- **`.stylelintrc.json`** (`scale-unlimited/declaration-strict-value`) fails `npm run lint:css` if `font-size`, `border-radius`, `margin*`, `padding*`, or `*gap` use a raw value instead of `var(--...)`. A handful of genuine one-offs (e.g. `0.75em` relative-to-parent arrow markers in `chrome.css`) are allow-listed in `ignoreValues` with an inline comment explaining why — add to that list rather than disabling the rule if you hit a real exception.
- **`scripts/check_token_drift.py`** fails CI if a raw hex color or a `font-family` not wrapped in `var()` shows up in any CSS file other than `tokens.css`.

Both run in `.github/workflows/ci.yml` alongside Playwright (`npm run test:e2e`, `npm run test:a11y`, and non-blocking `npm run test:visual` until baseline screenshots are committed — see the header comment in `tests/e2e/visual.spec.mjs`).

Adding a new page or component? [docs/site-builder.md](../../docs/site-builder.md#adding-a-new-page-or-component) has the step-by-step checklist (which token to reach for, which file to touch, which checks to run before opening a PR).
