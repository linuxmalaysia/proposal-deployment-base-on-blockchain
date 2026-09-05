---
okf_version: "0.2"
type: "agent_skill"
title: "Strict Mypy Type Annotation Enforcement Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "mypy"
  - "typing"
  - "quality"
  - "python"
description: "Enforce strict Mypy type checking across adapter layer and web application modules."
resource: "file:///.agents/skills/strict-mypy-type-annotations/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "strict-mypy-type-annotations"
---

# Strict Mypy Type Annotation Enforcement Skill

## Overview

Mandates 100% type annotation coverage using `uv run mypy --strict src/`.

## Enforcement Scope

- `src/dca_service/adapters/` (storage and framework adapters).
- `src/dca_service/web_app.py` (FastAPI application layer).
- Mandatory use of `from __future__ import annotations` across Python files.


## Sovereign Knowledge Mandate

- Strict Mypy type annotations (mypy --strict) are enforced across the adapter layer (src/dca_service/adapters/) and web layer (src/dca_service/web_app.py).

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
