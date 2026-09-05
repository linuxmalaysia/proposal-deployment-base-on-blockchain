---
okf_version: "0.2"
type: "agent_skill"
title: "FastAPI Lifespan Automatic Schema Builder Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "fastapi"
  - "lifespan"
  - "schema"
  - "postgresql"
description: "Automatically check and build missing database tables from docs/schema.sql non-destructively during startup."
resource: "file:///.agents/skills/fastapi-lifespan-schema-builder/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "fastapi-lifespan-schema-builder"
---

# FastAPI Lifespan Automatic Schema Builder Skill

## Overview

Executes non-destructive schema initialization during FastAPI application startup.

## Details

- Lifespan context manager: `auto_check_and_build_schema`.
- Source DDL: `docs/schema.sql`.
- Fail-safe error handling prevents startup crashes during temporary database outages.


## Sovereign Knowledge Mandate

- FastAPI application startup in src/dca_service/web_app.py uses a lifespan context manager (auto_check_and_build_schema) to automatically check and build missing database tables from docs/schema.sql non-destructively with fail-safe error handling.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
