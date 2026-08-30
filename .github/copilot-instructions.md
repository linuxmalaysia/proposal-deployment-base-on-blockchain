---
okf_version: "0.2"
type: "agent_instructions"
title: "GitHub Copilot Workspace Directives & Clean Architecture Guardrails"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "copilot"
  - "directives"
  - "clean-architecture"
  - "okf"
  - "dsom"
description: "Custom system prompt and engineering instructions for GitHub Copilot"
resource: "file:///.github/copilot-instructions.md"
sources:
  - "AGENTS.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# GitHub Copilot Custom Instructions

- Adhere strictly to the Deep State of Mind (DSOM) Protocol.
- Use UK English spelling in code comments and documentation.
- Maintain Clean Architecture boundary in `src/dca_service/core/`.
- Use `uv` toolchain for all Python task executions.
