---
okf_version: "0.2"
type: "agent_skill"
title: "Jekyll Liquid Relative URL & Baseurl Resolution Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "jekyll"
  - "liquid"
  - "relative-url"
  - "github-pages"
description: "Use relative_url Liquid filter alongside baseurl setting in _config.yml to ensure correct asset and link resolution."
resource: "file:///.agents/skills/jekyll-baseurl-relative-links/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "jekyll-baseurl-relative-links"
---

# Jekyll Liquid Relative URL & Baseurl Resolution Skill

## Overview

Ensures documentation assets and navigation links render correctly under subpath deployments.

## Rule

- Always format internal links and asset tags with `| relative_url`.
- Maintain `baseurl` configuration in `_config.yml`.


## Sovereign Knowledge Mandate

- Jekyll layouts and documents use the relative_url Liquid filter alongside the baseurl setting in _config.yml to ensure correct asset and link resolution under repository subpath deployments.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
