---
okf_version: "0.2"
type: "agent_skill"
title: "Supabase PostgreSQL Deployment on Render.com Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "supabase"
  - "render"
  - "postgresql"
  - "sslmode"
description: "Configure Supabase PostgreSQL database connections on Render using environment variables or secret files with enforced SSL."
resource: "file:///.agents/skills/supabase-render-deployment/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "supabase-render-deployment"
---

# Supabase PostgreSQL Deployment on Render.com Skill

## Overview

Governs cloud database configuration for Render Web Services.

## Setup

- Key variables: `DATABASE_URL`, `SUPABASE_PROJECT_REF`, Secret Files (`/etc/secrets/`).
- Enforce SSL mode: `sslmode=require`.
- `render.yaml` setting: `sync: false` to prevent accidental key commits.


## Sovereign Knowledge Mandate

- Supabase PostgreSQL database connections on Render.com are configured via environment variables (DATABASE_URL, SUPABASE_PROJECT_REF) or Secret Files (/etc/secrets/) with enforced SSL (sslmode=require) and sync: false in render.yaml to prevent committing secrets.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
