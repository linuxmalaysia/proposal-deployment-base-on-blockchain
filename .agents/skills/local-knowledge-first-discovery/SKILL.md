---
okf_version: "0.2"
type: "agent_skill"
title: "Local Knowledge-First & OKF Discovery Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "knowledge-first"
  - "okf"
  - "discovery"
  - "agents"
description: "Mandate local project knowledge search in .agents/brain/ and docs/ using OKF metadata before remote or web calls."
resource: "file:///.agents/skills/local-knowledge-first-discovery/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "local-knowledge-first-discovery"
---

# Local Knowledge-First & OKF Discovery Skill

## Overview

Codifies the 3-step local discovery workflow before attempting external web searches or remote calls.

## Discovery Workflow

1. Query OKF frontmatter (`topics:` and `description:`) in `.agents/brain/` and `docs/`.
2. Inspect local documentation files for relevant domain knowledge.
3. Proceed to external web searches or remote server calls only if local knowledge is insufficient.


## Sovereign Knowledge Mandate

- AI agents must search local project knowledge in .agents/brain/ and docs/ using OKF frontmatter metadata (topics: and description:) before executing remote server calls or web searches, as codified in .agents/AGENTS.md and docs/how-to/sop-knowledge-first-discovery.md.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
