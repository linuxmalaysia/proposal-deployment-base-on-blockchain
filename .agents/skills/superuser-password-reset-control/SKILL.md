---
okf_version: "0.2"
type: "agent_skill"
title: "Superuser Password Reset Restriction Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "superuser"
  - "password-reset"
  - "security"
  - "sql-only"
description: "Manage superuser credential resets via SUPERUSER_INITIAL_PASSWORD seeding or scrypt hash updates."
resource: "file:///.agents/skills/superuser-password-reset-control/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "superuser-password-reset-control"
---

# Superuser Password Reset Restriction Skill

## Overview

Guards root superuser credentials against unauthorised API or UI password reset attempts.

## Directives

- `dca_sys_root` password resets via API or Web UI are blocked with HTTP 403 Forbidden.
- Password resets must use the supported `SUPERUSER_INITIAL_PASSWORD` startup seeding flow or direct SQL updates using valid scrypt hash formatting with synchronized registry state.


## Sovereign Knowledge Mandate

- System superuser (dca_sys_root) password resets are restricted to direct SQL database queries; reset attempts via API endpoints or UI are blocked with HTTP 403 Forbidden.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
