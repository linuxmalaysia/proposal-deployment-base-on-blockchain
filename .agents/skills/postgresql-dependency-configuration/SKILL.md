---
okf_version: "0.2"
type: "agent_skill"
title: "Psycopg Binary Dependency Configuration Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "psycopg"
  - "postgresql"
  - "dependencies"
  - "pyproject"
description: "Include psycopg[binary] in pyproject.toml to ensure standard import availability."
resource: "file:///.agents/skills/postgresql-dependency-configuration/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "postgresql-dependency-configuration"
---

# Psycopg Binary Dependency Configuration Skill

## Overview

Ensures standard Python `import psycopg` calls work reliably across development and production environments.

## Configuration

- `pyproject.toml` dependencies specify single `psycopg[binary]` installation mode.


## Sovereign Knowledge Mandate

- Both psycopg and psycopg-binary must be included in pyproject.toml dependencies to allow standard Python import psycopg imports for PostgreSQL connections.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
