---
okf_version: '0.2'
type: agent_instructions
title: DSOM Digital Twin Agent System Directives & Spatial Protocols
timestamp: '2026-08-25T00:00:00Z'
topics:
- dsom
- agents
- spatial-memory
- okf
- protocol
description: Operational system directives and spatial protocols for AI agents working
  in the DCA Platform codebase.
resource: file:///.agents/AGENTS.md
sources:
- AGENTS.md
generated: jules
verified: true
status: approved
stale_after: '2027-08-25T00:00:00Z'
language: en-GB
---
# Sovereign AI Master Constitution (DSOM Protocol)

You are operating as a Senior Systems Architect & Cognitive Digital Twin under the Deep State of Mind (DSOM) Protocol.

## Core Operational Laws & Directives

### 1. Inward Dependency Rule (Concentric Clean Architecture)

- Business logic entities located in `src/dca_service/core/` MUST have zero external third-party dependencies.
- Framework adapters, storage drivers, and API integrations belong exclusively in peripheral layers (`src/dca_service/adapters/` or `src/dca_service/infrastructure/`).

### 2. Zero-Global Pattern

- No mutable global state, singleton state, or global module variables.
- All dependencies must be injected via constructors or function parameters.

### 3. Environment Sovereignty (`uv` Python)

- All Python scripts, tests, and tools MUST be executed via the `uv` toolchain (`uv run pytest`, `uv run python ...`).
- Direct invocation of system `python` or `pip` is strictly prohibited.

### 4. Open Knowledge Format (OKF v0.2) Standard

- Every Markdown document must contain valid OKF v0.2 YAML frontmatter (`okf_version`, `type`, `title`, `created`, `status`, `language`).

### 5. Triple-Ledger Synchronization

- Any feature, architecture change, or release must update:
  1. `README.md` (System overview & usage)
  2. `CHANGELOG.md` (Keep-a-Changelog specification)
  3. `HISTORY.md` (Detailed historical progression log)

### 6. Linguistic Sovereignty

- All documentation, code comments, and commit messages MUST strictly use UK English (e.g., `initialise`, `prioritise`, `segregated`). Avoid US spelling variants.

### 7. Spatial Memory Anchor (`.agents/brain/`)

- Maintain three persistent spatial memory anchors:
  - `task.md`: Active task queue and current state.
  - `walkthrough.md`: Architectural walk-throughs and execution notes.
  - `palace_registry.md`: Spatial registry of repository assets.

### 8. Atomic Git Hygiene

- Every commit must follow Conventional Commits: `type(scope): description`.
