---
okf_version: "0.2"
type: "agent_skill"
title: "Database Connection Pool Metrics & Checkout Monitoring Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "connection-pool"
  - "metrics"
  - "monitoring"
  - "postgresql"
description: "Track database connection pool statistics and checkout latency for Supabase / PostgreSQL via ConnectionPoolMetrics."
resource: "file:///.agents/skills/db-connection-pool-metrics/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "db-connection-pool-metrics"
---

# Database Connection Pool Metrics & Checkout Monitoring Skill

## Overview

Monitors PostgreSQL database connection pool health and performance.

## Implementation

- Track metrics using `ConnectionPoolMetrics` in `src/dca_service/web_app.py`.
- Expose realtime telemetry via `/api/db-pool-metrics`.


## Sovereign Knowledge Mandate

- Database connection pooling metrics and checkout latency monitoring for Supabase / PostgreSQL are tracked via ConnectionPoolMetrics in src/dca_service/web_app.py and exposed via the /api/db-pool-metrics endpoint.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
