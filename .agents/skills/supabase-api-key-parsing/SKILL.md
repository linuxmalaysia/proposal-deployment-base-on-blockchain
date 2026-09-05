---
okf_version: "0.2"
type: "agent_skill"
title: "Multi-Format Supabase Environment Key Parsing Skill"
timestamp: "2026-09-01T00:00:00Z"
topics:
  - "supabase"
  - "environment"
  - "configuration"
  - "parsing"
description: "Parse singular and plural Supabase API key environment variables across string, JSON object, and JSON array formats."
resource: "file:///.agents/skills/supabase-api-key-parsing/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "src/dca_service/web_app.py"
  - "src/dca_service/adapters/database_api.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-09-01T00:00:00Z"
language: "en-GB"
name: "supabase-api-key-parsing"
---

# Multi-Format Supabase Environment Key Parsing Skill

## Overview

Ensures resilient environment key loading in `src/dca_service/web_app.py`.

## Formats Handled

- Keys: `SUPABASE_SECRET_KEY`, `SUPABASE_SECRET_KEYS`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_PUBLISHABLE_KEYS`.
- Formats: JSON object, JSON array, and raw plain strings.


## Sovereign Knowledge Mandate

- src/dca_service/web_app.py parses both singular (SUPABASE_SECRET_KEY, SUPABASE_PUBLISHABLE_KEY) and plural (SUPABASE_SECRET_KEYS, SUPABASE_PUBLISHABLE_KEYS) environment variables, supporting JSON object, JSON array, and plain string formats for Supabase API keys.

---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
