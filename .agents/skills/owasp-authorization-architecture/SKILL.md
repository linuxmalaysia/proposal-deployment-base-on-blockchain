---
okf_version: "0.2"
type: "agent_skill"
title: "OWASP Authorization Cheat Sheet Principles Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "owasp"
  - "authorization"
  - "security"
  - "rbac"
description: "Implement least privilege, deny by default, server-side object-level authorization, and W3C DID verification."
resource: "file:///.agents/skills/owasp-authorization-architecture/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "owasp-authorization-architecture"
---

# OWASP Authorization Cheat Sheet Principles Skill

## Overview

Enforces OWASP authorization standards across the system.

## Principles

- Least privilege & deny by default.
- Require server-side object-level authorization for every object request, retaining W3C DIDs and cryptographic hashing for identity and integrity controls.
- Stateless JWT verification and fine-grained ABAC/ReBAC policies.


## Sovereign Knowledge Mandate

- The application's access control architecture adopts OWASP Authorization Cheat Sheet principles (least privilege, deny by default, IDOR prevention via W3C DIDs and cryptographic hashes, stateless JWT verification, ABAC/ReBAC), as documented in docs/explanation/owasp-authorization-framework.md.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
