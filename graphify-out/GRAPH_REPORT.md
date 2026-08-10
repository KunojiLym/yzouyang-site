# Graph Report - .  (2026-08-10)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 193 nodes · 285 edges · 25 communities (16 shown, 9 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `67af35a9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 23

## God Nodes (most connected - your core abstractions)
1. `esc()` - 20 edges
2. `main()` - 14 edges
3. `with_base()` - 13 edges
4. `scripts` - 10 edges
5. `build_credentials()` - 9 edges
6. `layout()` - 8 edges
7. `build_about()` - 8 edges
8. `stopE2EServer()` - 8 edges
9. `build_portfolio()` - 7 edges
10. `startE2EServer()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `extends` --extends--> `stylelint-config-standard`  [EXTRACTED]
  .stylelintrc.json → package.json
- `plugins` --extends--> `stylelint-declaration-strict-value`  [EXTRACTED]
  .stylelintrc.json → package.json
- `globalSetup()` --calls--> `startE2EServer()`  [EXTRACTED]
  tests/e2e/global-setup.mjs → tests/e2e/server-lifecycle.mjs
- `globalTeardown()` --calls--> `stopE2EServer()`  [EXTRACTED]
  tests/e2e/global-teardown.mjs → tests/e2e/server-lifecycle.mjs

## Import Cycles
- None detected.

## Communities (25 total, 9 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (44): analytics_body(), analytics_head(), assemble_styles(), build_about(), build_career_journey(), build_contact_redirect(), build_credentials(), build_home() (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.17
Nodes (18): globalSetup(), globalTeardown(), BASE_URL, HOST, isReady(), log(), PORT, processExists() (+10 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (17): @axe-core/playwright, husky, lint-staged, devDependencies, @axe-core/playwright, husky, lint-staged, @playwright/test (+9 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (14): stylelint-config-standard, stylelint-declaration-strict-value, dist/**/*.css, stylelint-config-standard, stylelint-declaration-strict-value, extends, ignoreFiles, plugins (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.20
Nodes (10): scripts, lint:css, lint:token-drift, prepare, qa:shots, serve:dist, test:a11y, test:e2e (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (9): fileFor(), log(), port, root, send(), server, shutdown(), shutdownTimeoutMs (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.50
Nodes (7): clampIndex(), goTo(), nearestIndex(), requestActiveFromScroll(), revealStep(), setActive(), slideLeft()

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (5): main(), make_handler(), Path, Coerce *value* to int, returning *default* for non-numeric input., _to_int()

### Community 8 - "Community 8"
Cohesion: 0.60
Nodes (5): main(), Windows CreateProcess cannot run bare 'npx' (needs npx.cmd)., resolve_npx(), run(), run_pagefind()

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (4): __dirname, OUT, pairs, report

### Community 10 - "Community 10"
Cohesion: 0.33
Nodes (4): __dirname, input, OUT, pages

### Community 11 - "Community 11"
Cohesion: 0.70
Nodes (4): cleanEvent(), corsHeaders(), fetch(), toInt()

### Community 12 - "Community 12"
Cohesion: 0.40
Nodes (4): __dirname, OUT, report, sites

### Community 13 - "Community 13"
Cohesion: 1.00
Nodes (3): fail(), main(), validate_public_visibility()

## Knowledge Gaps
- **51 isolated node(s):** `scale-unlimited/declaration-strict-value`, `custom-property-pattern`, `selector-class-pattern`, `no-descending-specificity`, `font-family-name-quotes` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `devDependencies` connect `Community 2` to `Community 3`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `scripts` connect `Community 4` to `Community 2`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **What connects `scale-unlimited/declaration-strict-value`, `custom-property-pattern`, `selector-class-pattern` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.11400966183574879 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._