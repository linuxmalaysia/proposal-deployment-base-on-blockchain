---
okf_version: "0.2"
type: "agent_skill"
title: "Interactive HTML & JSON Database Diagnostic Endpoints Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "db-status"
  - "diagnostics"
  - "fastapi"
  - "html"
description: "Provide interactive database connectivity and schema diagnostics via /db-status and /api/db-status."
resource: "file:///.agents/skills/db-status-diagnostic-endpoints/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "db-status-diagnostic-endpoints"
---

# Interactive HTML & JSON Database Diagnostic Endpoints Skill

## Overview

Delivers realtime database status feedback without exposing secrets.

## Endpoints

- `/db-status`: Interactive HTML portal rendering status badges and pool metrics.
- `/api/db-status`: JSON API endpoint for automated monitoring probes, sanitizing PostgreSQL/Supabase raw exception text in `status_detail` before returning response.


## Sovereign Knowledge Mandate

- FastAPI web application endpoints /db-status and /api/db-status in src/dca_service/web_app.py provide interactive HTML and JSON database connectivity diagnostics and schema verification without exposing environment secrets.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
