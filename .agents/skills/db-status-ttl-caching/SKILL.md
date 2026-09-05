---
okf_version: "0.2"
type: "agent_skill"
title: "Database Status In-Memory TTL Caching Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "caching"
  - "db-status"
  - "ttl"
  - "performance"
description: "Provide high-concurrency database status caching with configurable DB_STATUS_CACHE_TTL and cache bypass."
resource: "file:///.agents/skills/db-status-ttl-caching/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "db-status-ttl-caching"
---

# Database Status In-Memory TTL Caching Skill

## Overview

Prevents database polling overload using in-memory TTL caching in `check_database_connection`.

## Parameters

- Default TTL: 5.0 seconds (configurable via `DB_STATUS_CACHE_TTL`).
- Supports explicit cache bypass for instant diagnostic refresh.


## Sovereign Knowledge Mandate

- The database status diagnostic function check_database_connection in src/dca_service/web_app.py implements in-memory TTL caching (configurable via environment variable DB_STATUS_CACHE_TTL, defaulting to 5.0s) to prevent redundant database round-trips under high polling concurrency, with support for cache bypass.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
