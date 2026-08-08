# DIY pageview tracking (supplement)

First-party beacon + collector. Runs **alongside** Jetpack Stats (and optional GA4). No cookies; DNT honored by default.

## Client

`src/track.js` is copied into `dist/` when `analytics.diy.enabled` is true. It POSTs a small JSON pageview to `analytics.diy.collect_url`.

Payload fields: `t`, `v`, `ts`, `path`, `host`, `title`, `ref` (referrer **hostname** only), `lang`, `tz`, `vw`, `vh`.

## Local collector (smoke / Homelab)

```bash
python scripts/diy_collect.py --port 8787 --out data/diy-events.ndjson
# in data/site.json set collect_url to http://127.0.0.1:8787/collect
python scripts/build.py
python -m http.server -d dist 8080
```

Events append as NDJSON — later load into DuckDB/Grafana (C3 hook).

## Cloudflare Worker (public preview / production)

```bash
cd collect
npx wrangler deploy
# set analytics.diy.collect_url to https://<worker>.workers.dev/collect
```

Optional bindings (uncomment in `wrangler.toml`):

- **Analytics Engine** `EVENTS` — cheap aggregates
- **R2** `EVENTS_BUCKET` — raw JSON objects per hit

Tighten `ALLOWED_ORIGINS` before apex cutover.

## Config (`data/site.json`)

```json
"diy": {
  "enabled": true,
  "collect_url": "https://yzouyang-diy-collect.<account>.workers.dev/collect",
  "honor_dnt": true
}
```

Empty `collect_url` with `enabled: true` ships the script but sends nothing (safe default until the Worker URL is set).
