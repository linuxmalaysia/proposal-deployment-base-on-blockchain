---
okf_version: "0.2"
type: "agent_skill"
title: "Root-Level Markdown File Restriction Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "markdown"
  - "root-restriction"
  - "diataxis"
  - "organization"
description: "Restrict root-level Markdown files strictly to README.md, CHANGELOG.md, SUMMARY.md, and HISTORY.md."
resource: "file:///.agents/skills/root-markdown-restriction/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "root-markdown-restriction"
---

# Root-Level Markdown File Restriction Skill

## Overview

Enforces strict file organization in the repository root.

## Allowed Root Files

- `README.md`
- `CHANGELOG.md`
- `SUMMARY.md`
- `HISTORY.md`
*Note: All other documentation must reside inside `docs/` or `.agents/`.*


## Sovereign Knowledge Mandate

- Root-level Markdown files are restricted to README.md, CHANGELOG.md, SUMMARY.md, and HISTORY.md, with all other documentation stored inside docs/.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
