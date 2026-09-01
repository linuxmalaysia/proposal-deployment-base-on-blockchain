---
okf_version: "0.2"
type: "agent_skill"
title: "Superuser Password Reset Restriction Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "superuser"
  - "password-reset"
  - "security"
  - "sql-only"
description: "Restrict system superuser (dca_sys_root) password resets exclusively to direct SQL database queries."
resource: "file:///.agents/skills/superuser-password-reset-control/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "superuser-password-reset-control"
---

# Superuser Password Reset Restriction Skill

## Overview
Guards root superuser credentials against unauthorised API or UI password reset attempts.

## Directives
- `dca_sys_root` password resets via API or Web UI are blocked with HTTP 403 Forbidden.
- Password resets must be executed directly via SQL database queries.


---
### Deep State of Mind (DSOM) AI Protocol Compliance
* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix
---
