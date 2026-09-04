---
okf_version: "0.2"
type: "changelog"
title: "DCA Service Platform Changelog & Release History"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "changelog"
  - "releases"
  - "dca-service"
  - "versioning"
description: "Chronological ledger of user-facing changes"
resource: "file:///CHANGELOG.md"
sources:
  - "HISTORY.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-09-02

### Added

- Centralized Database API Access Layer (`src/dca_service/adapters/database_api.py`) for direct PostgreSQL database operations across all application modules.
- Soft non-deletion user archiving policy: `DELETE /api/users/{username}` disables account (`is_active=False`, `is_disabled=True`, `can_login=False`, `is_archived=True`, `tags=['archive']`) without record deletion.
- OWASP REST Security Cheat Sheet compliance: generic authentication failure messages (`"Authentication failed. Invalid username or password."`), CSRF and origin token validation on user mutation endpoints (`create_system_user`, `reset_user_password`, `delete_system_user`, `register_user`), strict `sslmode=verify-full` validation on TCP `DATABASE_URL` connections, and server-side exception logging.
- Refactored `docs/schema.sql` schema definitions with idempotent column migrations and `duplicate_object` exception handling on username unique constraints.

- Local Knowledge-First & Metadata Discovery Mandate in `.agents/AGENTS.md` and root `AGENTS.md` requiring AI agents to query local OKF metadata in `.agents/brain/` and `docs/` before remote server or external web queries.
- Standard Operating Procedure guide (`docs/how-to/sop-knowledge-first-discovery.md`) detailing the 3-step local discovery flow and OKF context preservation rules.
- `HttpOnly`, `SameSite="lax"`, `Secure` cookies for browser session handling on `/api/login` and `/api/logout` endpoint in `src/dca_service/web_app.py`.
- Session cookie extraction support in `extract_current_user_payload` alongside `Authorization: Bearer` headers.
- Connection pooling metrics monitoring (`ConnectionPoolMetrics`) for Supabase / PostgreSQL tracking acquisition latency, pool utilization, and query counts, exposed via `/api/db-pool-metrics` and integrated into `/api/db-status`.
- Expanded in-memory TTL caching (`INVESTOR_ASSETS_CACHE_TTL`) for high-throughput API endpoints with instant cache invalidation upon asset registration.
- Strict type annotations and `from __future__ import annotations` across all core domain entities in `src/dca_service/core/`.
- Playwright E2E browser automation tests (`tests/test_playwright_e2e.py`) covering full login form submission, HttpOnly session cookie verification, administrative user creation, table rendering, and logout workflow under headless CI.
- Diátaxis explanation guide for HttpOnly cookie session security, connection pool metrics, and high-throughput caching ([`docs/explanation/httponly-cookies-and-connection-pooling.md`](docs/explanation/httponly-cookies-and-connection-pooling.md)).
- Automatic fail-safe database schema check and table building routine (`auto_check_and_build_schema`) triggered upon application startup via FastAPI `lifespan` context manager in `src/dca_service/web_app.py`.
- Non-destructive `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` execution preserving existing database tables and records on Render.com deployments.
- Interactive Database Connection Status page (`/db-status`) and JSON diagnostic endpoint (`/api/db-status`) verifying real-time connection status, secret variables, and schema tables in `src/dca_service/web_app.py`.
- SQL DDL schema files (`docs/schema.sql` and `src/dca_service/schema.sql`) for project PostgreSQL tables (`users`, `assets`, `cloverleaf_scores`, `revenue_splits`, `blockchain_transactions`).
- Secret file loader and fallback handling for `INVESTOR_JWT_SECRET` using `SUPABASE_SECRET_KEY` or environment variables on Render.com.
- Diátaxis How-To guide for securely connecting Supabase PostgreSQL database instances on Render.com ([`docs/how-to/connect-supabase-postgresql-on-render.md`](docs/how-to/connect-supabase-postgresql-on-render.md)).

## [0.1.0] - 2026-08-25

### Added
- Greenfield project setup with Python `uv` toolchain.
- DSOM Protocol 6-Pillar downstream footprint (`AGENTS.md`, `.agents/brain/`, spatial memory anchors).
- Core domain models for MPC Key Management, Segregated Client Ledger, Policy Engine, and Ancillary Audit logging.
- Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Synchroniser architecture, domain entities (`src/dca_service/core/blockchain_sync.py`), and storage adapters (`src/dca_service/adapters/timescaledb_adapter.py`).
- Comprehensive pytest suite covering dual-write workflows, error recovery, and TimescaleDB hypertable chunk archiving policies.
- Diátaxis documentation suite covering institutional DCA-as-a-Service architecture, implementation patterns, regulatory frameworks, and PostgreSQL/TimescaleDB time-series sync design.
- Open-Source MPC Wallet System Architecture documentation based on Coinbase `cb-mpc` cryptography library ([`docs/explanation/open-source-mpc-wallet-architecture.md`](docs/explanation/open-source-mpc-wallet-architecture.md)).
- Research Commercialisation Fund (RCF) and Digital Asset Custodian (DAC) proposal documentation anchored on Percona Server for PostgreSQL ([`docs/explanation/research-commercialisation-fund-dac-proposal.md`](docs/explanation/research-commercialisation-fund-dac-proposal.md)).
- Complete Diátaxis Framework documentation expansion (Tutorials, How-To Guides, and Technical Reference).
- Interactive FastAPI Web Application (`src/dca_service/web_app.py`) for RCF & DAC portal modules (W3C DID user registration, asset vault SHA-256 evidence hashing, Cloverleaf MRS score calculation, investor data room, revenue split matrix).
- Render.com Blueprint deployment specification (`render.yaml`) and deployment guide ([`docs/how-to/deploy-rcf-dac-web-app-on-render.md`](docs/how-to/deploy-rcf-dac-web-app-on-render.md)).
