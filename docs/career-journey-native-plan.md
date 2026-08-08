# Career Journey: native implementation plan

Plan to replace the `/about/` Figma Deck embed (`about.career_journey` in
`data/export_public.json`, rendered via `figma_embed_html()` in
`scripts/build.py`) with a standalone, natively-built, independently
shareable page. See [site-builder.md](site-builder.md) for the pipeline this
slots into and [design-system.md](design-system.md) for the token/breakpoint
contract everything below must respect.

**Why native, and why this deck specifically:** see the embed-vs-native
discussion this plan follows on from — short version, this deck is
"purely animated" narrative content (no interactive prototype state to
fake) that the operator expects to update with some frequency, which is
exactly where a Figma embed's edit-and-re-export cycle costs the most and
buys the least.

## 1. Goals

- New route `/career-journey/`, independently linkable/shareable (own
  `<title>`, own OG/social meta), not just a section nested in `/about/`.
- Content lives in a data file, not hardcoded HTML — same "content in data,
  presentation in `build.py`" convention as every other page.
- Slide layout must support three tiers of authoring effort: fast
  templated slides for repeating content, declarative composed layouts for
  bespoke-but-still-data-driven slides, and a raw-HTML escape hatch for the
  rare one-off — see §3.
- Mandatory image alt text — the one accessibility gap a Figma iframe
  cannot be fixed to close from this side of the embed.
- No new runtime dependency. CSS transitions + a small `IntersectionObserver`
  module, same spirit as the existing `src/track.js`.
- `/about/` keeps a link card to the new page instead of the embed.

## 2. Content pipeline

- **Source data:** `data/career-journey.yaml` (new file). Standalone in
  this repo's `data/` folder rather than routed through the
  `personal-content` → `export_public.json` pipeline — this is
  presentation/portfolio content, not CV/profile data, and the operator
  wants to edit it frequently without a cross-repo round trip. Revisit if
  that changes.
- **Images:** exported once from Figma per slide, optimized (resize to
  actual display width, WebP with PNG fallback if needed), stored under
  `assets/career-journey/`. This export happens once regardless of
  embed-vs-native, since the current iframe embed would eventually need
  re-export too if Figma's embed format changes.
- **Text content:** wherever a slide in the original deck is "a picture of
  text," transcribe it into the `body`/`title` fields as real text instead
  of shipping it as an image. This is what makes the page Pagefind-indexable
  and screen-reader-readable, which the embed structurally cannot be.

## 3. Data file schema

Top level:

```yaml
title: "Career Journey"
subtitle: "My Long and Winding Journey into Data"
lede: "One-paragraph dek shown at the top of the page."
source_link: "https://www.figma.com/deck/0nKvFiourL6ya4HCTEN0AL/Career-Journey-2025"
source_label: "View original Figma deck"
default_transition: fade-up
slides: [ ... ]
```

Each entry in `slides` has a `kind` discriminator that `build_career_journey()`
dispatches on. Three tiers, ordered by expected frequency of use:

**Tier 1 — named templates** (fast path, the common case):

```yaml
kind: title | image | text | quote | stat
```

Fixed fields per kind (`title`/`body`/`image`+`image_alt`/`caption`/
`stat_value`+`stat_label`/`attribution`), same shape drafted earlier in
this plan's predecessor discussion. No layout decisions to make — this is
the "just write the content" path for slides that are genuinely
one-thing-per-slide.

**Tier 2 — composed layout** (declarative, bespoke, still data-driven):

```yaml
kind: composed
layout: split-60-40   # references the grid recipe library, §4
blocks:
  - region: main
    type: image
    image: /assets/career-journey/act2-collage-1.png
    image_alt: "Required, non-empty."
  - region: side-top
    type: image
    image: /assets/career-journey/act2-collage-2.png
    image_alt: "Required, non-empty."
  - region: side-bottom
    type: text
    body: "Caption or callout text next to the images."
```

`layout` must match one of the named recipes in §4; `blocks[].region` must
match one of that recipe's named grid areas. Both are validated (§6).

**Tier 3 — raw partial** (escape hatch, rare):

```yaml
kind: partial
partial: slides/act3-signature-moment.html   # new dir: data/career-journey-slides/
```

`build.py` reads that file's contents verbatim and wraps it in the
standard `<section id="{slug}" class="cj-slide">...</section>` shell — no
`esc()`, since this is hand-authored trusted markup, not user-submitted
data. Reserve this tier for slides that genuinely don't fit a tier-2
recipe; if more than ~2-3 slides in a deck end up here, that's a signal
a new tier-2 recipe is missing, not that tier 3 is working as intended.

Shared fields on every slide, regardless of `kind`: `id` (slug, required,
used as anchor + section `id`), `chapter` (optional, groups slides for an
in-page progress nav — §5), `transition` (optional per-slide override of
`default_transition`).

## 4. Grid recipe library (Tier 2)

A small, hand-curated set of named `grid-template-areas`, defined once in
the new `src/styles/career-journey.css` module (see §5 for where this
file fits in the existing CSS architecture) and referenced by name from
the data file — deliberately not arbitrary x/y/w/h positioning, which
would just be rebuilding Figma's canvas model in YAML and reintroducing
the exact fiddly-coordinate maintenance cost native was meant to avoid.

Starting set (expand only when a real slide from the source deck needs a
shape not covered — resist speculative recipes):

| Recipe | Areas | Typical use |
|---|---|---|
| `split-60-40` | `main`, `side-top`, `side-bottom` | one large image + two stacked smaller elements |
| `overlay-caption` | `bg`, `caption` | full-bleed image with a caption overlaid at one edge |
| `three-up` | `left`, `center`, `right` | three roughly equal images/blocks in a row |
| `full-bleed-text-overlay` | `bg`, `text` | background image with large text on top |

Each recipe gets one `.cj-layout--{name}` class using `grid-template-areas`
per the design-system.md breakpoint contract (`--bp-sm`/`--bp-md` collapse
to single-column stacking on narrow viewports — no new breakpoint without
writing it into design-system.md per the existing rule).

**Action before finalizing this table:** walk the real Career Journey
deck's slide images once we have them exported, and confirm this covers
what's actually there rather than guessing — cheap to adjust now, more
disruptive to redo after slides are authored against it.

## 5. `build.py` / CSS / JS changes

- **New builder:** `build_career_journey(site, export_or_yaml) -> str`,
  same signature/return-a-string-of-HTML pattern as `build_portfolio` /
  `build_credentials`. Reuses `layout()`, `nav_html()`, `footer_html()`,
  `esc()`, `with_base()` — no new HTML-assembly pattern introduced.
- **New route:** `dist/career-journey/index.html`, written from `main()`
  alongside the other `write(...)` calls.
- **Nav / IA:** add to `data/site.json`'s `nav` array, or (matching the
  "Contact is not a primary nav item" precedent in site-builder.md's IA
  rules) keep it out of primary nav and reachable only via a link card on
  `/about/` plus direct sharing — worth deciding explicitly rather than
  defaulting, since it affects whether this reads as a "real site page" or
  a "shareable extra." Leaning toward: out of primary nav, linked from
  About, same tier as the Figma embed is today.
- **`/about/` change:** replace the `journey_inner` embed block (currently
  `figma_embed_html(...)` at `build.py:565-582`) with a plain link card —
  title, one-line description, "Read my career journey →" to
  `/career-journey/`.
- **New CSS module:** `src/styles/career-journey.css`, added to the
  concatenation order in `assemble_styles()` and to the file-by-file
  responsibility table in `src/styles/README.md` (per the existing
  per-module ownership convention — do not add these rules to
  `components.css` or `chrome.css`). Contains the Tier-2 grid recipes
  (§4) and the reveal-transition CSS (opacity/transform pairs keyed by
  `data-transition`, gated behind `prefers-reduced-motion: no-preference`
  so the animation genuinely turns off for users who've asked for that —
  the deck's content must be fully visible/readable with zero JS or with
  motion disabled, not just "eventually" visible).
- **New JS module:** `src/career-journey.js` (or extend `src/track.js` if
  it's already a shared "small page-specific behaviors" file — check
  before adding a new file). `IntersectionObserver` toggling an `.is-in`
  class per `.cj-slide`; reads `transition`/`default_transition` from a
  `data-transition` attribute set at build time. ~15-20 lines, no
  dependency.
- **OG/social meta:** confirm whether `layout()` currently sets
  `og:title`/`og:description`/`og:image`/canonical at all (not confirmed
  either way yet) — this page is the one most likely to be shared 1:1
  outside site navigation, so it's worth having a real preview image
  (e.g. the deck's existing `thumbnail.png`, or a generated one) rather
  than a generic site-wide default.

## 6. Validation additions

- **`scripts/lint.py`:** extend to validate `data/career-journey.yaml`
  before build — every slide has a non-empty `id`; every `image` block has
  a non-empty `image_alt`; every `composed` slide's `layout` is a known
  recipe name and every `blocks[].region` matches that recipe's areas;
  every `partial` path exists on disk. Fail loudly (same spirit as
  `check_token_drift.py`) rather than silently rendering a broken slide.
- **`scripts/test_site_build.py`:** add a contract check that
  `dist/career-journey/index.html` exists, contains one `<section>` per
  slide, and that every `<img>` has a non-empty `alt` attribute (this is
  the concrete, automated version of the accessibility argument for going
  native — worth having CI actually enforce it, not just assert it in
  conversation).
- **`tests/e2e/a11y.spec.mjs`:** add `/career-journey/` to the routes the
  existing axe-core sweep already checks — no new landmark-uniqueness risk
  expected here (no iframe), but confirms it rather than assumes it.
- **`tests/e2e/visual.spec.mjs`:** add a snapshot once the page is stable
  enough to baseline (per the existing non-blocking-until-baselined
  convention noted in that file's header comment).

## 7. Migration order

1. Export slide images from Figma; transcribe any picture-of-text slides
   into real text. (Blocking on nothing else — do this first since it's
   the slowest, most manual step.)
2. Finalize the Tier-2 recipe table (§4) against the *real* exported
   slides, not speculatively.
3. Author `data/career-journey.yaml` fully.
4. Implement `build_career_journey()`, the CSS module, and the JS reveal
   module; wire the new route into `main()`.
5. Add the `lint.py` validation rules (§6) and run them against the
   authored data file — fix any missing alt text / bad recipe references
   before moving on, not after.
6. Replace the `/about/` embed with the link card.
7. Run the full local check sequence from site-builder.md's "Adding a new
   page or component" checklist: `lint.py`, `check_token_drift.py`,
   `npm run lint:css`, `test:e2e`, `test:a11y`, `test:visual`.
8. Open a **draft PR only** per the repo's agent/contributor rules — no
   direct push/merge to `main`.

## 8. Open decisions (need operator input before or during implementation)

- Primary nav placement vs. link-only-from-About (§5) — leaning link-only,
  not decided.
- Whether `data/career-journey.yaml` should eventually flow through the
  `personal-content` pipeline for consistency, or stay standalone in this
  repo permanently since it's presentation content, not CV data.
- Confirm current OG/social meta tag state in `layout()` before assuming
  work is needed there.
- Exact Tier-2 recipe set (§4's table is a starting hypothesis, not final)
  — confirm against the real exported slide images before locking it in.

## 9. Implementation notes (added once §1–§8 was actually built)

- **PyYAML is now a real dependency**, managed via `uv` — `pyproject.toml`
  is this repo's uv project file (`requires-python = ">=3.10"`,
  `pyyaml>=6.0`, `tool.uv.package = false` since this isn't a
  distributable package). Run `uv sync` once before building. CI installs
  it via `astral-sh/setup-uv` + `uv sync`, and every Python invocation in
  `.github/workflows/ci.yml` now goes through `uv run python ...`. This is
  the one place this plan's "no new dependency" framing (§1) was revised —
  that goal was about not adding a JS framework to the browser bundle,
  which still holds; it did not anticipate needing a YAML parser for
  `data/career-journey.yaml` on the Python side, since every other data
  file in this repo is JSON with no parser dependency at all. An earlier
  pass of this implementation briefly moved the data file to JSON instead
  to sidestep that dependency question — reverted once `uv` was adopted,
  since YAML's comments and block-scalar prose are worth the one added
  dependency for a file the operator will hand-edit often.
- **`uv.lock` could not be generated in the sandbox this was built in** —
  its network egress is restricted to an internal allowlist that doesn't
  include PyPI. `pyproject.toml` is in place and correct; run `uv lock`
  (or just `uv sync`, which will lock-and-sync in one step) once on a
  machine with normal network access and commit the resulting `uv.lock`
  for reproducible CI installs. Until that's committed, CI's `uv sync`
  step will still work (it resolves on the fly), just without a pinned
  lockfile.
- **Nav placement (§8) was resolved**, not left open: `/career-journey/`
  is out of primary nav, same tier as Contact, reachable via the new link
  card on `/about/` and by direct/shared URL. Revisit if that reads as
  too buried once real content is in place.
- **`CJ_LAYOUTS`** (the Tier-2 recipe→region-name table from §4) lives once
  in `scripts/build.py` and is imported by `scripts/lint.py` (`from build
  import CJ_LAYOUTS, ...` — safe because `scripts/lint.py` runs with
  `scripts/` on `sys.path[0]`, and `build.py`'s side effects are guarded
  behind `if __name__ == "__main__"`), rather than duplicated — keeps the
  recipe list and its validation in sync by construction.
- **All slide content and images in `data/career-journey.yaml` /
  `assets/career-journey/` are placeholders**, not the real deck — see the
  file header comment. Replace before this page ships live; do not treat
  the current content as reviewed copy.
