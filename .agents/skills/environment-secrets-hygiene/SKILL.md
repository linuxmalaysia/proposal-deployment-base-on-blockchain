---
okf_version: "0.2"
type: "agent_skill"
title: "Strict Environment Secrets & Credentials Protection Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "secrets"
  - "security"
  - "hygiene"
  - "placeholders"
description: "Enforce zero exposure of secrets, credentials, or API keys in outputs, web endpoints, PRs, or docs."
resource: "file:///.agents/skills/environment-secrets-hygiene/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "environment-secrets-hygiene"
---

# Strict Environment Secrets & Credentials Protection Skill

## Overview

Guarantees sensitive keys are sanitized across all outputs and documentation.

## Guidelines

- Never print or render production keys.
- Use generic placeholders (e.g. `sb_sk_placeholder_123`) in tests and examples.
- Exclude secret files via `.gitignore`.


## Sovereign Knowledge Mandate

- Environment secrets and Supabase credentials must never be exposed or displayed in application output, web endpoints, code repositories, PRs, or documentation; only generic placeholder values must be used in examples.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
