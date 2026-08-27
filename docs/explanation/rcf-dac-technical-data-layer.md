---
okf_version: "0.2"
type: "explanation"
title: "RCF & DAC Proposal: 4. Technical Architecture & Data Layer"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# 4. Technical Architecture & Data Layer

## Executive Overview

The technical architecture of the Digital Asset Custodian (DAC) is built upon institutional principles of data sovereignty, high transactional durability, and cryptographic auditability. Percona Server for PostgreSQL with the TimescaleDB time-series hypertable extension serves as the foundational, mandatory primary backend database for the entire DAC platform.

In accordance with our dual-write architecture pattern, all transaction data, evidence metadata, asset registry states, and rating evaluations are written to PostgreSQL first before broadcasting to any optional distributed ledger or blockchain notarisation layer.

---

## 4.1 Platform Design Principles

The technical design of the DAC adheres to five foundational engineering principles:

```
+-----------------------------------------------------------------------+
|                       PLATFORM DESIGN PRINCIPLES                       |
+-----------------------------------------------------------------------+
|  1. SINGLE SOURCE OF TRUTH                                            |
|     - Percona PostgreSQL primary backend & relational engine         |
|                                                                       |
|  2. TRUST BY DESIGN                                                   |
|     - SHA-256 cryptographic hashing & dual-write transaction logs     |
|                                                                       |
|  3. LAYERED ACCESS CONTROL                                            |
|     - Strict Role-Based Access Control (RBAC) & NDA-gated access      |
|                                                                       |
|  4. COMPLIANCE BY DEFAULT                                             |
|     - Aligned with PDPA 2010, university IP policy & MyIPO standards  |
|                                                                       |
|  5. INTEROPERABILITY                                                  |
|     - REST/GraphQL APIs connecting to MRANTI, MyIPO & grant portals   |
+-----------------------------------------------------------------------+
```

1. **Single Source of Truth:** One authoritative database record per research asset stored within Percona Server for PostgreSQL, integrating directly with existing institutional research management systems (RADIS/URMS), grant databases, and patent registries.
2. **Trust by Design:** Every certificate, evidence document, and evaluation score is cryptographically hashed (SHA-256) and timestamped. An optional distributed ledger (blockchain) notarisation layer can be enabled for public tamper-evidence via our dual-write engine.
3. **Layered Access Control:** Strict Role-Based Access Control (RBAC) separates internal researchers, faculty administrators, RCF investment committee members, and external investors. Sensitive evidence files are NDA-gated and audit-logged.
4. **Compliance by Default:** Fully compliant with Malaysia's Personal Data Protection Act 2010 (PDPA), institutional IP ownership policies, MyIPO patent filing standards, and institutional records retention requirements.
5. **Interoperability:** Modular REST and GraphQL APIs enable seamless automated data exchange with national platforms including MRANTI, MTDC, and the MOSTI-MyIPO IPR Marketplace.

---

## 4.2 Logical Architecture — Five Layers

The DAC architecture is organized into five clean, decoupled logical layers:

```
+-----------------------------------------------------------------------+
|                     LOGICAL ARCHITECTURE — 5 LAYERS                   |
+-----------------------------------------------------------------------+
| LAYER 5: IMPACT MEASUREMENT PLATFORM                                  |
| - Analytics Engine (TimescaleDB Hypertables, Return-on-Investment)    |
+-----------------------------------------------------------------------+
| LAYER 4: DASHBOARDS & PRESENTATION PORTALS                            |
| - Commercialisation Dashboard | Investor Dashboard (NDA-Gated API)    |
+-----------------------------------------------------------------------+
| LAYER 3: ASSESSMENT & SCORING ENGINE                                  |
| - TRL Calculator (1-9) | Market Readiness Score (MRS) Evaluator      |
+-----------------------------------------------------------------------+
| LAYER 2: REGISTRY & EVIDENCE REPOSITORY                               |
| - Metadata Engine | Object Store | Digital Research ID Mapper         |
+-----------------------------------------------------------------------+
| LAYER 1: INTEGRATION & INGESTION LAYER                                |
| - External Connectors (RADIS, URMS, MyIPO, Grant Databases)           |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
| PERSISTENCE ENGINE: PERCONA POSTGRESQL + TIMESCALEDB DUAL-WRITE       |
+-----------------------------------------------------------------------+
```

### Layer Details
- **Layer 1 — Integration & Ingestion:** Connectors import baseline metadata, grant records, and inventor details from legacy systems into PostgreSQL intake tables.
- **Layer 2 — Registry & Evidence Repository:** Manages core research metadata schemas and object storage pointers linked permanently to a UUID Digital Research ID.
- **Layer 3 — Assessment & Scoring Engine:** Computes standardized TRL (1–9) and composite Market Readiness Scores using automated rules and expert analyst inputs.
- **Layer 4 — Dashboards & Presentation Portals:** Serves permission-controlled web views for internal executives and external investors.
- **Layer 5 — Impact Measurement Platform:** Tracks time-series financial returns, licensing royalties, and employment metrics in TimescaleDB hypertables.

---

## 4.3 Core Data Objects

The core domain model relies on four primary data entities:

| Data Object | Purpose | Primary Storage Engine |
| :--- | :--- | :--- |
| **Digital Research ID** | Globally unique, permanent identifier assigned to every registered research asset. | Percona PostgreSQL (`uuid` primary key) |
| **Digital Asset Certificate** | Tamper-evident certificate summarizing inventorship, ownership, TRL, and evidence hashes. | Percona PostgreSQL + TimescaleDB Hash Log |
| **Technology Readiness Level (TRL)** | Standardized 1–9 technical maturity rating aligned with MRANTI SRF and NTIS standards. | Percona PostgreSQL Core Entity |
| **Market Readiness Score (MRS)** | Composite index evaluating market opportunity, competitive moat, and regulatory readiness. | Percona PostgreSQL Analytical Engine |

---

## Next Steps & Related Documentation

- Proceed to Section 5: [Proposed DAC Process — Five Phases](rcf-dac-five-phase-process.md)
- Review Section 3: [Proposed Solution Architecture](rcf-dac-solution-architecture.md)
- Return to [Proposal Overview & Hub Page](research-commercialisation-fund-dac-proposal.md)
