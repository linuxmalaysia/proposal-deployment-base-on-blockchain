---
okf_version: "0.2"
type: "agent_skill"
title: "Jules Memory Enablement and Context Loading Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "jules"
  - "context-memory"
  - "antigravity"
  - "dsom"
description: "Enable and load context memories across sessions to align Google Jules and Google Antigravity responses."
resource: "file:///.agents/skills/jules-context-memory/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "jules-context-memory"
---

# Jules Memory Enablement and Context Loading Skill

## Overview

This skill governs how Google Jules and Google Antigravity persist and restore context from past interaction sessions using `.agents/brain/` spatial memory anchors.

## Operational Workflow

1. At start-of-day (SOD), read `.agents/brain/task.md`, `.agents/brain/walkthrough.md`, and `.agents/brain/palace_registry.md`.
2. Extract historical session decisions, active backlog, and repository asset locations.
3. Inject past context memories into active reasoning prior to taking actions.
4. At end-of-day (EOD), persist all newly acquired knowledge back into `.agents/brain/`.


---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
