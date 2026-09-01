---
okf_version: "0.2"
type: "standard_operating_procedure"
title: "SOP: Local Knowledge-First Discovery & Context Preservation Protocol"
timestamp: "2026-08-30T00:00:00Z"
topics:
  - "okf"
  - "discovery"
  - "context-management"
  - "brain"
  - "dsom"
  - "sop"
description: "Standard Operating Procedure detailing how AI agents and human operators leverage OKF YAML frontmatter in .agents/brain/ and docs/ to prioritize local discovery before external probing."
resource: "file:///docs/how-to/sop-knowledge-first-discovery.md"
sources:
  - ".agents/AGENTS.md"
  - "AGENTS.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-30T00:00:00Z"
language: "en-GB"
---

# 📚 SOP: Local Knowledge-First Discovery & OKF Context Preservation Protocol

## 1. Executive Intent

To prevent unnecessary remote probes, token context window exhaustion, and mental state loss during engineering sessions, AI agents and developers operating on the Digital Custody Asset (DCA) Platform must strictly adhere to the **Local Knowledge-First Protocol**.

All project specifications, architectural topologies, data schemas, security guardrails, and operational rules are pre-indexed via **Open Knowledge Format (OKF v0.2) YAML Frontmatter** across `.agents/brain/` and `docs/`.

---

## 2. Standard Operating Procedure (Three-Step Discovery Flow)

```text
[ Step 1: User Request / Question ]
         │
         ▼
[ Step 2: Local OKF Search ] ──▶ Keyword search on .agents/brain/ & docs/ (topics: / description:)
         │
         ▼
[ Step 3: Targeted File Inspection ] ──▶ Inspect line ranges / read matched .md files
```

### Step 1: User Request / Question Intake
Upon receiving an operational task, query, or bug report:
- Do NOT immediately execute web searches or probe external remote servers.
- First formulate target keywords based on domain terminology (e.g. `cb-mpc`, `timescaledb`, `httponly-cookies`, `percona`, `render`, `guardrails`).

### Step 2: Local OKF & Metadata Search
Query local project documentation before looking outside the repository:
1. Search local OKF frontmatter in `.agents/brain/` and `docs/` for matching `topics:` or `description:` keywords.
2. Search `.agents/brain/` spatial anchors (`task.md`, `walkthrough.md`, `palace_registry.md`) for current task queue status and session historical context.

### Step 3: Targeted File Reading
Once relevant documents or source files are identified:
- Read specific sections or targeted line ranges to preserve token efficiency.
- Leverage OKF frontmatter metadata (`sources:`, `resource:`) to navigate to related code modules or specifications.

---

## 3. Mandatory Rules & Compliance

1. **Rule (OKF Frontmatter Compliance):** Every Markdown document in the codebase (with the exception of auto-generated indices like `SUMMARY.md`) MUST open on line 1 with `---` and contain valid OKF v0.2 YAML frontmatter with all 13 mandatory fields (`okf_version`, `type`, `title`, `timestamp`, `topics`, `description`, `resource`, `sources`, `generated`, `verified`, `status`, `stale_after`, `language`).
2. **Rule (Metadata-First Discovery):** Always search `topics:` and `description:` metadata in `.agents/brain/` and `docs/` before executing web searches or external network calls.
3. **Rule (Local Single Source of Truth - SSOT):** Local project documentation represents the SSOT for configuration topology, deployment targets, database schemas (`docs/schema.sql`), and policy engine rules. Remote execution is strictly reserved for applying changes or fetching live runtime state not documented locally.
