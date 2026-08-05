# Token migration checklist (Phase 2)

Phase 1 (done) added a type scale, spacing scale, radius scale, and documented breakpoint constants to [`tokens.css`](../src/styles/tokens.css) — see [design-system.md](design-system.md) for the token tables. This doc is the file-by-file, line-by-line map from what's in the CSS today to what it should become, so Phase 2 is a mechanical migration rather than a design exercise done twice.

Recommended migration order (lowest raw-value surface first, per the upgrade plan): `base.css` → `motion.css` → `search.css` (no changes needed, listed for completeness) → `components.css` → `chrome.css` → `longform.css` → `home.css`.

Drift column shows the difference between the raw value and its assigned token — anything ≤0.15rem (2.4px) is treated as acceptable rounding under the "refactor freely" scope agreed for this project; anything larger is called out explicitly.

## Font sizes

| File | Line | Raw value | Token | Drift |
|---|---|---|---|---|
| chrome.css | 31 | `0.85rem` | `--text-sm` | 0 |
| chrome.css | 44 | `1.35rem` | `--text-xl` | 0 |
| chrome.css | 59 | `0.9rem` | `--text-base` | 0 |
| chrome.css | 74 | `0.75em` | `--text-xs` (or leave `em` if relative-to-parent sizing is intentional — check context) | 0 |
| chrome.css | 91 | `0.9rem` | `--text-base` | 0 |
| chrome.css | 118 | `0.75rem` | `--text-xs` | 0 |
| chrome.css | 143 | `0.85rem` | `--text-sm` | 0 |
| chrome.css | 160 | `0.75em` | `--text-xs` (check `em` context, as above) | 0 |
| components.css | 15 | `clamp(1.85rem, 3.5vw, 2.35rem)` | `--text-display-1` | 0 |
| components.css | 24 | `clamp(1.3rem, 2.5vw, 1.65rem)` | `--text-display-2` | 0 |
| components.css | 34 | `1.1rem` | `--text-lg` (`1.2rem`) | +0.10rem |
| components.css | 42 | `1.05rem` | `--text-md` | 0 |
| components.css | 52 | `1.05rem` | `--text-md` | 0 |
| components.css | 84 | `1.2rem` | `--text-lg` | 0 |
| components.css | 98 | `0.9rem` | `--text-base` | 0 |
| components.css | 103 | `0.9rem` | `--text-base` | 0 |
| components.css | 122 | `0.9rem` | `--text-base` | 0 |
| components.css | 138 | `0.9rem` | `--text-base` | 0 |
| components.css | 191 | `1.1rem` | `--text-lg` (`1.2rem`) | +0.10rem |
| components.css | 207 | `1.1rem` | `--text-lg` (`1.2rem`) | +0.10rem |
| home.css | 61 | `0.75rem` | `--text-xs` | 0 |
| home.css | 71 | `clamp(2.6rem, 7vw, 4.6rem)` | `--text-display-hero` | 0 |
| home.css | 81 | `clamp(1.05rem, 2.2vw, 1.35rem)` | `--text-display-4` | 0 |
| home.css | 91 | `1.05rem` | `--text-md` | 0 |
| home.css | 110 | `1.35rem` | `--text-xl` | 0 |
| home.css | 119 | `0.8rem` | `--text-sm` (`0.85rem`) | +0.05rem |
| home.css | 136 | `0.8rem` | `--text-sm` (`0.85rem`) | +0.05rem |
| home.css | 192 | `clamp(1.3rem, 2.5vw, 1.65rem)` | `--text-display-2` | 0 |
| longform.css | 23 | `0.7rem` | `--text-xs` (`0.75rem`) | +0.05rem |
| longform.css | 40 | `0.85rem` | `--text-sm` | 0 |
| longform.css | 82 | `0.8rem` | `--text-sm` (`0.85rem`) | +0.05rem |
| longform.css | 128 | `clamp(1.15rem, 2.2vw, 1.4rem)` | `--text-display-3` | 0 |

Note on the three `1.1rem` cases in `components.css`: they land 0.10rem below `--text-lg`. Before mapping mechanically, check whether they were meant to match the `1.2rem` at line 84, or whether they're deliberately one step down — if the latter, it's worth adding a `--text-md-lg: 1.125rem` step rather than forcing a visible size bump in three places. Flag for a quick visual diff during Phase 2 rather than assuming.

## Spacing (margin / padding / gap / inset)

| File | Line | Raw value | Token | Drift |
|---|---|---|---|---|
| chrome.css | 16 | `1rem 1.5rem` | `--space-4 --space-6` | 0 |
| chrome.css | 19 | `0.85rem 1.5rem` | `--space-3 --space-6` | 0 |
| chrome.css | 26 | `0.75rem 1rem` | `--space-3 --space-4` | 0 |
| chrome.css | 32 | `0.45rem 0.85rem` | `--space-2 --space-3` | +0.05 / 0 |
| chrome.css | 38 | `0.35rem` | `--space-tight` | 0 |
| chrome.css | 58 | `0.65rem 1rem` | `--space-3 --space-4` | +0.10 / 0 |
| chrome.css | 92 | `0.35rem 0.65rem` | `--space-tight --space-3` | 0 / +0.10 |
| chrome.css | 109 | `0.5rem` | `--space-2` | 0 |
| chrome.css | 110 | `0.75rem` | `--space-3` | 0 |
| chrome.css | 111 | `0.75rem 0 0` | `--space-3 0 0` | 0 |
| chrome.css | 121 | `0.5rem 0 0.15rem` | `--space-2 0 --space-hairline` | 0 |
| chrome.css | 141 | `1.5rem 1.5rem 2.5rem` | `--space-6 --space-6 --space-10` | 0 |
| chrome.css | 148 | `0.25rem 0` | `--space-1 0` | 0 |
| chrome.css | 154 | `0.5rem 1rem` | `--space-2 --space-4` | 0 |
| chrome.css | 155 | `0.5rem` | `--space-2` | 0 |
| components.css | 5 | `2rem 1.5rem 4rem` | `--space-8 --space-6 --space-12` | 0 |
| components.css | 27 | `2.5rem 0 1rem` | `--space-10 0 --space-4` | 0 |
| components.css | 36 | `1.75rem 0 0.75rem` | `--space-7 0 --space-3` | 0 |
| components.css | 48 | `1.5rem 0 0.75rem` | `--space-6 0 --space-3` | 0 |
| components.css | 73 | `1.5rem` | `--space-6` | 0 |
| components.css | 77 | `1.5rem` | `--space-6` | 0 |
| components.css | 96 | `0.5rem 0 0` | `--space-2 0 0` | 0 |
| components.css | 112 | `0.35rem 0 0` | `--space-tight 0 0` | 0 |
| components.css | 113 | `1.1rem` | `--space-5` (`1.25rem`) | +0.15 |
| components.css | 120 | `0.5rem 1rem` | `--space-2 --space-4` | 0 |
| components.css | 121 | `0.5rem` | `--space-2` | 0 |
| components.css | 126 | `1rem` | `--space-4` | 0 |
| components.css | 131 | `0.65rem` | `--space-3` (`0.75rem`) | +0.10 |
| components.css | 132 | `0.75rem 1rem` | `--space-3 --space-4` | 0 |
| components.css | 177 | `1.2rem` | `--space-5` (`1.25rem`) | +0.05 |
| components.css | 181 | `0.85rem` | `--space-3` (`0.75rem`) | -0.10 |
| components.css | 199 | `1.25rem 0 1.25rem 1.25rem` | `--space-5 0 --space-5 --space-5` | 0 |
| home.css | 6 | `2.5rem 3rem` | `--space-10 --space-11` | 0 |
| home.css | 10 | `3rem 1.5rem 4rem` | `--space-11 --space-6 --space-12` | 0 |
| home.css | 55–57 | `0.65rem` (×3, inset) | `--space-3` (`0.75rem`) | +0.10 each |
| home.css | 60 | `0.4rem 0.65rem` | `--space-2 --space-3` | +0.10 / +0.10 |
| home.css | 97 | `0.75rem 1.25rem` | `--space-3 --space-5` | 0 |
| home.css | 121 | `0.2rem` | `--space-1` (`0.25rem`) | +0.05 |
| home.css | 128 | `0.5rem 0.65rem` | `--space-2 --space-3` | 0 / +0.10 |
| home.css | 138 | `0.35rem 0.7rem` | `--space-tight --space-3` | 0 / +0.05 |
| home.css | 152 | `0.75rem 1rem` | `--space-3 --space-4` | 0 |
| home.css | 158 | `0.65rem 1.05rem` | `--space-3 --space-4` (`1rem`) | +0.10 / -0.05 |
| home.css | 194 | `2rem 0 0.75rem` | `--space-8 0 --space-3` | 0 |
| home.css | 202 | `2rem` | `--space-8` | 0 |
| longform.css | 5 | `1.75rem 2.25rem` | `--space-7 --space-9` | 0 |
| longform.css | 15 | `0.85rem 1rem` | `--space-3 --space-4` | -0.10 / 0 |
| longform.css | 36 | `0.35rem 1rem` | `--space-tight --space-4` | 0 |
| longform.css | 64 | `0.55rem` | `--space-2` (`0.5rem`) | -0.05 |
| longform.css | 72 | `0.35rem 0 0.15rem 0.75rem` | `--space-tight 0 --space-hairline --space-3` | 0 |
| longform.css | 76 | `0.35rem` | `--space-tight` | 0 |
| longform.css | 78 | `0.65rem` | `--space-3` (`0.75rem`) | +0.10 |
| longform.css | 100 | `0.85rem 1rem` | `--space-3 --space-4` | -0.10 / 0 |
| longform.css | 113 | `0.35rem` | `--space-tight` | 0 |
| longform.css | 132 | `0.5rem 1rem 1.15rem` | `--space-2 --space-4 --space-5` (`1.25rem`) | 0 / 0 / +0.10 |
| longform.css | 150 | `0.35rem 0.85rem` | `--space-tight --space-3` | 0 / -0.10 |
| search.css | 3 | `2rem` | `--space-8` | 0 |
| search.css | 42 | `0.5rem` | `--space-2` | 0 |

`!important` flags at `longform.css:72,76,78` should be re-examined during migration — worth understanding why they're needed rather than carrying them forward unquestioned.

## Border radius (no drift — direct rename)

| File | Occurrences | Token |
|---|---|---|
| Various | `0.15rem` (×2) | `--radius-sm` |
| Various | `0.2rem` (×9) | `--radius-md` |
| Various | `0.25rem` (×2) | `--radius-lg` |

Run `grep -rn "border-radius" src/styles/*.css` at migration time to get current line numbers (not reproduced here since none of these values change).

## Breakpoints

| File | Line | Current | Target | Note |
|---|---|---|---|---|
| home.css | 198 | `max-width: 800px` | stays `800px` (`--bp-sm` reference) | No change — already the intended value |
| chrome.css | 124 | `max-width: 900px` | stays `900px` (`--bp-md` reference) | No change |
| longform.css | 135 | `max-width: 960px` | change to `900px` (`--bp-md` reference) | Only real breakpoint change in Phase 2 — verify sidebar collapse still reads well at 900px before shipping |

## Out of scope for Phase 2

- `motion.css`, `base.css`: no raw font-size/spacing values present — nothing to migrate.
- `search.css`: only 2 spacing values, both trivial exact-matches (included above for completeness).
- Color values in `tokens.css` itself: unchanged, this migration is type/space/radius/breakpoint only.
