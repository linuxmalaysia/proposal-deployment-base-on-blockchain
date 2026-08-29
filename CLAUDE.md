---
okf_version: '0.2'
type: gateway
title: Claude AI Integration Rules & Workspace Directives
timestamp: '2026-08-25T00:00:00Z'
topics:
- claude
- directives
- clean-architecture
- okf
- dsom
description: Workspace configuration and guidelines for Anthropic Claude AI sessions
  in the DCA platform.
resource: file:///CLAUDE.md
sources:
- AGENTS.md
generated: jules
verified: true
status: approved
stale_after: '2027-08-25T00:00:00Z'
language: en-GB
---
# Claude Code & Desktop Rules - DSOM Protocol Integration

You are operating under the **Deep State of Mind (DSOM) Protocol**.
Before answering or generating code, inspect:
- `.agents/AGENTS.md`
- `.agents/brain/task.md`
- `.agents/brain/walkthrough.md`
- `.agents/brain/palace_registry.md`

Key Directives:
- UK English spelling standard (`initialise`, `segregated`, `prioritise`).
- Zero external dependencies for `src/dca_service/core/`.
- All Python execution must use `uv run`.
