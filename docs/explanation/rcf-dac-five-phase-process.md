---
okf_version: "0.2"
type: "explanation"
title: "RCF & DAC Proposal: 5. Proposed DAC Process — Five Phases"
timestamp: "2026-08-25T00:00:00Z"
topics: ["rcf", "dac", "phases", "inventory", "registration", "assessment", "investment", "realisation"]
description: "End-to-end operational lifecycle across Phase 1 Inventory, Phase 2 Registration, Phase 3 Assessment, Phase 4 Investment, and Phase 5 Revenue Realisation."
resource: "file:///docs/explanation/rcf-dac-five-phase-process.md"
sources: ["docs/explanation/research-commercialisation-fund-dac-proposal.md", ".agents/AGENTS.md"]
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# 5. Proposed DAC Process — Five Phases

## Executive Overview

The operational lifecycle of the Digital Asset Custodian (DAC) structures the movement of university research outputs from initial laboratory discovery to commercial deployment and revenue recognition. This process is divided into five sequential, audited phases.

Each phase enforces data verification standards, ensuring that only research projects clearing explicit technical, legal, and market thresholds advance to subsequent investment stages.

```text
+-----------------------------------------------------------------------+
|                    PROPOSED DAC PROCESS — 5 PHASES                    |
+-----------------------------------------------------------------------+
|  PHASE 1: RESEARCH INVENTORY                                          |
|  - Systematically catalogue outputs from Chairs & Centres of Excellence|
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|  PHASE 2: DIGITAL ASSET REGISTRATION                                  |
|  - Issue Digital Research ID, Asset Certificate & initial TRL/MRS    |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|  PHASE 3: COMMERCIALISATION ASSESSMENT                                |
|  - FTO landscape evaluation, market sizing & valuation scorecards     |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|  PHASE 4: FUNDING AND INVESTMENT                                      |
|  - Match verified assets (minimum TRL 6) with RCF & co-investment     |
+-----------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------+
|  PHASE 5: REVENUE REALISATION                                         |
|  - Track royalties, equity dividends & economic impact via hypertables|
+-----------------------------------------------------------------------+
```

---

## 5.1 Phase 1 — Research Inventory

### Systematic Asset Discovery

Phase 1 initiates a comprehensive, systematic inventory scan across all university academic departments, Chancellor's Research Chairs, specialised centres of excellence, and grant-funded laboratories.
- **Data Collection:** Collects baseline details regarding publications, granted/pending patents, experimental software repositories, hardware prototypes, and specialised datasets.
- **Intake Database Persistence:** Raw inventory data is ingested directly into Percona Server for PostgreSQL intake staging tables.
- **Initial Classification:** Assets are tagged by scientific discipline, primary inventor, funding grant origin, and initial self-reported TRL (1–3).

---

## 5.2 Phase 2 — Digital Asset Registration

### Formal Certification & Identity Assignment

In Phase 2, inventoried outputs undergo formal onboarding into the DAC platform:
- **UUID Identity Generation:** The system assigns a permanent, globally unique **Digital Research ID** (`uuid` primary key) to the asset.
- **Digital Asset Certificate Issuance:** A cryptographically hashed certificate is generated, encapsulating legal ownership claims, co-inventors, and initial file hashes.
- **Baseline Scoring:** The Assessment Engine computes an initial verified Technology Readiness Level (TRL) and preliminary Market Readiness Score (MRS).
- **Dual-Write Notarisation:** Certificate hash logs are saved in PostgreSQL and appended to TimescaleDB time-series ledgers.

---

## 5.3 Phase 3 — Commercialisation Assessment

### Rigorous Due Diligence & Valuation

High-priority registered assets advancing past Phase 2 undergo detailed commercial due diligence led by the Research Commercialisation & Innovation Office and external subject-matter experts:
- **Freedom-to-Operate (FTO) Verification:** Conduct prior art and patent landscape analysis to assess freedom-to-operate and mitigate identified third-party infringement risks.
- **Market Sizing & Competitive Analysis:** Evaluation of Total Addressable Market (TAM), Serviceable Addressable Market (SAM), and competitive moat.
- **Regulatory Pathway Mapping:** Identification of necessary certification standards (e.g., ISO, CE Mark, MDA approval for medical devices).
- **Commercialisation Scorecard Generation:** High-performing projects (minimum TRL 6, MRS > 75/100) are certified as "Investment Ready" and published to the Investor Dashboard.

---

## 5.4 Phase 4 — Funding and Investment

### Capital Allocation & Syndicate Matching

Phase 4 connects certified "Investment Ready" digital assets with growth capital:
- **RCF Seed Deployment:** The RCF Investment Committee evaluates the standardised scorecard and approves pre-seed/seed funding rounds (RM 100k – RM 1.5m) for spin-off creation or prototype refinement for qualified assets (minimum TRL 6).
- **Syndicate & Co-Investment Matching:** Qualified external venture funds, corporate partners, and institutional bodies (e.g., MTDC, MRANTI SRF/NTIS) discover opportunities through the NDA-gated Investor Dashboard.
- **Deal Structuring:** Legal agreements (licensing agreements, equity shares, SAFE notes) are stored in the DAC Evidence Repository linked to the asset's Digital Research ID.

---

## 5.5 Phase 5 — Revenue Realisation

### Longitudinal Performance & Return Tracking

The final phase manages ongoing commercial operations and return distribution:
- **Royalty & Licensing Monetisation:** Inflows from technology licensing fees and upfront assignment payments are collected and accounted for.
- **Equity Liquidity Events:** Dividend distributions and equity exit payouts from university spin-offs are tracked.
- **Impact Analytics:** Utilising TimescaleDB time-series hypertables, financial returns, high-value job creation, and socio-economic indicators are dynamically aggregated and mapped back to originating Digital Research IDs.
- **Reinvestment Loop:** Net financial yields are recycled back into the RCF to fund subsequent cohorts of university research discoveries.

---

## Next Steps & Related Documentation

- Proceed to Section 6: [Implementation Methodology & Timeline](rcf-dac-implementation-roadmap.md)
- Review Section 4: [Technical Architecture & Data Layer](rcf-dac-technical-data-layer.md)
- Return to [Proposal Overview & Hub Page](research-commercialisation-fund-dac-proposal.md)
