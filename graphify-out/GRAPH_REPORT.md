# Graph Report - d:\Git Repositories\yzouyang-site  (2026-08-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 327 nodes · 315 edges · 132 communities (20 shown, 112 thin omitted)
- Extraction: 98% EXTRACTED · 1% INFERRED · 1% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ef46633f`
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
- Community 22
- Community 23
- Community 24
- Community 25
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 129
- Community 130
- Community 131

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
- `README` --references--> `Cutover Documentation`  [EXTRACTED]
  README.md → docs/cutover.md
- `README` --references--> `Design System Documentation`  [EXTRACTED]
  README.md → docs/design-system.md
- `README` --references--> `DIY Tracking Documentation`  [EXTRACTED]
  README.md → docs/diy-tracking.md
- `README` --references--> `Site Builder Documentation`  [EXTRACTED]
  README.md → docs/site-builder.md
- `extends` --extends--> `stylelint-config-standard`  [EXTRACTED]
  .stylelintrc.json → package.json

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Graph Query and Navigation Commands** — query, path, explain [EXTRACTED 0.90]
- **Documentation for Site Build Process** — readme, docs_site-builder, docs_preview-uat, docs_cutover [EXTRACTED 0.90]
- **Career Skill Summary Flow** — transferable_skills, what_learn, connect [EXTRACTED 0.90]
- **Career Journey Frontend Component Stack** — career_journey_page, css_modules, js_modules [EXTRACTED 0.90]
- **Content Pipeline Validation Flow** — career_journey_data_structure, career_journey_validation_script, about_page [EXTRACTED 0.85]
- **Core Professional Narrative Flow (Dossier Structure)** — design_system, visual_tokens [EXTRACTED 0.90]
- **WordPress redirect paths and destinations** — docs_redirects [EXTRACTED 0.90]
- **CSS Tokenization Scope and Enforcement** — README, spacing_drift_table, radius_drift_table, breakpoints_table [EXTRACTED 0.95]

## Communities (132 total, 112 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (44): analytics_body(), analytics_head(), assemble_styles(), build_about(), build_career_journey(), build_contact_redirect(), build_credentials(), build_home() (+36 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (27): @axe-core/playwright, husky, lint-staged, devDependencies, @axe-core/playwright, husky, lint-staged, @playwright/test (+19 more)

### Community 2 - "Community 2"
Cohesion: 0.17
Nodes (18): globalSetup(), globalTeardown(), BASE_URL, HOST, isReady(), log(), PORT, processExists() (+10 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (14): stylelint-config-standard, stylelint-declaration-strict-value, dist/**/*.css, stylelint-config-standard, stylelint-declaration-strict-value, extends, ignoreFiles, plugins (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.17
Nodes (12): Cutover Documentation, Public JSON Data Export, Cutover Documentation, Design System Documentation, DIY Tracking Documentation, Preview/UAT Documentation, Site Builder Documentation, E2E Test Script (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.27
Nodes (9): fileFor(), log(), port, root, send(), server, shutdown(), shutdownTimeoutMs (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.50
Nodes (7): clampIndex(), goTo(), nearestIndex(), requestActiveFromScroll(), revealStep(), setActive(), slideLeft()

### Community 7 - "Community 7"
Cohesion: 0.33
Nodes (7): /about/ page content update, Career Journey Data Structure (JSON/Schema), Career Journey Page Component/Route, Career Journey Content Validation Script, New CSS Modules (Styling), Dependency Management Update (uv/pyproject.toml), New JavaScript Modules (Interactivity)

### Community 8 - "Community 8"
Cohesion: 0.33
Nodes (5): main(), make_handler(), Path, Coerce *value* to int, returning *default* for non-numeric input., _to_int()

### Community 9 - "Community 9"
Cohesion: 0.53
Nodes (6): AGENTS.md Document, graphify explain command, Knowledge Graph Output Directory, graphify path command, graphify query command, wiki/index.md file

### Community 10 - "Community 10"
Cohesion: 0.60
Nodes (5): main(), Windows CreateProcess cannot run bare 'npx' (needs npx.cmd)., resolve_npx(), run(), run_pagefind()

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (4): __dirname, OUT, pairs, report

### Community 12 - "Community 12"
Cohesion: 0.33
Nodes (4): __dirname, input, OUT, pages

### Community 13 - "Community 13"
Cohesion: 0.70
Nodes (4): cleanEvent(), corsHeaders(), fetch(), toInt()

### Community 14 - "Community 14"
Cohesion: 0.40
Nodes (4): __dirname, OUT, report, sites

### Community 15 - "Community 15"
Cohesion: 1.00
Nodes (3): fail(), main(), validate_public_visibility()

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (3): Diagram showing career journey stages and progression, Diagram showing career journey stages and progression, Book cover: The Constitution of Europe by Stephen Weathrill

### Community 17 - "Community 17"
Cohesion: 0.67
Nodes (3): Let's Connect Slide, Transferable Skills Section, What You Can Learn Section

## Ambiguous Edges - Review These
- `Diagram showing career journey stages and progression` → `Book cover: The Constitution of Europe by Stephen Weathrill`  [AMBIGUOUS]
  N/A · relation: conceptually_related_to
- `Diagram showing career journey stages and progression` → `Book cover: The Constitution of Europe by Stephen Weathrill`  [AMBIGUOUS]
  N/A · relation: conceptually_related_to

## Knowledge Gaps
- **155 isolated node(s):** `scale-unlimited/declaration-strict-value`, `custom-property-pattern`, `selector-class-pattern`, `no-descending-specificity`, `font-family-name-quotes` (+150 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **112 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Diagram showing career journey stages and progression` and `Book cover: The Constitution of Europe by Stephen Weathrill`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Diagram showing career journey stages and progression` and `Book cover: The Constitution of Europe by Stephen Weathrill`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `devDependencies` connect `Community 1` to `Community 3`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **What connects `scale-unlimited/declaration-strict-value`, `custom-property-pattern`, `selector-class-pattern` to the rest of the system?**
  _155 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.11400966183574879 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._