---
okf_version: "0.2"
type: "agent_skill"
title: "Automated Security CI Workflow & SAST Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "security"
  - "ci-cd"
  - "bandit"
  - "gitleaks"
description: "Execute Bandit SAST static code analysis and Gitleaks secret scanning in GitHub CI."
resource: "file:///.agents/skills/security-ci-workflow-scanner/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "security-ci-workflow-scanner"
---

# Automated Security CI Workflow & SAST Skill

## Overview

Enforces automated static security testing and secret detection in `.github/workflows/security.yml`.

## Tools

- Bandit: Static Application Security Testing (SAST) for Python.
- Gitleaks: Uses `gitleaks/gitleaks-action@v3` with `fetch-depth: 0` to scan repository history for hardcoded secrets.


## Sovereign Knowledge Mandate

- Automated security CI workflow .github/workflows/security.yml executes Bandit SAST static application security testing and Gitleaks secret scanning.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
