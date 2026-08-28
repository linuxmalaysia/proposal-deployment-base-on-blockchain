---
okf_version: "0.2"
type: "explanation"
title: "Open Knowledge Format (OKF v0.2) Architectural Specification & Adoption Guide"
timestamp: "2026-08-25T00:00:00Z"
topics: ["okf", "dsom", "context-engineering", "provenance", "yaml-frontmatter", "diataxis", "specification"]
description: "Comprehensive architectural explanation and adoption guide for Open Knowledge Format (OKF v0.2) in the Deep State of Mind (DSOM) framework."
resource: "file:///docs/explanation/open-knowledge-format-v02-guide.md"
sources: [
  "https://linuxmalaysia.github.io/deep-state-of-mind-for-my-ai/OKF-ADOPTION-GUIDE/",
  "README.md",
  "AGENTS.md",
  ".agents/AGENTS.md"
]
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Open Knowledge Format (OKF v0.2) Architectural Specification & Adoption Guide

## Executive Summary & Core Concept

Introduced by Google Cloud's Data Cloud team in June 2026, the **Open Knowledge Format (OKF)** is an open, vendor-neutral specification designed to resolve the fundamental context problem in autonomous AI agent systems.

Historically, AI agents struggle when deployed in real-world software and infrastructure engineering environments because institutional knowledge — such as system runbooks, database schemas, architectural decision records (ADRs), and operational playbooks — is fragmented across disparate wikis, databases, ticketing platforms, and code comments. Traditional Retrieval-Augmented Generation (RAG) attempts to bridge this gap by slicing raw text into floating-point vector embeddings. However, RAG is stateless, computationally expensive, subject to vector collision, and prone to severe attention dilution (the "lost-in-the-middle" phenomenon) within large language model (LLM) context windows.

OKF formalises the "LLM-wiki" paradigm into a standardised, Git-native representation. Rather than introducing proprietary runtimes, complex database schemas, or heavy binary SDKs, OKF represents curated organisational knowledge as a structured directory of UTF-8 Markdown files initialised with semantic YAML frontmatter.

---

## Why OKF is the Core Engine of Deep State of Mind (DSOM)

The Deep State of Mind (DSOM) protocol relies on OKF as its primary context engineering standard. OKF transforms passive documentation into an active, machine-readable Spatial Memory Palace (`.agents/brain/` and `.agents/skills/`), delivering four critical performance advantages:

```text
+-------------------------------------------------------------------------+
|                      Sovereign AI Workspace (DSOM)                      |
|                                                                         |
|  +-----------------------+                    +----------------------+  |
|  |   Spatial Memory      |                    |  Agent Skill Library |  |
|  |   (.agents/brain/)    |                    |   (.agents/skills/)  |  |
|  |  YAML Frontmatter +   |                    |   YAML Frontmatter + |  |
|  |  Markdown Closets     |                    |   Executable SOPs    |  |
|  +-----------+-----------+                    +----------+-----------+  |
|              |                                           |              |
|              +---------------------+---------------------+              |
|                                    v                                    |
|                    +-------------------------------+                    |
|                    |     OKF Frontmatter Index     |                    |
|                    |    (okf_version, type, title, |                    |
|                    |     timestamp, topics, etc.)  |                    |
|                    +---------------+---------------+                    |
|                                    |                                    |
|       +----------------------------+----------------------------+       |
|       v                            v                            v       |
|  +---------------+          +---------------+          +---------------+|
|  | Progressive   |          | Zero-Loss     |          | Multi-Agent   ||
|  | Disclosure    |          | Reanimation   |          | MCP Server    ||
|  | (~98% Token   |          | (Instant      |          | (FastMCP /    ||
|  | Compression)  |          | Re-alignment) |          | OpenWiki)     ||
|  +---------------+          +---------------+          +---------------+|
+-------------------------------------------------------------------------+
```

### 1. 98%+ Token & Cost Compression Ratio
Loading raw source code, exhaustive database dumps, or thousands of lines of unformatted documentation into an LLM prompt consumes hundreds of thousands of context tokens, draining API budgets and degrading reasoning quality. In DSOM, OKF YAML frontmatter allows AI agents to scan lightweight metadata blocks (~50 tokens per file) to locate exact information before selectively reading deep content. As an engineering target, this compresses initial prompt overhead by over 98%.

### 2. Progressive Disclosure via Directory Index Routers
Instead of dumping an entire repository into active memory, OKF uses hierarchical `index.md` files at directory roots. An AI agent reads the root `index.md` first to build a topographical map of available domains, traversing deeper into specific concept files only when required for immediate execution.

### 3. Zero-Loss Persistent Memory & Instant Reanimation
By maintaining session walkthrough anchors (`task.md`, `walkthrough.md`, `palace_registry.md`) structured with OKF frontmatter, AI digital twins (such as Google Jules, Google Antigravity, Claude, and Copilot) reanimate instantly with full historical mental state across chat session resets or machine reboots.

### 4. The Artifact Pyramid & Zero-Cost Context Prediction
OKF knowledge bundles in DSOM stratify knowledge into an ontological pyramid:
- **Layer 1 (L1) — Strategic Synthesis:** High-level executive summaries and operational playbooks (for Orchestrator agents).
- **Layer 2 (L2) — Focused Analysis:** Deep domain-specific investigations and architecture maps (for Worker agents).
- **Layer 3 (L3) — Raw Dossiers:** Unaltered transcripts, raw telemetry, and code references (for Validator agents).

To enable zero-cost context prediction, every L1 and L2 document appends a structured `sources` block at the bottom of its YAML frontmatter and explicit inline references, pairing Markdown links with single-line target descriptions. This allows agents to evaluate relevance without triggering additional filesystem reads.

---

## OKF Technical Specification & Conformance Rules

### OKF v0.2 Complete Frontmatter Schema

Every Markdown document inside an OKF knowledge bundle MUST begin with a valid YAML frontmatter block enclosed by triple dashes (`---`) at line 1, column 1. OKF v0.2 specifies 13 mandatory metadata fields:

| Field | Type | Description | Example Value |
| :--- | :--- | :--- | :--- |
| `okf_version` | string / float | Specification version format (MUST be `"0.2"`). | `"0.2"` |
| `type` | string | Semantic category (`explanation`, `howto`, `tutorial`, `reference`, `overview`, `summary`, `agent_instructions`, `spatial_memory`). | `"explanation"` |
| `title` | string | Human- and machine-readable title. | `"Open-Source MPC Wallet Architecture"` |
| `timestamp` | string | ISO 8601 UTC timestamp of creation or major revision. | `"2026-08-25T00:00:00Z"` |
| `topics` | list[string] | Array of lower-case semantic tags for zero-cost discovery. | `["mpc", "cb-mpc", "cryptography"]` |
| `description` | string | Concise 1–2 sentence summary used for semantic routing. | `"Technical explanation of Coinbase cb-mpc integration."` |
| `resource` | string | Canonical URI or file path identifier. | `"file:///docs/explanation/mpc.md"` |
| `sources` | list[string] | Array of origin URLs, file paths, or ADRs used for synthesis. | `["README.md", "src/dca_service/core/key_management.py"]` |
| `generated` | string | Agent identifier, author, or generator tool name. | `"jules"` |
| `verified` | boolean | Verification flag confirming content validation. | `true` |
| `status` | string | Document lifecycle state (`approved`, `draft`, `deprecated`). | `"approved"` |
| `stale_after` | string | ISO 8601 UTC date when knowledge must be re-evaluated. | `"2027-08-25T00:00:00Z"` |
| `language` | string | IETF BCP 47 language code (`en-GB`). | `"en-GB"` |

---

## Concrete OKF v0.2 Code Example

Below is the canonical YAML frontmatter structure enforced across all Markdown files in this project:

```yaml
---
okf_version: "0.2"
type: "architecture_concept"
title: "🛡️ The Master Guide to AI Guardrails & Custom Validators (DSOM Protocol)"
timestamp: "2026-08-22T07:10:00Z"
topics: ["guardrails", "validation", "ast", "mcp", "dsom", "twilight-state", "security", "okf"]
description: "The definitive, comprehensive master guide to AI guardrails and custom validator architectures in the Deep State of Mind (DSOM) framework."
resource: "file:///docs/governance/AI-GUARDRAILS-MASTER-GUIDE.md"
sources: [
  "https://guardrailsai.com/guardrails/docs/how-to-guides/custom_validators",
  "docs/governance/DSOM-CUSTOM-VALIDATORS-GUIDE.md",
  "docs/governance/DSOM-TRI-PHASIC-COGNITIVE-ARCHITECTURE.md",
  ".agents/AGENTS.md"
]
generated: "google-antigravity"
verified: true
status: "approved"
stale_after: "2027-08-22T00:00:00Z"
language: "en-GB"
---
```

---

## Frontmatter Invariants & Rules

1. **Line 1 Column 1 Invariant:** The opening `---` fence MUST start at byte index 0 (no BOM, no leading whitespace or newlines).
2. **Mandatory Field Invariant:** Every document MUST contain all 13 OKF v0.2 fields.
3. **Quoting Rules:** Strings containing colons (`:`), brackets (`[]`), braces (`{}`), commas (`,`), or emojis MUST be double-quoted. `okf_version` MUST be specified as `"0.2"`.
4. **Preservation of Raw Timestamps:** Compliance scripts and PyYAML loaders MUST process timestamps as strings (`"2026-08-25T00:00:00Z"`) without converting them to native Python datetime objects.
5. **Language Standard:** All system documentation and metadata MUST use UK English (`"en-GB"`) spelling (e.g. `initialise`, `prioritise`, `segregated`).

---

## Verification & Link Validation

Verify repository-wide OKF v0.2 compliance and execute system unit tests:

```bash
# Execute pytest suite including summary generator tests
uv run pytest

# Re-generate SUMMARY.md index
uv run python tools/generate_summary.py
```
