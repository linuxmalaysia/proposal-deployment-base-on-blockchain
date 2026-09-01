---
okf_version: "0.2"
type: "history"
title: "DCA Service Project History Ledger"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "history"
  - "ledger"
  - "dca-service"
  - "milestones"
description: "Historical repository milestone ledger"
resource: "file:///HISTORY.md"
sources:
  - "CHANGELOG.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Project History Ledger

## Phase 1: Greenfield Bootstrapping & Architectural Design (2026-08-25)
- Initialised repository structure following DSOM Protocol guidelines and Clean Architecture principles.
- Configured `uv` environment and dependency management.
- Drafted comprehensive institutional digital custody research documentation across Diátaxis quadrants.
- Implemented pure Python domain models for key vault tiering, segregated account accounting, policy verification, and immutable auditing.
- Integrated Percona Server for PostgreSQL and TimescaleDB dual-write pattern architecture, enabling time-series transaction logging prior to blockchain broadcast.
- Designed Open-Source MPC Wallet System linking Coinbase `cb-mpc` cryptographic library with P2P node transport, policy engine quorums, and database dual-write settlement.
- Integrated Research Commercialisation Fund (RCF) and Digital Asset Custodian (DAC) proposal into Diátaxis documentation, maintaining Percona Server for PostgreSQL & TimescaleDB as primary backend.
- Expanded full Diátaxis documentation suite across Tutorials, How-To Guides, and Reference manuals.
- Created interactive FastAPI backend service (`src/dca_service/web_app.py`) providing REST API endpoints and web routes for W3C DID registration, evidence vault hashing, Cloverleaf quantitative scoring, investor data room, and revenue distribution split.
- Configured Render.com Blueprint deployment specification (`render.yaml`) and authored comprehensive deployment & troubleshooting guide (`docs/how-to/deploy-rcf-dac-web-app-on-render.md`).
- Authored step-by-step Diátaxis guide for securing Supabase PostgreSQL connection strings, environment variables, SSL parameters, and Supabase CLI on Render.com (`docs/how-to/connect-supabase-postgresql-on-render.md`).
- Implemented real-time Database Connection Status diagnostic page (`/db-status` & `/api/db-status`), schema DDL specification (`docs/schema.sql`), and Render secret file environment loader in `src/dca_service/web_app.py`.
- Automated database schema table check and creation routine (`auto_check_and_build_schema`) on application deployment and startup via FastAPI `lifespan` context manager, ensuring fail-safe execution and zero data loss on Render.com.
- Implemented `HttpOnly`, `SameSite="lax"`, `Secure` cookie session handling (`/api/login`, `/api/logout`) for web browser session isolation from client-side scripts.
- Implemented connection pool metrics monitoring (`ConnectionPoolMetrics`) for Supabase / PostgreSQL exposed via `/api/db-pool-metrics` and `/api/db-status`.
- Expanded high-throughput in-memory TTL caching (`INVESTOR_ASSETS_CACHE_TTL`) for investor data room endpoints with instant cache invalidation upon asset registration.
- Enforced strict type annotations and future annotations across all core domain entities in `src/dca_service/core/` and updated `.gitignore` exclusions for test/cache artifacts.
- Extended Playwright end-to-end browser automation test suite (`tests/test_playwright_e2e.py`) to automate full login form submission, HttpOnly session cookie handling, administrative user creation, table rendering, and logout workflow under headless CI.
- Authored Diátaxis explanation guide (`docs/explanation/httponly-cookies-and-connection-pooling.md`) conforming to OKF v0.2 frontmatter with all 13 mandatory fields.
- Codified Rule 9 (Local Knowledge-First & Metadata Discovery Mandate) in `.agents/AGENTS.md` and updated root AI Gateway `AGENTS.md`.
- Authored Standard Operating Procedure `docs/how-to/sop-knowledge-first-discovery.md` documenting the 3-step local OKF frontmatter search flow (`topics:` / `description:`) before remote execution or web search.
