---
okf_version: "0.2"
type: "explanation"
title: "Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC) Architecture Proposal"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# Establishment of a Research Commercialisation Fund (RCF) Anchored on "Research as an Asset Class" and Powered by a Digital Asset Custodian (DAC)

**Prepared for:** Vice-Chancellor / Board of Directors, Research & Innovation Management
**Prepared by:** Research Commercialisation & Innovation Office
**Date:** August 2026
**Classification:** Internal – For Deliberation

---

## Executive Summary & System Backend Mandate

Malaysian universities collectively generate a substantial pipeline of patents, prototypes, datasets, and publications every year, yet only a small fraction is ever converted into licensing income, spin-off companies, or investable ventures. The gap is rarely a shortage of good science — it is the absence of a trusted, standardised, and investor-ready system for identifying, verifying, and valuing research outputs. This is the classic "Valley of Death" that separates laboratory discovery from market impact.

This proposal recommends the establishment of a **Research Commercialisation Fund (RCF)**, built on two founding principles: research must be treated and managed as an investable **Asset Class**, and every research output entering the commercialisation pipeline must first become a **Trusted Digital Research Asset** — verifiable, traceable, and comparable in the same way a financial asset is.

The operational engine that makes this possible is the **Digital Asset Custodian (DAC)**: a single digital platform that functions simultaneously as a Digital Research Asset Registry, a Digital Evidence Repository, a Commercialisation Dashboard, an Investor Dashboard, and an Impact Measurement Platform.

### Core Architecture & Database Backend Sovereignty
To ensure enterprise durability, transactional reliability, and strict audit compliance, **Percona Server for PostgreSQL** with the **TimescaleDB** time-series hypertable extension serves as the foundational, mandatory primary backend database for the entire DAC platform. All DAC transaction data, evidence metadata, asset registry states, and rating evaluations are written to PostgreSQL first in accordance with our dual-write pattern before broadcasting to any optional distributed ledger or blockchain settlement layer.

---

## Proposal Modules & Navigation

The full architectural proposal is divided into eight modular explanation documents, detailed below:

| # | Section Title | Summary Scope & Key Highlights | Link |
| :-: | :--- | :--- | :--- |
| **1** | **Background and Problem Statement** | Institutional commercialisation gap, isolated research records, the technology "Valley of Death", and why a fund alone is insufficient without sovereign data infrastructure. | [View Section 1](rcf-dac-background-problem.md) |
| **2** | **Business Case: Research as an Asset Class** | Strategic paradigm shift to active portfolio management, trusted digital research asset characteristics, strategic alignment (MOSTI, 10-10 MySTIE, MRANTI, MyIPO), and expected value creation. | [View Section 2](rcf-dac-business-case.md) |
| **3** | **Proposed Solution Architecture** | Overview of the dual-pillar model (RCF capital layer + DAC trust layer) and the 5 core functions of the Digital Asset Custodian platform. | [View Section 3](rcf-dac-solution-architecture.md) |
| **4** | **Technical Architecture & Data Layer** | Platform design principles, 5 logical architecture layers, core data entities (Digital Research ID, Asset Certificate, TRL, Market Readiness Score), and PostgreSQL/TimescaleDB dual-write engine. | [View Section 4](rcf-dac-technical-data-layer.md) |
| **5** | **Proposed DAC Process — Five Phases** | End-to-end operational lifecycle: Phase 1 Inventory, Phase 2 Registration, Phase 3 Assessment, Phase 4 Funding & Investment, and Phase 5 Revenue Realisation. | [View Section 5](rcf-dac-five-phase-process.md) |
| **6** | **Implementation Methodology & Timeline** | Hybrid governance-engineering rollout model and detailed 24-month roadmap with workstreams and milestones. | [View Section 6](rcf-dac-implementation-roadmap.md) |
| **7** | **Governance, Risk Management & Budget** | Indicative Year 1–2 budget envelope breakdown, institutional risk matrix (IP disputes, data security/PDPA, overvaluation), and mitigation protocols. | [View Section 7](rcf-dac-governance-budget-risks.md) |
| **8** | **Conclusion & Ecosystem Precedents** | International institutional benchmarks (Stanford, Oxford, Penn, Minnesota, Stellenbosch), Malaysian national ecosystem integration (MRANTI, MyIPO), and strategic conclusions. | [View Section 8](rcf-dac-ecosystem-precedents.md) |

---

## Governance & Version Controls

- **Document Version:** `1.0.0`
- **Framework Protocol:** DSOM Protocol / Open Knowledge Format (OKF v0.2)
- **Primary Persistence Engine:** Percona Server for PostgreSQL + TimescaleDB
- **Language Standard:** UK English (`en-GB`)
