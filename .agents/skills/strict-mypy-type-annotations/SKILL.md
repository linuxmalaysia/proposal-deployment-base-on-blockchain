---
okf_version: "0.2"
type: "agent_skill"
title: "Strict Mypy Type Annotation Enforcement Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "mypy"
  - "typing"
  - "quality"
  - "python"
description: "Enforce strict Mypy type checking across adapter layer and web application modules."
resource: "file:///.agents/skills/strict-mypy-type-annotations/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "strict-mypy-type-annotations"
---

# Strict Mypy Type Annotation Enforcement Skill

## Overview
Mandates 100% type annotation coverage using `mypy --strict`.

## Enforcement Scope
- `src/dca_service/adapters/` (storage and framework adapters).
- `src/dca_service/web_app.py` (FastAPI application layer).
- Mandatory use of `from __future__ import annotations` across Python files.


---
### Deep State of Mind (DSOM) AI Protocol Compliance
* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix
---
