---
okf_version: "0.2"
type: "agent_skill"
title: "FastAPI Web Service Deployment via uv & Uvicorn on Render Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "fastapi"
  - "uvicorn"
  - "uv"
  - "render"
description: "Configure FastAPI application deployment on Render using uv sync build command and uvicorn runner."
resource: "file:///.agents/skills/fastapi-uvicorn-render-config/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "fastapi-uvicorn-render-config"
---

# FastAPI Web Service Deployment via uv & Uvicorn on Render Skill

## Overview

Configures web application runtime environment on Render.com.

## Configuration

- Build command: `uv sync`.
- Start command: `uv run uvicorn src.dca_service.web_app:app --host 0.0.0.0 --port $PORT`.


---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
