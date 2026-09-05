---
okf_version: "0.2"
type: "agent_skill"
title: "Async PostgreSQL Connection Pooling via psycopg-pool Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "psycopg-pool"
  - "postgresql"
  - "fastapi"
  - "lifespan"
description: "Manage asynchronous PostgreSQL connection pooling within FastAPI lifespan context manager."
resource: "file:///.agents/skills/psycopg-pool-async-connection/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "psycopg-pool-async-connection"
---

# Async PostgreSQL Connection Pooling via psycopg-pool Skill

## Overview

Manages `psycopg_pool.AsyncConnectionPool` lifecycle within FastAPI application context.

## Pattern

- Initialise connection pool during FastAPI startup lifespan.
- Provide clean shutdown and pool cleanup on application teardown.
- Monitor checkout latency and connection metrics.


## Sovereign Knowledge Mandate

- psycopg-pool is included in project dependencies to manage asynchronous PostgreSQL connection pooling (psycopg_pool.AsyncConnectionPool) within the FastAPI lifespan context manager.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
