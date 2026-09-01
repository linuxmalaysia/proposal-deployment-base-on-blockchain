---
okf_version: "0.2"
type: "spatial_memory"
title: "Spatial Memory Palace Registry & Knowledge Map"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "dsom"
  - "memory-palace"
  - "spatial-memory"
  - "registry"
description: "Directory registry and structural map of the Spatial Memory Palace"
resource: "file:///.agents/brain/palace_registry.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Palace Registry (`palace_registry.md`)

## Repository Map

### Governance & AI Gateway Matrix
- `AGENTS.md` -> Root Gateway File for AI agents.
- `.agents/AGENTS.md` -> Sovereign Master AI Constitution under Deep State of Mind (DSOM) Protocol.
- `.cursorrules` -> Cursor AI configuration entrypoint.
- `CLAUDE.md` -> Claude Desktop / Code setup rules.
- `.github/copilot-instructions.md` -> GitHub Copilot instruction matrix.

### Spatial Memory Anchors (`.agents/brain/`)
- `.agents/brain/task.md` -> Active task state and chronological task queue.
- `.agents/brain/walkthrough.md` -> Session execution log and historical architectural decisions.
- `.agents/brain/palace_registry.md` -> Spatial asset map and structural knowledge registry.

### Source Code Core (`src/dca_service/core/`)

- `key_management.py` -> MPC & HSM vault key management domain model.
- `account_ledger.py` -> Segregated client ledger & non-commingling rules.
- `policy_engine.py` -> Quorum approvals, limits, allow-lists.
- `ancillary_audit.py` -> Staking, tokenization, immutable audit logger.
- `blockchain_sync.py` -> TimescaleDB time-series models and blockchain sync states.

### Adapters & Web Application (`src/dca_service/`)

- `adapters/timescaledb_adapter.py` -> Percona PostgreSQL / TimescaleDB hypertable persistence & dual-write service.
- `web_app.py` -> Interactive FastAPI portal web service, RBAC module access isolation, W3C DIDs, HttpOnly session handling, connection pool metrics, and database diagnostics.

### Tests (`tests/`)

- Pytest test suites covering core domain, web application, RBAC permissions, Playwright E2E browser automation, database status, and OKF frontmatter validation (1161 tests total).

### Documentation (`docs/`)

- `docs/role_module_permissions.json` -> RBAC and module-role authorization permission specification matrix.
- `docs/schema.sql` -> Project SQL DDL schema definitions for PostgreSQL.
- `docs/explanation/owasp-authorization-framework.md` -> OWASP Authorization Cheat Sheet & RBAC architecture guide.
- `docs/explanation/httponly-cookies-and-connection-pooling.md` -> HttpOnly cookie security, connection pool metrics, and caching architecture.
- `docs/explanation/open-source-mpc-wallet-architecture.md` -> Coinbase `cb-mpc` open-source wallet architecture.
- `docs/explanation/percona-timescaledb-blockchain-sync.md` -> Dual-write PostgreSQL / TimescaleDB architecture.
- `docs/explanation/research-commercialisation-fund-dac-proposal.md` -> RCF and DAC proposal architecture document.
- `docs/tutorials/getting-started-dca-dac.md` -> Getting Started Tutorial for DCA/DAC on Percona PostgreSQL.
- `docs/tutorials/web-application-user-guide.md` -> Web Application User & Administrative Guide.
- `docs/how-to/install-and-configure-guardrails.md` -> How-To Guide for guardrails and tools.
- `docs/how-to/connect-supabase-postgresql-on-render.md` -> Step-by-step guide for Supabase PostgreSQL on Render, including Agent Skills configuration (`npx skills add supabase/agent-skills`).
- `docs/how-to/deploy-rcf-dac-web-app-on-render.md` -> Web application deployment guide on Render.com.
- `docs/how-to/reset-superuser-password-and-manage-users.md` -> Superuser password reset and user management guide.
- `docs/how-to/sop-knowledge-first-discovery.md` -> SOP for Local Knowledge-First Discovery and OKF context preservation.
- `docs/reference/dca-dac-api-and-cli-reference.md` -> Core API, CLI, and Data Objects Reference.

### Tools & Guardrails (`tools/`)

- `tools/generate_summary.py` -> Documentation summary generator and router index builder (`SUMMARY.md`).
- `tools/install_git_guardrails.py` -> DSOM git pre-commit hook validator (Ruff, Mypy, Pytest, OKF frontmatter validation).
