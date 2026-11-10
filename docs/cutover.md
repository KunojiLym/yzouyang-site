# Operator cutover checklist

**Gate:** only after Phase 1 **UAT / preview** parity is signed off (see [preview-uat.md](preview-uat.md)). Until then, WordPress on Bluehost stays authoritative on the apex.

**Full replacement checklist:** Homelab [docs/runbooks/yzouyang-wordpress-replacement.md](https://github.com/KunojiLym/Homelab/blob/main/docs/runbooks/yzouyang-wordpress-replacement.md).

## Before DNS (C2a)

- [ ] Offline `python scripts/preview.py` looks right
- [ ] `python scripts/lint.py`, `python scripts/test_site_build.py`, `python scripts/verify_migration.py`, and `npm run test:e2e` green
- [ ] Downloaded preview artifact / local UAT signed off; hosted UAT needs a separate destination
- [ ] Release guard applied to main and existing UAT branch; obsolete deploy runs/environment retired
- [ ] `github-pages` environment permits main only, with intended independent approval
- [ ] Main Pages release matches the reviewed source and `release.json` file hashes
- [ ] Preview serves `/`, `/systems/`, `/credentials/`, `/notes/` from PUBLIC export
- [ ] Notes **Reading mode** signed off: covers, full-date bylines, prose measure, wrapped code, blockquotes (see [design-system.md](design-system.md#reading-mode-notes-only))
- [ ] Legacy stubs redirect as documented: `/about/`, `/contact/`, `/career-journey/` → `/`; `/portfolio/`, `/work/`, `/systems/catalogue/` → `/systems/`; `/perspectives/`, `/blog/` → `/notes/`
- [ ] Pagefind indexes systems, credentials, and notes (titles + bodies)
- [ ] Footer **Blog** → `/notes/` (on-site); Medium / LinkedIn still external
- [ ] Legacy Bitly shorts (`bit.ly/3GGyiXF`, `bit.ly/4m4fqki`) repointed to `/systems/` and `/credentials/`
- [ ] Smoke all 18 WP slug stubs → matching `/notes/note-*/` pages using `url-map.json` (see [c2b-writing-inventory.md](c2b-writing-inventory.md))
- [ ] On the target host, verify canonical/OG/Article URLs, titles, article bodies, assets, sitemap, robots policy, HTTPS and real HTTP 404; a local stub check alone is insufficient
- [ ] No work/university emails on public pages

## Cutover

1. Point DNS / CDN for apex + `www` to the static host (GitHub Pages custom domain or Cloudflare).
2. WP 301 non-blog routes to static where not already stubbed.
3. Medium and LinkedIn stay live — do not redirect or unpublish.
4. Smoke apex `/`, `/systems/`, `/credentials/`, `/notes/`, Bitly destinations.

## Decommission WP (C2c)

After redirect smoke passes:

1. Confirm each WP post permalink lands on the correct on-site note.
2. Cancel Bluehost or keep redirect-only for a TTL.
3. Do **not** take down Medium or LinkedIn.

## Rollback

Repoint DNS to Bluehost / restore WP as primary; static preview can remain for iteration.

## Draft preview (C2e)

Local only — never in public CI:

```bash
python scripts/preview.py --include-drafts ../personal-content
```

Draft rows use `visibility_policy: PRIVATE_ONLY` in `writing.yaml`. The builder adds a **Draft preview** kicker on those panels, sets `<meta name="robots" content="noindex">`, and marks `<html data-draft-preview="1">`.

UAT branch pushes generate a downloadable noindex artifact. They must not publish to the release Pages destination. Private drafts remain local; a noindex directive is not an access control.

## Automated migration checks

After `python scripts/build.py`:

```bash
python scripts/verify_migration.py
```

Confirms 18 PUBLIC essays, no `wp-content` hotlinks in export bodies, vendored `assets/notes/`, WP slug stubs → `/notes/note-*/`, and footer Blog → `/notes/`. Also run `python scripts/test_article_routes.py` for metadata, sitemap and exact redirect targets. These are artifact checks; they do not prove the hosting/CDN/TLS behavior after deployment.
