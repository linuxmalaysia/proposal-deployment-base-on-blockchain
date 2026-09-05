---
okf_version: "0.2"
type: "agent_skill"
title: "Documentation Summary Index Auto-Generation Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "summary"
  - "generate-summary"
  - "indexing"
  - "documentation"
description: "Automatically scan docs/ and root ledgers to build and update SUMMARY.md using tools/generate_summary.py."
resource: "file:///.agents/skills/summary-index-auto-generation/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "summary-index-auto-generation"
---

# Documentation Summary Index Auto-Generation Skill

## Overview

Maintains automated documentation routing and table of contents.

## Tool

- Script: `tools/generate_summary.py`.
- Function: Scans `docs/` and root-level Markdown ledgers to re-index `SUMMARY.md`.


## Sovereign Knowledge Mandate

- Documentation indexing is managed dynamically via tools/generate_summary.py, which scans all .md files to update SUMMARY.md and is executed during pre-commit guardrail checks.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
