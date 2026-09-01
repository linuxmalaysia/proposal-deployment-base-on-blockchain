---
okf_version: "0.2"
type: "agent_skill"
title: "Pre-Commit Guardrails & OKF Validation Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "guardrails"
  - "pre-commit"
  - "okf"
  - "pytest"
description: "Execute OKF frontmatter validation, Ruff linting, Mypy typing, Pytest suite, and SUMMARY.md auto-generation."
resource: "file:///.agents/skills/pre-commit-guardrails-validation/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "pre-commit-guardrails-validation"
---

# Pre-Commit Guardrails & OKF Validation Skill

## Overview

Automates pre-commit quality enforcement via `tools/install_git_guardrails.py`.

## Validation Suite

1. OKF v0.2 frontmatter validation across Markdown files.
2. Ruff linting (`uv run ruff check src/`).
3. Mypy type checking (`uv run mypy src/`).
4. Pytest suite execution (`uv run pytest`).
5. SUMMARY.md auto-generation via `tools/generate_summary.py`.


---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
