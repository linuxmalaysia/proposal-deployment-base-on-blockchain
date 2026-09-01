---
okf_version: "0.2"
type: "agent_skill"
title: "Database Status In-Memory TTL Caching Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "caching"
  - "db-status"
  - "ttl"
  - "performance"
description: "Provide high-concurrency database status caching with configurable DB_STATUS_CACHE_TTL and cache bypass."
resource: "file:///.agents/skills/db-status-ttl-caching/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "db-status-ttl-caching"
---

# Database Status In-Memory TTL Caching Skill

## Overview

Prevents database polling overload using in-memory TTL caching in `check_database_connection`.

## Parameters

- Default TTL: 5.0 seconds (configurable via `DB_STATUS_CACHE_TTL`).
- Supports explicit cache bypass for instant diagnostic refresh.


---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
