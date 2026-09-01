---
okf_version: "0.2"
type: "agent_instructions"
title: "DCA Platform Core Engineering & Agent Directives"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "agents"
  - "engineering"
  - "clean-architecture"
  - "okf"
  - "dsom"
description: "Root-level directives specifying Clean Architecture rules"
resource: "file:///AGENTS.md"
sources:
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Root AI Gateway: Deep State of Mind (DSOM) Protocol

Welcome, AI Agent (Jules, Cursor, Copilot, Claude).
This repository operates under the **Deep State of Mind (DSOM) Protocol**.

## 🚀 Immediate AI Routing Mandate

Before processing any task or modifying code, you MUST load and obey the sovereign AI rules:
- Read Master AI Constitution: `.agents/AGENTS.md`
- Active State Memory: `.agents/brain/task.md`
- Past Session History: `.agents/brain/walkthrough.md`
- Spatial Palace Registry: `.agents/brain/palace_registry.md`

## 🛡️ Core Rules Summary

1. **Linguistic Sovereignty:** Standard UK English (`initialise`, `prioritise`) or DBP-standard Bahasa Melayu Malaysia (Piawai).
2. **Environment & Dependency:** All Python operations must run via `uv` (`uv run pytest`, `uv add`). Zero global mutations.
3. **Clean Architecture:** Domain business logic in `src/dca_service/core/` must have zero external framework dependencies.
4. **OKF Frontmatter:** All Markdown documentation must start with OKF v0.2 YAML frontmatter.
5. **Triple-Ledger:** Maintain `README.md`, `CHANGELOG.md`, and `HISTORY.md`.
6. **Local Knowledge-First:** Always query `.agents/brain/` and `docs/` OKF frontmatter before external calls.

Refer to `.agents/AGENTS.md` for full constitutional laws.
