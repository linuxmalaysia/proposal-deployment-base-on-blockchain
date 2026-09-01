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
  - "antigravity"
  - "agent-skills"
description: "Root-level directives specifying Clean Architecture rules, Google Antigravity skills, and Jules context protocols"
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

Welcome, AI Agent (Google Jules, Google Antigravity, Cursor, Copilot, Claude).
This repository operates under the **Deep State of Mind (DSOM) Protocol** and incorporates **Google Antigravity-compatible Agent Skills**.

## 🚀 Immediate AI Routing Mandate

Before processing any task or modifying code, you MUST load and obey the sovereign AI rules:
- Read Master AI Constitution: `.agents/AGENTS.md`
- Active State Memory: `.agents/brain/task.md`
- Past Session History: `.agents/brain/walkthrough.md`
- Spatial Palace Registry: `.agents/brain/palace_registry.md`
- Google Antigravity Agent Skills Matrix: `.agents/skills/`

## 🧠 Google Antigravity & Jules Agent Skills Protocol

Google Antigravity and Google Jules operate in unison across this repository. All operational and domain knowledge is encapsulated inside modular skills under `.agents/skills/<skill-name>/SKILL.md`.

When executing tasks:
1. **Skill Discovery:** Search `.agents/skills/` for relevant `SKILL.md` documents matching task requirements.
2. **Context Memory Enablement:** Load context memories from `.agents/brain/` to align responses across sessions.
3. **Skill Execution:** Adhere to instructions, triggers, and validation rules specified in each `SKILL.md`.

## 🛡️ Core Rules Summary

1. **Linguistic Sovereignty:** Standard UK English (`initialise`, `prioritise`, `segregated`) or DBP-standard Bahasa Melayu Malaysia (Piawai).
2. **Environment & Dependency:** All Python operations must run via `uv` (`uv run pytest`, `uv add`). Zero global mutations.
3. **Clean Architecture:** Domain business logic in `src/dca_service/core/` must have zero external framework dependencies.
4. **OKF v0.2 Frontmatter:** All Markdown files must start with OKF v0.2 YAML frontmatter with all 13 mandatory fields.
5. **Triple-Ledger:** Maintain `README.md`, `CHANGELOG.md`, and `HISTORY.md`.
6. **Local Knowledge-First:** Query `.agents/brain/`, `.agents/skills/`, and `docs/` OKF frontmatter before external calls.

Refer to `.agents/AGENTS.md` for full constitutional laws.
