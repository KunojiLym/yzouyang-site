## Summary

<!-- What changed and why -->

## Pre-merge checklist (agent ticks)

- [ ] `agent-preflight <repo>` exits 0 on agent-dev
- [ ] **Draft PR** only — not targeting auto-merge
- [ ] Required CI checks green on this PR
- [ ] **homelab-gitops only:** Argo `app diff` note attached (resource names / +/- counts) — **no** prod sync from PR
- [ ] No secrets, age private key material, or decrypted SOPS in the diff

## Human merge

Operator reviews and merges (or closes). Agents never merge to `main`.
