# Graph Report - yzouyang-site  (2026-09-16)

## Corpus Check
- 57 files · ~2,210,075 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 639 nodes · 1223 edges · 66 communities (44 shown, 22 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 132 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `41c24491`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Career Journey 2025 Deck Slides
- build.py
- lint-build Job
- scripts
- career-journey.yaml slide data
- Data Platform Project Portfolio
- server-lifecycle.mjs
- rules
- serve-dist.mjs
- check_docs_links.py
- career-journey.js
- graphify Knowledge Graph
- diy_collect.py
- preview.py
- qa-compare-wp.mjs
- qa-screenshot.mjs
- yzouyang-site
- worker.js
- Operator Cutover Checklist
- qa-refs.mjs
- Multi-Cloud Platform Experience
- Design System CI Gates
- compose_home_selected_row
- C2b Writing Inventory (Deferred)
- Tier 2 Grid Recipe Library
- UAT Sign-Off Gate
- NTFY_TOPIC_URL
- Draft PR Policy
- check_token_drift.py
- test_site_build.py
- track.js
- a11y.spec.mjs
- usability.spec.mjs
- visual.spec.mjs
- Draft PR Only Policy
- pre-commit
- playwright.config.mjs
- Data & AI Platform Leader
- Agent Fine-Grained PAT
- main Branch Protection
- Writing Dedupe and Syndication
- Dossier Content Hierarchy
- scripts/diy_collect.py
- /contact/ to /#contact Redirect
- data/site.json
- longform.css Breakpoint Convergence to 900px
- Font Size Token Mapping
- No Secrets Policy
- yzouyang-site
- docs/cutover.md
- docs/preview-uat.md
- build_perspectives
- chrome.js
- theme.spec.mjs
- manifest.json
- footer_html
- _map_record_lookup
- verify_migration.py
- with_base
- main
- esc
- build_home
- extracted-code/make_repos/rux3vr/manifest.json
- .figma-make-import/make_repos/rux3vr/manifest.json
- longform_page

## God Nodes (most connected - your core abstractions)
1. `Career Journey 2025 Deck Slides` - 80 edges
2. `Employer Brand Logos` - 80 edges
3. `esc()` - 65 edges
4. `with_base()` - 28 edges
5. `main()` - 21 edges
6. `main()` - 20 edges
7. `Cloud Platform Certifications` - 20 edges
8. `_markdown_to_html()` - 15 edges
9. `build_perspectives()` - 15 edges
10. `layout()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `Professional Profile Photo` --conceptually_related_to--> `yzouyang-site`  [INFERRED]
  assets/profile.jpg → README.md
- `data/export_public.json` --semantically_similar_to--> `data/export_public.json`  [INFERRED] [semantically similar]
  docs/site-builder.md → README.md
- `scripts/preview.py` --semantically_similar_to--> `scripts/preview.py`  [INFERRED] [semantically similar]
  docs/preview-uat.md → README.md
- `scripts/build.py` --semantically_similar_to--> `scripts/build.py`  [INFERRED] [semantically similar]
  docs/site-builder.md → README.md
- `PyYAML uv Dependency` --semantically_similar_to--> `uv Dependency Management`  [INFERRED] [semantically similar]
  docs/career-journey-native-plan.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Site Build Pipeline** — readme_scripts_lint, readme_scripts_build, readme_scripts_test_site_build, github_workflows_ci_pagefind [INFERRED 0.85]
- **Analytics Providers** — readme_analytics, readme_jetpack_stats, readme_ga4, readme_diy_tracking [EXTRACTED 1.00]
- **Agent PR Guardrails** — readme_draft_pr_policy, github_pull_request_template_draft_pr, github_pull_request_template_no_secrets, github_pull_request_template_human_merge [INFERRED 0.85]
- **Career Journey Four-Act Narrative Placeholders** — assets_career_journey_act1_first_role, assets_career_journey_act2_bootcamp_1, assets_career_journey_act2_bootcamp_2, assets_career_journey_act3_project_1, assets_career_journey_act3_project_2, assets_career_journey_act3_project_3, assets_career_journey_act4_overlay_bg [INFERRED 0.85]
- **Multi-Cloud Platform Credentials and Logos** — assets_career_journey_logo_aws, assets_career_journey_logo_azure, assets_career_journey_badge_gcp_ml_engineer, assets_career_journey_concept_multi_cloud [INFERRED 0.85]
- **Career Journey Employer Brand Assets** — assets_career_journey_logo_prudential, assets_career_journey_logo_stb [INFERRED 0.75]
- **Career Journey 2025 Deck Slide Images** — assets_career_journey_deck_image_1_1, assets_career_journey_deck_image_10_1, assets_career_journey_deck_image_13_1, assets_career_journey_deck_image_14_1, assets_career_journey_deck_image_15_1, assets_career_journey_deck_image_16_1, assets_career_journey_deck_image_16_2, assets_career_journey_deck_image_17_1, assets_career_journey_deck_image_17_2, assets_career_journey_deck_image_17_3, assets_career_journey_deck_image_17_4, assets_career_journey_deck_image_18_1, assets_career_journey_deck_image_18_2, assets_career_journey_deck_image_18_3, assets_career_journey_deck_image_18_4, assets_career_journey_deck_image_18_5, assets_career_journey_deck_image_18_6, assets_career_journey_deck_image_18_7, assets_career_journey_deck_image_19_1, assets_career_journey_deck_image_19_2, assets_career_journey_deck_image_19_3, assets_career_journey_deck_image_19_4, assets_career_journey_deck_image_2_1, assets_career_journey_deck_image_2_2, assets_career_journey_deck_image_2_3, assets_career_journey_deck_image_2_4, assets_career_journey_deck_image_2_5, assets_career_journey_deck_image_2_6, assets_career_journey_deck_image_20_1, assets_career_journey_deck_image_20_2, assets_career_journey_deck_image_20_3, assets_career_journey_deck_image_20_4, assets_career_journey_deck_image_22_1, assets_career_journey_deck_image_23_1, assets_career_journey_deck_image_23_2, assets_career_journey_deck_image_23_3, assets_career_journey_deck_image_23_4, assets_career_journey_deck_image_24_1, assets_career_journey_deck_image_24_2, assets_career_journey_deck_image_24_3, assets_career_journey_deck_image_24_4, assets_career_journey_deck_image_24_5, assets_career_journey_deck_image_24_6, assets_career_journey_deck_image_25_1, assets_career_journey_deck_image_25_2, assets_career_journey_deck_image_26_1, assets_career_journey_deck_image_26_2, assets_career_journey_deck_image_3_1, assets_career_journey_deck_image_3_2, assets_career_journey_deck_image_3_3, assets_career_journey_deck_image_3_4, assets_career_journey_deck_image_32_1, assets_career_journey_deck_image_33_1, assets_career_journey_deck_image_33_2, assets_career_journey_deck_image_33_3, assets_career_journey_deck_image_33_4, assets_career_journey_deck_image_33_5, assets_career_journey_deck_image_33_6, assets_career_journey_deck_image_33_7, assets_career_journey_deck_image_4_1, assets_career_journey_deck_image_4_10, assets_career_journey_deck_image_4_11, assets_career_journey_deck_image_4_12, assets_career_journey_deck_image_4_13, assets_career_journey_deck_image_4_14, assets_career_journey_deck_image_4_2, assets_career_journey_deck_image_4_3, assets_career_journey_deck_image_4_4, assets_career_journey_deck_image_4_5, assets_career_journey_deck_image_4_6, assets_career_journey_deck_image_4_7, assets_career_journey_deck_image_4_8, assets_career_journey_deck_image_4_9, assets_career_journey_deck_image_5_1, assets_career_journey_deck_image_5_2, assets_career_journey_deck_image_5_3, assets_career_journey_deck_image_5_4, assets_career_journey_deck_image_7_1, assets_career_journey_deck_image_8_1, assets_career_journey_deck_image_9_1 [INFERRED 0.85]
- **Cloud Certification Badges in Deck** — assets_career_journey_deck_image_33_1, assets_career_journey_deck_image_33_7, assets_career_journey_deck_image_18_4, assets_career_journey_deck_image_33_4, assets_career_journey_deck_image_33_5, assets_career_journey_deck_image_16_2, assets_career_journey_deck_image_18_1, assets_career_journey_deck_image_18_3, assets_career_journey_deck_image_18_7, assets_career_journey_deck_image_33_6, assets_career_journey_deck_image_18_6, assets_career_journey_deck_image_33_3, assets_career_journey_deck_image_17_2, assets_career_journey_deck_image_33_2, assets_career_journey_deck_image_17_3, assets_career_journey_deck_image_17_4, assets_career_journey_deck_image_18_2, assets_career_journey_deck_image_17_1, assets_career_journey_deck_image_18_5, assets_career_journey_deck_image_16_1 [INFERRED 0.85]
- **Employer Logo Slides in Deck** — assets_career_journey_deck_image_19_3, assets_career_journey_deck_image_19_4, assets_career_journey_deck_image_19_2, assets_career_journey_deck_image_19_1 [INFERRED 0.85]
- **Technology Stack Logo Slides** — assets_career_journey_deck_image_4_11, assets_career_journey_deck_image_4_13, assets_career_journey_deck_image_4_2, assets_career_journey_deck_image_4_5, assets_career_journey_deck_image_4_7, assets_career_journey_deck_image_4_4, assets_career_journey_deck_image_4_8, assets_career_journey_deck_image_4_10, assets_career_journey_deck_image_4_3, assets_career_journey_deck_image_4_9, assets_career_journey_deck_image_4_6, assets_career_journey_deck_image_4_12 [INFERRED 0.85]
- **Career Journey Native Stack** — data_career_journey_slide_data, data_career_journey_build_career_journey, docs_career_journey_native_plan_three_tier_schema, src_styles_readme_career_journey_css [INFERRED 0.85]
- **Phase 1 Cutover Gates** — docs_preview_uat_preview_workflow, docs_cutover_operator_checklist, docs_redirects_wp_static_map, docs_cutover_dns_static_host [INFERRED 0.85]
- **CSS Token Enforcement** — src_styles_readme_tokens_css, src_styles_readme_stylelint_enforcement, src_styles_readme_check_token_drift, docs_design_system_ci_gates [INFERRED 0.85]

## Communities (66 total, 22 thin omitted)

### Community 0 - "Career Journey 2025 Deck Slides"
Cohesion: 0.07
Nodes (85): Career Journey 2025 Deck Slides, Cloud Platform Certifications, Employer Brand Logos, Online Learning Platforms, Data Engineering Tech Stack, Diagram showing career journey stages and progression, Diagram illustrating career journey concept, Diagram illustrating career journey concept (+77 more)

### Community 1 - "build.py"
Cohesion: 0.10
Nodes (37): _collect_expand_body(), _decode_fragment(), _draft_preview_mode(), _education_is_ongoing(), _env_flag(), _extract_inarticle_toc_tree(), _extract_toc_anchor_map(), _heading_anchor_id() (+29 more)

### Community 2 - "lint-build Job"
Cohesion: 0.06
Nodes (35): lint-build Status Check, personal-content writing.yaml Catalog, PyYAML uv Dependency, Cloudflare Worker Collector, DIY First-Party Pageview Beacon, src/track.js Client Beacon, scripts/preview.py, data/export_public.json (+27 more)

### Community 3 - "scripts"
Cohesion: 0.06
Nodes (31): @axe-core/playwright, husky, lint-staged, devDependencies, @axe-core/playwright, husky, lint-staged, @playwright/test (+23 more)

### Community 4 - "career-journey.yaml slide data"
Cohesion: 0.09
Nodes (23): build_career_journey(), Career Journey Page (/career-journey/), Career Transition Story, Figma Career Journey 2025 Deck, LinkedIn Connect Slide, Metis Data Science Bootcamp, Murdoch University BIS Degree, Native HTML Slide Rendering (+15 more)

### Community 5 - "Data Platform Project Portfolio"
Cohesion: 0.10
Nodes (22): Act 1 First Data Role Placeholder, Act 2 Bootcamp Cohort Placeholder, Act 2 Bootcamp Project Demo Placeholder, Act 3 Platform Project A Placeholder, Act 3 Platform Project B Placeholder, Act 3 Platform Project C Placeholder, Act 4 Leadership Milestone Placeholder, Compass on Financial Chart Photo (+14 more)

### Community 6 - "server-lifecycle.mjs"
Cohesion: 0.17
Nodes (18): globalSetup(), globalTeardown(), BASE_URL, HOST, isReady(), log(), PORT, processExists() (+10 more)

### Community 7 - "rules"
Cohesion: 0.15
Nodes (12): dist/**/*.css, stylelint-config-standard, stylelint-declaration-strict-value, extends, ignoreFiles, plugins, rules, custom-property-pattern (+4 more)

### Community 8 - "serve-dist.mjs"
Cohesion: 0.27
Nodes (9): fileFor(), log(), port, root, send(), server, shutdown(), shutdownTimeoutMs (+1 more)

### Community 9 - "check_docs_links.py"
Cohesion: 0.50
Nodes (8): check_links(), check_stale(), iter_markdown_files(), main(), parse_front_matter(), date, Path, repo_root()

### Community 10 - "career-journey.js"
Cohesion: 0.50
Nodes (7): clampIndex(), goTo(), nearestIndex(), requestActiveFromScroll(), revealStep(), setActive(), slideLeft()

### Community 11 - "graphify Knowledge Graph"
Cohesion: 0.29
Nodes (7): GRAPH_REPORT.md, graphify explain, graphify Knowledge Graph, graphify path, graphify query, graphify update, graphify-out/wiki/index.md

### Community 12 - "diy_collect.py"
Cohesion: 0.33
Nodes (5): main(), make_handler(), Path, Coerce *value* to int, returning *default* for non-numeric input., _to_int()

### Community 13 - "preview.py"
Cohesion: 0.60
Nodes (5): main(), Windows CreateProcess cannot run bare 'npx' (needs npx.cmd)., resolve_npx(), run(), run_pagefind()

### Community 14 - "qa-compare-wp.mjs"
Cohesion: 0.33
Nodes (4): __dirname, OUT, pairs, report

### Community 15 - "qa-screenshot.mjs"
Cohesion: 0.33
Nodes (4): __dirname, input, OUT, pages

### Community 16 - "yzouyang-site"
Cohesion: 0.40
Nodes (5): Professional Headshot Portrait, Professional Profile Photo, Site Routes, WordPress Migration Phase 1, yzouyang-site

### Community 17 - "worker.js"
Cohesion: 0.70
Nodes (4): cleanEvent(), corsHeaders(), fetch(), toInt()

### Community 18 - "Operator Cutover Checklist"
Cohesion: 0.40
Nodes (5): Pagefind Writing Index (Deferred), DNS Cutover to Static Host, Operator Cutover Checklist, WordPress on Bluehost (Pre-Cutover), WordPress to Static Redirect Map

### Community 19 - "qa-refs.mjs"
Cohesion: 0.40
Nodes (4): __dirname, OUT, report, sites

### Community 20 - "Multi-Cloud Platform Experience"
Cohesion: 0.50
Nodes (4): Google Cloud Certified Professional Machine Learning Engineer Badge, Multi-Cloud Platform Experience, Amazon Web Services Logo, Microsoft Azure Logo

### Community 21 - "Design System CI Gates"
Cohesion: 0.50
Nodes (4): Design System CI Gates, Stylelint Token Enforcement, scripts/check_token_drift.py, Stylelint Strict Value Enforcement

### Community 22 - "compose_home_selected_row"
Cohesion: 0.33
Nodes (8): case_copy_by_id(), compose_home_selected_row(), _home_featured_systems_html(), Beats live in enterprise_copy / project_copy, keyed by stable heading id., Home titles/tools compose from shared case copy; beats are not re-authored., fail(), main(), validate_public_visibility()

### Community 23 - "C2b Writing Inventory (Deferred)"
Cohesion: 0.67
Nodes (3): C2b Writing Inventory (Deferred), Blog Permalinks Stay on WordPress, Information Architecture Rules

### Community 24 - "Tier 2 Grid Recipe Library"
Cohesion: 0.67
Nodes (3): CJ_LAYOUTS Recipe Table, Tier 2 Grid Recipe Library, career-journey.css Module

### Community 25 - "UAT Sign-Off Gate"
Cohesion: 0.67
Nodes (3): UAT Sign-Off Gate, Preview & UAT Workflow, uat Branch GitHub Pages Deploy

### Community 26 - "NTFY_TOPIC_URL"
Cohesion: 0.67
Nodes (3): NTFY CI Failure Notifications, notify-ntfy Job, NTFY_TOPIC_URL

### Community 27 - "Draft PR Policy"
Cohesion: 0.67
Nodes (3): Draft PR Policy, Human Merge Gate, Draft PR Only Policy

### Community 29 - "test_site_build.py"
Cohesion: 0.15
Nodes (30): figma_embed_html(), _inarticle_toc_attr(), _inarticle_toc_from_md(), normalize_base(), _note_asset_href(), _note_index_title(), Match an export enterprise row to overlay copy keyed by heading_id., Normalize export `writing` records for site builders. (+22 more)

### Community 32 - "usability.spec.mjs"
Cohesion: 0.20
Nodes (4): escapeRegExp(), expectedRedirectUrl(), LIVE_ROUTES, REDIRECTS

### Community 52 - "build_perspectives"
Cohesion: 0.27
Nodes (10): _append_note_panel(), build_perspectives(), library_panel_html(), _note_category(), _note_date_sort_key(), _note_index_entry(), _note_series(), _notes_category_order() (+2 more)

### Community 53 - "chrome.js"
Cohesion: 0.23
Nodes (16): applyReadingSize(), applyTheme(), decorateSearchResultRow(), decorateSearchResults(), getPreferredReadingSize(), getPreferredTheme(), initChrome(), initHashRedirects() (+8 more)

### Community 55 - "manifest.json"
Cohesion: 0.33
Nodes (5): commit_sha, lfs_objects, packs, refs, version

### Community 56 - "footer_html"
Cohesion: 0.18
Nodes (12): footer_html(), _footer_links_html(), _library_index_header_html(), library_index_html(), _library_index_icon_svg(), _library_index_rail_html(), library_shell(), _nav_anchor_html() (+4 more)

### Community 57 - "_map_record_lookup"
Cohesion: 0.12
Nodes (23): _domain_target_label(), _domain_target_section(), _home_slide_link(), _internal_route_link(), _map_detail_panels_html(), _map_detail_panels_only_html(), _map_detail_record_item(), _map_domain_index_html() (+15 more)

### Community 59 - "verify_migration.py"
Cohesion: 0.47
Nodes (10): check_export_writing(), check_site_json(), check_vendored_assets(), check_wp_stubs(), fail(), load_export(), main(), ok() (+2 more)

### Community 60 - "with_base"
Cohesion: 0.12
Nodes (24): _compose_current_index_rows(), _credentials_teaser_html(), _current_index_html(), _current_index_link_html(), _current_index_topic(), _current_index_topic_label(), _footer_meta_html(), _home_featured_notes_html() (+16 more)

### Community 61 - "main"
Cohesion: 0.14
Nodes (19): analytics_body(), analytics_head(), article_json_ld(), assemble_styles(), canonical_url(), _header_search_html(), layout(), load_json() (+11 more)

### Community 62 - "esc"
Cohesion: 0.14
Nodes (28): _beat_value_html(), build_credentials(), build_portfolio(), build_systems(), build_systems_catalogue(), case_beats_html(), _case_tools_html(), _cert_card_html() (+20 more)

### Community 63 - "build_home"
Cohesion: 0.22
Nodes (11): _about_data(), _atmosphere_figure_html(), _atmosphere_slot(), build_home(), _home_competencies_html(), _home_competency_item_html(), _home_context_meta_html(), _home_entrance_actions_html() (+3 more)

### Community 64 - "extracted-code/make_repos/rux3vr/manifest.json"
Cohesion: 0.33
Nodes (5): commit_sha, lfs_objects, packs, refs, version

### Community 65 - ".figma-make-import/make_repos/rux3vr/manifest.json"
Cohesion: 0.33
Nodes (5): commit_sha, lfs_objects, packs, refs, version

### Community 66 - "longform_page"
Cohesion: 0.50
Nodes (4): longform_page(), Render on-this-page nav. entries: {id, label, children?} trees., Legacy long-page shell (redirect stubs only)., toc_html()

## Knowledge Gaps
- **143 isolated node(s):** `version`, `commit_sha`, `refs`, `packs`, `lfs_objects` (+138 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `esc()` connect `esc` to `build.py`, `test_site_build.py`, `build_perspectives`, `compose_home_selected_row`, `footer_html`, `_map_record_lookup`, `with_base`, `main`, `build_home`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **What connects `version`, `commit_sha`, `refs` to the rest of the system?**
  _143 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Career Journey 2025 Deck Slides` be split into smaller, more focused modules?**
  _Cohesion score 0.07086834733893557 - nodes in this community are weakly interconnected._
- **Should `build.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09743589743589744 - nodes in this community are weakly interconnected._
- **Should `lint-build Job` be split into smaller, more focused modules?**
  _Cohesion score 0.06050420168067227 - nodes in this community are weakly interconnected._
- **Should `scripts` be split into smaller, more focused modules?**
  _Cohesion score 0.0625 - nodes in this community are weakly interconnected._
- **Should `career-journey.yaml slide data` be split into smaller, more focused modules?**
  _Cohesion score 0.09486166007905138 - nodes in this community are weakly interconnected._