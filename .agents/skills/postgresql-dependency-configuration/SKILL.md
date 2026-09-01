---
okf_version: "0.2"
type: "agent_skill"
title: "Dual psycopg and psycopg-binary Dependency Configuration Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "psycopg"
  - "postgresql"
  - "dependencies"
  - "pyproject"
description: "Include both psycopg and psycopg-binary in pyproject.toml to ensure standard import availability."
resource: "file:///.agents/skills/postgresql-dependency-configuration/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "postgresql-dependency-configuration"
---

# Dual psycopg and psycopg-binary Dependency Configuration Skill

## Overview
Ensures standard Python `import psycopg` calls work reliably across development and production environments.

## Configuration
- `pyproject.toml` dependencies must list both `psycopg` and `psycopg-binary`.


---
### Deep State of Mind (DSOM) AI Protocol Compliance
* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix
---
