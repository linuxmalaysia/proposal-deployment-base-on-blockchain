---
okf_version: "0.2"
type: "agent_skill"
title: "Concentric Clean Architecture Inward Dependency Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "clean-architecture"
  - "dependencies"
  - "core-domain"
  - "isolation"
description: "Enforce Concentric Clean Architecture where core domain entities in src/dca_service/core/ have zero external dependencies."
resource: "file:///.agents/skills/concentric-clean-architecture/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "concentric-clean-architecture"
---

# Concentric Clean Architecture Inward Dependency Skill

## Overview

Guarantees clean separation of business logic from external frameworks.

## Inward Rule

- `src/dca_service/core/` entities must have ZERO third-party library dependencies.
- Storage drivers, HTTP frameworks, and external APIs must be isolated in `src/dca_service/adapters/`.


---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
