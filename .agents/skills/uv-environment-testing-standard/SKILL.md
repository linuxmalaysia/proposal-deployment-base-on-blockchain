---
okf_version: "0.2"
type: "agent_skill"
title: "uv Environment & Pytest Execution Standard Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "uv"
  - "pytest"
  - "testing"
  - "environment"
description: "Execute all Python environment commands and tests strictly through the uv toolchain (uv run pytest)."
resource: "file:///.agents/skills/uv-environment-testing-standard/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "uv-environment-testing-standard"
---

# uv Environment & Pytest Execution Standard Skill

## Overview

Mandates consistent virtual environment management via `uv`.

## Execution Commands

- Test suite: `uv run pytest`.
- Python scripts: `uv run python <script.py>`.
- Zero global mutations or direct system `pip` invocations allowed.


## Sovereign Knowledge Mandate

- Tests are executed using uv run pytest.
- The repository uses uv as the Python environment and package management tool for all project operations.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
