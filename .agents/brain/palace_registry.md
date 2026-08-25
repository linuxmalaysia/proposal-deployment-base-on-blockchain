---
okf_version: "0.2"
type: "spatial_memory"
title: "Palace Registry & Asset Mapping"
created: "2026-08-25"
status: "active"
language: "en-GB"
---

# Palace Registry (`palace_registry.md`)

## Repository Map

### Governance & AI Gateway Matrix
- `AGENTS.md` -> Root Gateway File for AI agents.
- `.agents/AGENTS.md` -> Sovereign Master AI Constitution.
- `.cursorrules` -> Cursor AI configuration entrypoint.
- `CLAUDE.md` -> Claude Desktop / Code setup rules.
- `.github/copilot-instructions.md` -> GitHub Copilot instruction matrix.

### Spatial Memory Anchors (`.agents/brain/`)
- `.agents/brain/task.md` -> Active task state and queue.
- `.agents/brain/walkthrough.md` -> Execution log and historical decisions.
- `.agents/brain/palace_registry.md` -> Spatial asset map.

### Source Code Core (`src/dca_service/core/`)
- `key_management.py` -> MPC & HSM vault key management domain model.
- `account_ledger.py` -> Segregated client ledger & non-commingling rules.
- `policy_engine.py` -> Quorum approvals, limits, allow-lists.
- `ancillary_audit.py` -> Staking, tokenization, immutable audit logger.

### Tests (`tests/`)
- Pytest test suites mirroring domain core modules.

### Tools & Guardrails (`tools/`)
- `tools/install_git_guardrails.py` -> DSOM git pre-commit hook validator.
