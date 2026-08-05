# Operator cutover checklist

**Gate:** only after Phase 1 **UAT / preview** parity is signed off (see [preview-uat.md](preview-uat.md)). Until then, WordPress on Bluehost shared (`yzouyang.com` / `www` → `162.241.24.224`, `host-header` → `shared.bluehost.com`) stays authoritative on the apex.

## Before DNS

- [ ] Offline `python scripts/preview.py` looks right
- [ ] `python scripts/test_site_build.py` and `npm run test:e2e` green
- [ ] UAT on GitHub Pages (`uat` branch deploy) signed off: https://kunojilym.github.io/yzouyang-site/
- [ ] Promoted to `main` Pages deploy matches UAT
- [ ] Preview URL serves `/`, `/about/`, `/portfolio/`, `/credentials/` from PUBLIC export
- [ ] Home `#contact` reachable from sticky header Contact; `/contact/` redirects to Home contact
- [ ] Pagefind works on portfolio or credentials
- [ ] Blog / Medium / LinkedIn still reachable from nav (external)
- [ ] About Selected writing links out (no full post import until C2b)
- [ ] Bitly shorts still resolve: portfolio `bit.ly/3GGyiXF`, credentials `bit.ly/4m4fqki`
- [ ] Digital card (`bit.ly/m/yzouyang`) reachable from home CTA
- [ ] No work/university emails on Contact
- [ ] Footer is public (© + contact/social), not migration notes

## Cutover

1. Point DNS / CDN for apex + `www` to the static host (GitHub Pages custom domain or Cloudflare).
2. Keep WP read-only **or** redirect non-blog routes to static (see [redirects.md](redirects.md)).
3. Leave WP `/blog`, Medium, and LinkedIn writing hosts as-is until **C2b**.
4. Smoke apex `/`, `/portfolio/`, `/credentials/`, Bitly destinations.
5. Do not import writing into Pagefind until C2b inventory is complete.

## Rollback

Repoint DNS to Bluehost / restore WP as primary; static preview can remain for iteration.
