# Branch Protection Notes

Operator-facing checklist for `main` so agents can open draft PRs but cannot
merge, force-push, delete protected branches, or bypass review.

## Target Settings

| Setting | Value |
|---|---|
| Require a pull request before merging | On |
| Require status checks to pass | On |
| Required check | `lint-build` |
| Allow force pushes | Off |
| Allow deletions | Off |
| Admin bypass | Off |
| Agent PAT | Fine-grained Contents + Pull requests R/W; no admin, no workflow, no bypass |

## Agent Rules

- Open draft PRs only.
- Never push directly to `main`.
- Never merge PRs.
- Do not add private repo tokens to public CI.
- Validate vendored data with `uv run python scripts/lint.py`; non-public visibility markers must fail the build.
