# Operator cutover checklist

**Gate:** only after Phase 1 **UAT / preview** parity is signed off (see [preview-uat.md](preview-uat.md)). Until then, WordPress on Bluehost stays authoritative on the apex.

**Full replacement checklist:** Homelab [docs/runbooks/yzouyang-wordpress-replacement.md](https://github.com/KunojiLym/Homelab/blob/main/docs/runbooks/yzouyang-wordpress-replacement.md).

## Before DNS (C2a)

- [ ] Offline `python scripts/preview.py` looks right
- [ ] `python scripts/lint.py`, `python scripts/test_site_build.py`, and `npm run test:e2e` green
- [ ] UAT on GitHub Pages (`uat` branch deploy) signed off: https://kunojilym.github.io/yzouyang-site/
- [ ] Promoted to `main` Pages deploy matches UAT
- [ ] Preview serves `/`, `/systems/`, `/credentials/`, `/notes/` from PUBLIC export
- [ ] `/about/`, `/contact/`, `/portfolio/` 301 to `/` or `/systems/` as documented
- [ ] Pagefind indexes systems, credentials, and notes (titles + bodies)
- [ ] Footer **Blog** → `/notes/` (on-site); Medium / LinkedIn still external
- [ ] Legacy Bitly shorts (`bit.ly/3GGyiXF`, `bit.ly/4m4fqki`) repointed to `/systems/` and `/credentials/`
- [ ] Smoke all 18 WP slug stubs → matching `/notes/#NOTE-*` (see [c2b-writing-inventory.md](c2b-writing-inventory.md))
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

Draft rows use `visibility_policy: PRIVATE_ONLY` in `writing.yaml`.
