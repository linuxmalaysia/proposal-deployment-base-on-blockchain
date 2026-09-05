---
okf_version: "0.2"
type: "agent_skill"
title: "In-Memory Leaky-Bucket Rate Limiting Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "rate-limiting"
  - "leaky-bucket"
  - "security"
  - "authentication"
description: "Protect login and account creation endpoints from credential brute-force attacks via in-memory leaky-bucket rate limiting."
resource: "file:///.agents/skills/leaky-bucket-rate-limiting/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "leaky-bucket-rate-limiting"
---

# In-Memory Leaky-Bucket Rate Limiting Skill

## Overview

Implements `is_rate_limited` leaky-bucket algorithm for authentication endpoints.

## Protection Scope

- Endpoints: `/api/login` and `/api/users` in `src/dca_service/web_app.py`.
- Function: Throttle excessive authentication attempts to prevent brute-force attacks.


## Sovereign Knowledge Mandate

- The authentication endpoints /api/login and /api/users in src/dca_service/web_app.py implement an in-memory leaky-bucket rate limiter (is_rate_limited) to protect against credential brute-forcing.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
