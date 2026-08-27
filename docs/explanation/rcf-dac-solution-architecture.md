---
okf_version: "0.2"
type: "explanation"
title: "RCF & DAC Proposal: 3. Proposed Solution Architecture"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# 3. Proposed Solution Architecture

## Executive Overview

To bridge the university technology transfer "Valley of Death" and transform research outputs into investable assets, this proposal introduces a dual-pillar solution architecture:
1. **The Research Commercialisation Fund (RCF):** The capital allocation, investment decision, and corporate governance layer.
2. **The Digital Asset Custodian (DAC):** The enterprise software backend, cryptographically verifiable evidence repository, registry, and analytics engine.

By pairing capital deployment directly with a sovereign digital custody platform, the university replaces manual, subjective project evaluations with standardised, data-driven due diligence.

---

## 3.1 The Research Commercialisation Fund (RCF)

### Fund Structure and Mandate

The RCF is established as a dedicated, ring-fenced investment vehicle structured in accordance with institutional governance requirements (e.g., a university-linked trust, a corporate Special Purpose Vehicle [SPV], or a fund-of-funds arrangement in partnership with MRANTI or MTDC).

The primary mandate of the RCF is to invest targeted pre-seed, seed, and bridge capital exclusively into university research assets that have successfully cleared the DAC's rigorous Commercialisation Assessment phase.

```text
+-----------------------------------------------------------------------+
|                    DUAL-PILLAR SOLUTION ARCHITECTURE                  |
+-----------------------------------------------------------------------+
|                                                                       |
|   +--------------------------+      +-----------------------------+   |
|   |  RESEARCH COMMERCIAL-    |      |    DIGITAL ASSET CUSTODIAN  |   |
|   |  ISATION FUND (RCF)      | <--> |            (DAC)            |   |
|   |  (Capital & Governance)  |      |   (Data, Trust & Registry)  |   |
|   +--------------------------+      +-----------------------------+   |
|                 |                                  |                  |
|                 v                                  v                  |
|      - Seed Investment                  - Asset Registry & IDs        |
|      - Corporate Structuring            - Cryptographic Evidence      |
|      - Industry Partnerships            - TRL / MRS Scorecards        |
|                                                                       |
+-----------------------------------------------------------------------+
```

### Objective Investment Scorecards

The RCF Investment Committee relies on standardised DAC outputs as its primary due diligence input:
- **Digital Asset Certificate:** Validates inventorship, legal ownership, and IP filing integrity.
- **Technology Readiness Level (TRL 1–9):** Confirms technical maturity based on verified laboratory evidence.
- **Market Readiness Score (MRS):** Evaluates total addressable market size, competitive advantage, and regulatory pathway.
- **Freedom-to-Operate (FTO) Audit:** Assesses the patent landscape and mitigates identified third-party infringement risks.

---

## 3.2 The Digital Asset Custodian (DAC) — Five Core Functions

The DAC functions as the digital operating system powering the RCF. It performs five integrated enterprise functions:

```text
+-----------------------------------------------------------------------+
|                   DAC PLATFORM — FIVE CORE FUNCTIONS                  |
+-----------------------------------------------------------------------+
|  1. DIGITAL RESEARCH ASSET REGISTRY                                   |
|     - Unique Digital Research ID assignment & lifecycle tracking      |
|                                                                       |
|  2. DIGITAL EVIDENCE REPOSITORY                                       |
|     - Hashed, version-controlled storage for IP & lab records        |
|                                                                       |
|  3. COMMERCIALISATION DASHBOARD                                       |
|     - Internal executive oversight & pipeline analytics               |
|                                                                       |
|  4. INVESTOR DASHBOARD                                                |
|     - Permissioned, NDA-gated deal discovery for investors            |
|                                                                       |
|  5. IMPACT MEASUREMENT PLATFORM                                       |
|     - Longitudinal tracking of royalties, equity & economic impact    |
+-----------------------------------------------------------------------+
```

### 1. Digital Research Asset Registry

Serves as the single, authoritative institutional registry for all research outputs generated across university faculties, Chancellor's Research Chairs, and centres of excellence. Upon registration, each asset receives a permanent, globally unique **Digital Research ID** (UUID primary key) stored within Percona Server for PostgreSQL.

### 2. Digital Evidence Repository

Provides encrypted, version-controlled storage for raw research datasets, CAD models, lab notebooks, prototype test logs, publication preprints, and MyIPO patent documents. Every document added to the repository is cryptographically hashed and timestamped to provide tamper-evident verification.

To satisfy formal tamper-evidence and audit requirements beyond simple hashing, the evidence architecture incorporates independent structural controls:
- **Append-only WORM Storage:** Write-Once-Read-Many storage rules prevent modification or deletion of raw evidence files.
- **Cryptographic Hash Signatures:** Evidence hashes are signed using institutional private keys.
- **Deletion Protection & Retention Policies:** Policy engine rules prohibit deletion of evidence assets during active custody or legal retention periods.
- **Independent Blockchain Anchoring:** Hashes are periodically committed to a public distributed ledger via our PostgreSQL/TimescaleDB dual-write sync engine.

### 3. Commercialisation Dashboard

Delivers real-time executive visibility for university leadership, Deputy Vice-Chancellors (Research & Innovation), and research office managers. The dashboard tracks the progression of research assets across all five operational phases, identifying bottlenecks, faculty performance metrics, and pending due diligence tasks.

### 4. Investor Dashboard

Offers a secure, web-accessible discovery portal for external venture capital funds, corporate innovation partners, and angel investors. Qualified investors can browse anonymised project profiles filtered by TRL, market sector, and Market Readiness Score. Access to granular evidence packages is unlocked dynamically following executed Non-Disclosure Agreements (NDAs) and role-based authorisation.

### 5. Impact Measurement Platform

Tracks long-term commercial and socio-economic outcomes resulting from RCF investment and DAC deployment. Utilising TimescaleDB time-series hypertables, the platform records licensing royalty inflows, equity valuation growth, spin-off job creation, and socio-economic impact metrics, tying all financial returns directly back to originating Digital Research IDs.

---

## Next Steps & Related Documentation

- Proceed to Section 4: [Technical Architecture & Data Layer](rcf-dac-technical-data-layer.md)
- Review Section 2: [Business Case — Research as an Asset Class](rcf-dac-business-case.md)
- Return to [Proposal Overview & Hub Page](research-commercialisation-fund-dac-proposal.md)
