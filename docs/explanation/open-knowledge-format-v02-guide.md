---
okf_version: "0.2"
type: "explanation"
title: "Open Knowledge Format (OKF v0.2) Architectural Specification & Adoption Guide"
timestamp: "2026-08-25T00:00:00Z"
topics: ["okf", "dsom", "context-engineering", "provenance", "yaml-frontmatter", "diataxis", "specification"]
description: "Open Knowledge Format (OKF v0.2) architectural specification and adoption guide within the Deep State of Mind (DSOM) framework."
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

The Open Knowledge Format (OKF v0.1) was introduced by Google Cloud's Data Cloud team in June 2026 to overcome the fundamental bottlenecks of traditional Retrieval-Augmented Generation (RAG), including high token overhead and "lost-in-the-middle" attention degradation.

OKF provides a Git-native representation of knowledge assets stored as UTF-8 Markdown files with strict YAML frontmatter metadata schemas.

## Why OKF is the Core Engine of Deep State of Mind (DSOM)

```text
       +-------------------------------------------------------+
       |             Sovereign AI Workspace (DSOM)             |
       +-------------------------------------------------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+------------------+     +------------------+      +-----------------------+
|  Spatial Memory  |     |Agent Skill Library|     | OKF Frontmatter Index |
|   (task.md)      |     |  (tools/*.py)    |      |    (SUMMARY.md)       |
+------------------+     +------------------+      +-----------------------+
```

System performance advantages:
- Progressive disclosure
- Zero-Loss context preservation
- Multi-Agent interoperability

### 1. 98%+ Token & Cost Compression Ratio

By leveraging directory routers and OKF frontmatter indexing, agents load only required sub-trees into LLM context windows.

### 2. Progressive Disclosure via Directory Index Routers

`SUMMARY.md` serves as the root router for instant document discovery.

### 3. Zero-Loss Persistent Memory & Instant Reanimation

Persistent spatial memory files maintain ongoing task execution state across agent restarts.

### 4. The Artifact Pyramid & Zero-Cost Context Prediction

Structured metadata enables instant context resolution before deep file inspection.

## OKF Technical Specification & Conformance Rules

The repository's Deep State of Mind (DSOM) profile mandates 13 mandatory metadata fields for every Markdown document, whereas core OKF v0.2 specifies `type` by default and treats additional trust fields (`verified`, `generated`, `stale_after`) as opt-in profile extensions.

### OKF v0.2 Complete Frontmatter Schema

| Field | Type | Description | Example Value |
| :--- | :--- | :--- | :--- |
| `okf_version` | String | OKF specification version string | "0.2" |
| `type` | String | Diátaxis or DSOM document classification | "explanation" |
| `title` | String | Full title of document | "Open Knowledge Format (OKF v0.2)..." |
| `timestamp` | String | ISO-8601 immutable document creation timestamp | "2026-08-25T00:00:00Z" |
| `topics` | Array | Lowercase semantic tagging topics | ["okf", "dsom"] |
| `description` | String | Executive summary of document contents | "Architectural specification..." |
| `resource` | String | Permanent URI/file locator | "file:///docs/..." |
| `sources` | Array | References and parent sources | ["README.md"] |
| `generated` | String | Twin or author generator identity | "jules" |
| `verified` | Boolean | Verification status flag (DSOM profile intentionally restricts verified to a Boolean while core OKF v0.2 allows structured {by, at} mappings) | true |
| `status` | String | Document approval status | "approved" |
| `stale_after` | String | ISO-8601 expiration timestamp | "2027-08-25T00:00:00Z" |
| `language` | String | IETF BCP 47 language tag | "en-GB" |

## Concrete OKF v0.2 Code Example

```yaml
---
okf_version: "0.2"
type: "explanation"
title: "Open Knowledge Format (OKF v0.2) Architectural Specification & Adoption Guide"
timestamp: "2026-08-25T00:00:00Z"
topics: ["guardrails", "validation", "ast", "mcp", "dsom", "twilight-state", "security", "okf"]
description: "Architectural specification of OKF v0.2."
resource: "file:///docs/explanation/open-knowledge-format-v02-guide.md"
sources: ["README.md"]
generated: "google-antigravity"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---
```

## Frontmatter Invariants & Rules

1. **Line 1 Column 1 Invariant:** Frontmatter MUST begin at line 1, column 1 with `---\n`.
2. **Mandatory Field Invariant:** All 13 mandatory fields MUST be present in non-generator-owned documents (generator-owned files such as `SUMMARY.md` are explicitly exempt from the `timestamp` requirement and retain `created`). `okf_version` MUST be specified as `"0.2"`.
3. **Quoting Rules:** Strings with special characters MUST be enclosed in quotes.
4. **Preservation of Raw Timestamps:** The raw `timestamp` MUST represent the document's immutable creation time in ISO-8601 format and MUST be preserved without alteration.
5. **Language Standard:** Documentation MUST use UK English standard spelling (e.g., `initialise`, `prioritise`, `segregated`).

## Verification & Link Validation

```bash
uv run pytest
uv run python tools/generate_summary.py
```
