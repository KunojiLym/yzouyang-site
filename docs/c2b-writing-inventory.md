# C2b — writing inventory (deferred)

Phase 1 does **not** scrape or import writing. This doc is the checklist for a later personal-content + site change.

## Goal

One governed catalog (likely `personal-content` `writing.yaml`) covering every PUBLIC piece, with dedupe across republications; site `/writing` (or `/blog`) lists from export.

## Sources

| Source | What to inventory | Channel tag |
|---|---|---|
| WordPress Blog | Posts on yzouyang.com | `wordpress` |
| Medium | `@kunojilym` posts / lists | `medium` |
| LinkedIn articles | Standalone article URLs | `linkedin_article` |
| LinkedIn newsletter | Each edition | `linkedin_newsletter` |

Seed hubs: [WP blog](https://www.yzouyang.com/blog/), [Medium](https://medium.com/@kunojilym), [LinkedIn](https://www.linkedin.com/in/yzouyang/).

## Steps

1. **Inventory** — YAML stub: title, URL, published date, channel, series/tags, PUBLIC visibility.
2. **Dedupe** — same essay on Medium + WP + LinkedIn → one canonical URL + `aliases` / syndication links.
3. **SoT** — land in `personal-content`; export PUBLIC rows only.
4. **Site** — `/writing` lists from export; Pagefind indexes titles/summaries; bodies may stay off-site until import is worth it.
5. **C3/C4** — feed Career KB `writing` / `content_impact` and newsletter freshness alerts.

Prefer LinkedIn data export / manual CSV / curated YAML over fragile scraping. Phase 1 must not depend on LinkedIn at build time.
