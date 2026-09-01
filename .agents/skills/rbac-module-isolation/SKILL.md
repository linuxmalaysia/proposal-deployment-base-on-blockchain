---
okf_version: "0.2"
type: "agent_skill"
title: "Strict RBAC and Operational Module Isolation Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "rbac"
  - "module-isolation"
  - "security"
  - "authorization"
description: "Enforce strict role-based access control and module isolation across administrative and operational endpoints."
resource: "file:///.agents/skills/rbac-module-isolation/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "rbac-module-isolation"
---

# Strict RBAC and Operational Module Isolation Skill

## Overview
Defines role boundaries and module access isolation policies in `src/dca_service/web_app.py` and `docs/role_module_permissions.json`.

## Core Rules
- Admin and Superuser roles are strictly forbidden from accessing operational modules (Modules 2-5).
- Operational endpoints require active authentication.
- Auditor role is granted read-only access to operational modules.
- Dynamic module-role mappings are configurable via `/api/role-assignments`.


---
### Deep State of Mind (DSOM) AI Protocol Compliance
* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix
---
