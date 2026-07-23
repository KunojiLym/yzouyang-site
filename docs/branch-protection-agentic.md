# Branch protection notes (B5 agentic ops)

Operator-facing checklist for `main` so agents can open **draft PRs only** (no merge, no force-push). SoT also lives in the Genbu Homelab docs (`docs/runbooks/agent-premerge-validation.md`, `docs/runbooks/1password-agent-debug.md`).

## Target settings

| Setting | Value |
|---|---|
| Require a pull request before merging | On |
| Require status checks to pass | On when CI exists (see table) |
| Allow force pushes | Off |
| Allow deletions | Off |
| Admin bypass of the above | Off (preferred) |
| Agent PAT | Fine-grained **Contents** + **Pull requests** R/W — **not** admin / bypass |

## Required check names (when CI exists)

| Repo | Required check job |
|---|---|
| `homelab-gitops` | `validate` |
| `macmini-ops` | `compose-validate` |
| `agentic-services` | `pytest` |
| `personal-content` | PR-only until thin CI exists |
| `yzouyang-site` | PR-only until thin CI exists |

## Measured 2026-07-23 (titles/scopes only)

Via `gh api …/branches/main/protection` as repo admin:

- `homelab-gitops`, `macmini-ops`, `agentic-services`, `personal-content`: require-PR **on**, required status checks **empty**
- `yzouyang-site`: **no** branch protection on `main`

**OPERATOR:** enable the required checks above (and protect `yzouyang-site` `main`). Agents must not push/merge to `main`.
