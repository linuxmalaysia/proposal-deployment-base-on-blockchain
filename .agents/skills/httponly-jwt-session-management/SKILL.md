---
okf_version: "0.2"
type: "agent_skill"
title: "HttpOnly Cookie & Dual JWT Session Management Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "httponly"
  - "jwt"
  - "session"
  - "security"
description: "Implement HttpOnly, SameSite=lax, Secure session cookies with dual JWT Bearer header support."
resource: "file:///.agents/skills/httponly-jwt-session-management/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "httponly-jwt-session-management"
---

# HttpOnly Cookie & Dual JWT Session Management Skill

## Overview
Provides secure authentication session management in FastAPI.

## Key Features
- Sets HttpOnly, Secure, SameSite="lax" cookie (`rcf_dac_jwt`) upon `/api/login`.
- Revokes session cookies on `/api/logout`.
- `extract_current_user_payload` seamlessly parses both JWT Bearer headers and session cookies.


---
### Deep State of Mind (DSOM) AI Protocol Compliance
* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix
---
