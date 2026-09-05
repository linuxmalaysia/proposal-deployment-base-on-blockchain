---
okf_version: "0.2"
type: "agent_skill"
title: "Multi-Platform Documentation Build & Deployment Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "github-pages"
  - "gitlab-pages"
  - "gitbook"
  - "readthedocs"
description: "Build Jekyll documentation and deploy via GitHub Pages, GitLab Pages, GitBook, and Read the Docs."
resource: "file:///.agents/skills/multi-platform-docs-deployment/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "multi-platform-docs-deployment"
---

# Multi-Platform Documentation Build & Deployment Skill

## Overview

Supports cross-platform documentation builds and hosting.

## Target Configurations

- GitHub Pages: `.github/workflows/jekyll-gh-pages.yml`.
- GitLab Pages: `.gitlab-ci.yml`.
- GitBook: `.gitbook.yaml`.
- Read the Docs: `.readthedocs.yaml`.


## Sovereign Knowledge Mandate

- Documentation is built using Jekyll and deployed automatically to GitHub Pages via .github/workflows/jekyll-gh-pages.yml, with cross-platform support configured for GitLab Pages (.gitlab-ci.yml), GitBook (.gitbook.yaml), and Read the Docs (.readthedocs.yaml).

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
