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
- `blockchain_sync.py` -> TimescaleDB time-series models and blockchain sync states.

### Adapters (`src/dca_service/adapters/`)

- `timescaledb_adapter.py` -> Percona PostgreSQL / TimescaleDB hypertable persistence & dual-write service.

### Tests (`tests/`)

- Pytest test suites mirroring core domain & adapter modules.

### Documentation (`docs/`)

- `docs/explanation/open-source-mpc-wallet-architecture.md` -> Coinbase `cb-mpc` open-source wallet architecture.
- `docs/explanation/percona-timescaledb-blockchain-sync.md` -> Dual-write PostgreSQL / TimescaleDB architecture.
- `docs/explanation/research-commercialisation-fund-dac-proposal.md` -> RCF and DAC proposal architecture document.
- `docs/tutorials/getting-started-dca-dac.md` -> Getting Started Tutorial for DCA/DAC on Percona PostgreSQL.
- `docs/how-to/install-and-configure-guardrails.md` -> How-To Guide for guardrails and tools.
- `docs/reference/dca-dac-api-and-cli-reference.md` -> Core API, CLI, and Data Objects Reference.

### Tools & Guardrails (`tools/`)

- `tools/generate_summary.py` -> Documentation summary generator.
- `tools/install_git_guardrails.py` -> DSOM git pre-commit hook validator.
