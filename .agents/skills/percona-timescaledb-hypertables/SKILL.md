---
okf_version: "0.2"
type: "agent_skill"
title: "Percona PostgreSQL & TimescaleDB Hypertables Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "percona"
  - "timescaledb"
  - "hypertables"
  - "time-series"
description: "Manage append-only time-series transaction data, hypertable compression, and chunk archiving policies."
resource: "file:///.agents/skills/percona-timescaledb-hypertables/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "percona-timescaledb-hypertables"
---

# Percona PostgreSQL & TimescaleDB Hypertables Skill

## Overview

Optimises transaction log performance using Percona Server for PostgreSQL and TimescaleDB extension.

## Capabilities

- Percona Server for PostgreSQL is designated as the primary database package for all application workloads and blockchain data synchronization.
- TimescaleDB extension is used within PostgreSQL to handle append-only time-series transaction data, hypertable compression, and table archiving.
- The FastAPI application uses Brotli (brotli-asgi) and GZip (GZipMiddleware) compression middlewares for web asset responses, while transaction history in TimescaleDB uses native columnar compression (timescaledb.compress) segmented by account and asset.
- Automated chunk compression and archiving policies.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
