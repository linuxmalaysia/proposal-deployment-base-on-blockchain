---
okf_version: "0.2"
type: "agent_skill"
title: "Project SQL DDL Schema Definitions Management Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "schema"
  - "ddl"
  - "sql"
  - "postgresql"
description: "Maintain canonical DDL schema definitions for users, assets, scores, splits, and transactions in docs/schema.sql."
resource: "file:///.agents/skills/ddl-schema-definitions/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "ddl-schema-definitions"
---

# Project SQL DDL Schema Definitions Management Skill

## Overview

Manages canonical database schema DDL inside `docs/schema.sql`.

## Schema Entities

- `users`: User profiles, DID references, and role assignments.
- `assets`: Segregated client digital custody assets.
- `cloverleaf_scores`: Risk assessment metric tables.
- `revenue_splits`: Institutional fee distribution models.
- `blockchain_transactions`: Audit log of on-chain sync transactions.


## Sovereign Knowledge Mandate

- Project DDL schema definitions (users, assets, cloverleaf_scores, revenue_splits, blockchain_transactions) are stored in docs/schema.sql.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
