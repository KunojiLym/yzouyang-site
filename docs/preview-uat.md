# Preview & UAT

Three ways to review the static site **before** promoting to `main` / apex cutover.

## 1. Offline local preview (no publish)

```bash
python scripts/preview.py
# http://127.0.0.1:8080/

# Mimic GitHub project Pages path prefix:
python scripts/preview.py --base-path /yzouyang-site
```

Runs lint → build (Pagefind included) → local server. No network deploy.

Contract checks: `python scripts/test_site_build.py` after build. Usability: `npm run test:e2e` (serves `dist/`).


## 2. PR artifact (downloadable dist)

Every PR CI run uploads artifact **`site-preview`** (built `dist/` with `/yzouyang-site` base path).

1. Open the PR → Checks → `lint-build`
2. Download **site-preview**
3. Unzip and either:
   - `python scripts/preview.py` from a branch checkout, or
   - serve the unzipped tree behind a path prefix `/yzouyang-site/`

## 3. Publish to UAT (GitHub Pages, not `main`)

GitHub allows **one** Pages URL per repo: https://kunojilym.github.io/yzouyang-site/

| Action | Result |
|---|---|
| Push / merge to **`uat`** | Deploys that tree to Pages (UAT) |
| Push / merge to **`main`** | Deploys that tree to the **same** Pages URL (promote) |
| Actions → **ci** → Run workflow → `deploy_target=uat` | Deploy current branch ref as UAT |

Recommended flow:

```text
feature branch → draft PR → merge to uat  → review Pages URL
uat → PR into main         → merge main   → Pages = signed-off build
apex DNS cutover only after main Pages parity (see cutover.md)
```

Create `uat` once (from `main` or from the Phase 1 PR):

```bash
git fetch origin
git checkout -b uat origin/main   # or from the feature branch after review
git push -u origin uat
```

### Environments

- **`uat`** — Pages deploy from `uat` / manual `deploy_target=uat`
- **`github-pages`** — Pages deploy from `main` / manual `deploy_target=production`

Add required reviewers on the `uat` environment in GitHub settings if you want a human gate before UAT goes live on Pages.

### Note

UAT and production **share** the Pages hostname until you add a second host (e.g. Cloudflare Pages project). Apex `yzouyang.com` stays on WordPress until [cutover.md](cutover.md).

## 4. CI / Pages failure → ntfy

Optional GitHub Actions secret **`NTFY_TOPIC_URL`** (full topic URL). Job `notify-ntfy` runs after `lint-build` or `deploy` **failure** and POSTs the workflow run URL only (no PRIVATE/CV body). If the secret is unset, the job exits 0. Reuse the Alertmanager ntfy topic if you already subscribe on the phone.
