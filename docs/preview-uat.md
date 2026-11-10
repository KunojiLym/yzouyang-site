# Preview & UAT

Review the static site **before** promoting to `main` / apex cutover. Pages is a release destination; UAT builds are downloadable artifacts until a separate preview host is configured.

## 1. Offline local preview (no publish)

```bash
python scripts/preview.py
# http://127.0.0.1:8080/

# Mimic GitHub project Pages path prefix:
python scripts/preview.py --base-path /yzouyang-site
```

Runs lint → build (Pagefind included) → local server. No network deploy.

Contract checks: `python scripts/test_site_build.py` after build. Playwright: `npm run test:e2e` (usability + theme) and `npm run test:a11y` (serves root-path `dist/`).

**Notes UAT (Reading mode):** on `/notes/`, confirm cover heroes, full-date bylines (`22 Dec 2025`), wrapped code (no per-line horizontal scroll), blockquotes, sidebar in-article TOC when index is open, and reading context bar when index is collapsed. See [design-system.md](design-system.md#reading-mode-notes-only).


## 2. PR artifact (downloadable dist)

Every successful PR, `uat` push, and manual preview run uploads **`site-preview`**. Its base path follows the configured origin (currently `/yzouyang-site`). Preview builds set `noindex, nofollow`. The artifact includes `release.json` with the source revision, run ID and SHA-256 hashes of the packaged files.

1. Open the PR → Checks → `lint-build`
2. Download **site-preview**
3. Unzip and either:
   - `python scripts/preview.py` from a branch checkout, or
   - serve the unzipped tree behind a path prefix `/yzouyang-site/`

## 3. Release to Pages from main

GitHub allows **one** Pages URL per repo: https://kunojilym.github.io/yzouyang-site/

| Action | Result |
|---|---|
| Push / merge to **`uat`** or a PR | Build and test; downloadable preview only |
| Push / merge to **`main`** | Deploy that revision after required build checks |
| Manual `deploy_target=production`, branch **main** | Release only if that revision is still main HEAD |
| Manual `deploy_target=production`, another branch | Fail before publishing |
| Manual `deploy_target=none` | Downloadable preview only |

Manual runs pass `deploy_target` through `github.event.inputs`. Push and pull_request events leave that input empty, so the build resolves to `none` and does not publish.

Recommended flow:

```text
feature branch → draft PR → review downloaded artifact / local preview
reviewed changes → main   → build, test, serialize release → Pages
apex DNS cutover only after main Pages parity (see cutover.md)
```

The deploy job alone has Pages/OIDC write permissions. All releases share the `github-pages` concurrency group, never cancel an active deployment, and check main HEAD after entering that group. New build jobs can cancel obsolete builds without interrupting an active deploy. Pages receives the artifact captured before the separate root-path browser-test rebuild.

### Rollout and independent controls still required

- Apply this workflow to **both main and any existing UAT branch**; an old workflow on UAT can still contain the previous deploy job. Cancel obsolete queued runs before enabling releases.
- Restrict the `github-pages` environment to main and require the intended independent approval. Retire the old UAT deployment environment and audit other workflow versions/branches that retain Pages permissions. Source changes alone do not enforce repository settings.
- Compare deployed `release.json` with the reviewed run and inspect important deployed file hashes. The manifest records artifact identity; it is not a signature or proof of independent approval.
- A shared hosted UAT URL remains outstanding. Give it a separate repository/site destination and credentials before enabling publication there. An environment named `uat` does not create another Pages site.

The source-level guard and offline previews are prepared locally; successful GitHub runs and deployed-artifact verification are still required. Apex `yzouyang.com` stays on WordPress until [cutover.md](cutover.md). See [GitHub's custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) for deployment permissions and environment controls.

## 4. CI / Pages failure → ntfy

Optional GitHub Actions secret **`NTFY_TOPIC_URL`** (full topic URL). Job `notify-ntfy` runs after `lint-build` or `deploy` **failure** and POSTs the workflow run URL only (no PRIVATE/CV body). If the secret is unset, the job exits 0. Reuse the Alertmanager ntfy topic if you already subscribe on the phone.
