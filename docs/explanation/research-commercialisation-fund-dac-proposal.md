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

## 1. Background and Problem Statement

### 1.1 The Commercialisation Gap
Universities invest heavily in research through Chancellor's Research Chairs, centres of excellence, and grant-funded laboratories, but the resulting assets — patents, prototypes, datasets, know-how — typically sit in disconnected records: faculty spreadsheets, individual researcher files, legacy grant-management systems, and paper patent files. There is no single, trusted source of truth that tells management, investors, or industry partners what research assets exist, who owns them, how mature they are, and what they might be worth.

Nationally, this is recognised as the technology "Valley of Death" — the stage between proof-of-concept and market-ready product where promising research stalls for lack of structured funding, credible readiness data, and investor confidence. Malaysia's own national programmes, including MRANTI's Strategic Research Fund and the National Technology & Innovation Sandbox (which requires a minimum TRL 6 for entry), exist precisely to help projects cross this gap — but they can only fund what has already been identified, documented, and rated. A university that cannot produce this documentation on demand will consistently under-access both national and private capital.

### 1.2 Why a Fund Alone Is Not Enough
A commercialisation fund without a trusted data layer behind it recreates the same problem in a new form: capital being allocated on the basis of incomplete or unverifiable information about the underlying research asset. Investors, industry partners, and internal decision-makers all need the same thing — confidence that a research output is what it claims to be, at the maturity level claimed, with clean ownership. This proposal therefore pairs the RCF (the capital and governance layer) with the DAC (the trust and data layer) as a single, integrated solution.

---

## 2. Business Case: Research as an Asset Class

### 2.1 Reframing Research as an Investable Asset
The core business idea is to manage university research the way a fund manager manages a portfolio of assets: each research output is identified, catalogued, rated for maturity and market potential, and made discoverable to capital providers. This reframing changes the university's posture from a passive generator of publications and patents to an active manager of an IP and innovation portfolio with a defined pipeline of investable opportunities.

### 2.2 Trusted Digital Research Assets
For research to behave like an asset class, it must carry the same qualities investors expect of any tradable asset: provenance, verifiability, comparability, and liquidity of information. The DAC operationalises this through digital certification — each asset receives a unique Digital Research ID and a Digital Asset Certificate that anchors ownership, inventorship, key documents, and status in a single verifiable record, with an auditable change history stored securely within Percona Server for PostgreSQL.

### 2.3 Strategic Alignment
The RCF/DAC model directly supports national innovation priorities — MOSTI's Science, Technology and Innovation Policy, the 10-10 MySTIE framework, and MRANTI's mandate to raise the number of commercialised research products. It also mirrors the direction already taken by MOSTI and MyIPO, whose memorandum of understanding to share intellectual property and funding data through the IPR Marketplace portal reflects the same underlying principle: commercialisation accelerates when research and IP data are centralised, standardised, and shared under proper controls.

### 2.4 Expected Value Creation
- **New Revenue Streams:** Diversified revenue streams for the university through royalties, licensing fees, equity stakes, and spin-off dividends, reducing reliance on tuition and government grants.
- **Shorter Time-to-Market:** Materially shorter time-to-market for research with commercial potential, by giving assessment, funding, and industry-matching a structured pipeline instead of ad-hoc faculty effort.
- **Higher Investor Confidence:** Larger average deal size, because due diligence data (TRL, ownership, evidentiary documents) is standardised and instantly retrievable.
- **National Grant Positioning:** Stronger positioning for national grants and co-investment (MRANTI SRF, NTIS, Applied Innovation Fund) which increasingly require TRL evidence and structured project data at the point of application.
- **Auditable Impact Record:** An auditable impact record — economic and social — that strengthens the university's case in national rankings, accreditation, and government funding negotiations.

---

## 3. Proposed Solution Architecture

### 3.1 The Research Commercialisation Fund (RCF)
The RCF is proposed as a dedicated, ring-fenced fund — structured as a university-linked trust, corporate vehicle, or fund-in-fund arrangement in partnership with MRANTI/MTDC — mandated to invest in research assets that have cleared the DAC's Commercialisation Assessment stage. The fund's investment committee draws on DAC data (TRL, Market Readiness Score, evidentiary certificate) as its primary due-diligence input, replacing ad-hoc, document-heavy evaluation with a standardised scorecard.

### 3.2 The Digital Asset Custodian (DAC)
The DAC is the digital backbone of the RCF. It performs five core functions:
1. **Digital Research Asset Registry:** A single, authoritative repository of all research assets across Chancellor's Research Chairs and centres of excellence, each carrying a unique Digital Research ID.
2. **Digital Evidence Repository:** Secure, version-controlled storage of research documentation, patent filings, prototype records, and development logs that constitute the evidentiary basis of each Digital Asset Certificate.
3. **Commercialisation Dashboard:** An internal management view showing every asset's stage in the five-phase DAC process, bottlenecks, and owner accountability.
4. **Investor Dashboard:** A permissioned, external-facing view through which qualified investors and industry partners can browse anonymised or NDA-gated opportunities, filter by TRL, sector, and Market Readiness Score, and initiate structured due diligence.
5. **Impact Measurement Platform:** Tracks realised outcomes (revenue, jobs created, products launched, social/economic impact indicators) back to the originating research asset, closing the loop from registration to realised value.

---

## 4. Technical Architecture & Data Layer

### 4.1 Platform Design Principles
- **Single Source of Truth:** One authoritative record per research asset, backed by Percona Server for PostgreSQL and integrated with existing research management, grant, and patent systems.
- **Trust by Design:** Every certificate is cryptographically hashed and timestamped; an optional distributed-ledger (blockchain) notarisation layer can be enabled for tamper-evident certificates via our PostgreSQL/TimescaleDB dual-write engine.
- **Layered Access Control:** Role-based permissions separate researcher, faculty administrator, RCF investment committee, and external investor views; investor access to sensitive evidence is NDA-gated and logged.
- **Compliance by Default:** Architecture aligns with Malaysia's Personal Data Protection Act 2010 (PDPA), university IP policy, MyIPO filing requirements, and the university's records-retention obligations.
- **Interoperability:** Open APIs allow the DAC to exchange data with MRANTI, MyIPO's IPR Marketplace, MTDC, and grant-management platforms.

### 4.2 Logical Architecture — Five Layers
1. **Layer 1 — Integration & Ingestion:** Connectors to existing research information systems, grant databases, patent-filing records, and finance systems pull baseline data into PostgreSQL intake tables.
2. **Layer 2 — Registry & Evidence Repository:** Document-management core with metadata schema (asset type, inventors, chair/centre of origin, funding source, IP status) and version-controlled file storage linked to a Digital Research ID.
3. **Layer 3 — Assessment & Scoring Engine:** Rules-based and analyst-assisted engine calculating Technology Readiness Level (TRL 1–9 scale) and composite Market Readiness Score.
4. **Layer 4 — Dashboards:** Commercialisation and Investor Dashboards built on top of relational PostgreSQL views and permissioned APIs.
5. **Layer 5 — Impact Measurement Platform:** Analytics layer using TimescaleDB hypertable tracking for realised royalties, licences, equity value, and spin-off performance.

### 4.3 Core Data Objects
| Data Object | Purpose | Primary Storage Engine |
| :--- | :--- | :--- |
| **Digital Research ID** | Unique, permanent identifier assigned to every registered research asset. | Percona PostgreSQL (`uuid` primary key) |
| **Digital Asset Certificate** | Tamper-evident certificate summarising ownership, evidence, and status. | Percona PostgreSQL + TimescaleDB Hash Log |
| **Technology Readiness Level (TRL)** | 1–9 scale indicating technical maturity (aligned with MRANTI SRF & NTIS). | Percona PostgreSQL Core Entity |
| **Market Readiness Score** | Composite index of market size, competitive position, and regulatory pathway. | Percona PostgreSQL Analytical Engine |

---

## 5. Proposed DAC Process — Five Phases

1. **Phase 1 — Research Inventory:** Systematically identify and catalogue every research asset held under Chancellor's Research Chairs and centres of excellence, feeding baseline records directly into PostgreSQL.
2. **Phase 2 — Digital Asset Registration:** Formally register inventoried outputs into the DAC, issuing a Digital Research ID, Digital Asset Certificate, TRL rating, and preliminary Market Readiness Score.
3. **Phase 3 — Commercialisation Assessment:** Perform deep evaluation of market potential, freedom-to-operate, and economic value for high-priority assets.
4. **Phase 4 — Funding and Investment:** Match cleared assets with RCF capital, MRANTI/MTDC co-investment, or direct corporate partnerships using the Investor Dashboard.
5. **Phase 5 — Revenue Realisation:** Track returns (royalties, licensing, equity holdings, spin-offs) back to originating Digital Research IDs via the Impact Measurement Platform.

---

## 6. Implementation Methodology & Timeline

### 6.1 Rollout & Delivery Strategy
A hybrid approach is adopted: phase-gated governance combined with iterative DAC platform releases. Development starts with the PostgreSQL Registry and Evidence Repository MVP before deploying scoring engines and investor portals.

### 6.2 Indicative 24-Month Roadmap
| Timeframe | Milestone | Workstream | Key Deliverable |
| :--- | :--- | :--- | :--- |
| **Month 1–2** | RCF governance and legal structuring | Governance | Steering Committee established |
| **Month 1–3** | Phase 1: Research Inventory (pilot Chairs/CoE) | Business | Baseline asset inventory |
| **Month 2–6** | DAC MVP build: PostgreSQL Registry + Repository | Technical | DAC Registry live (pilot) |
| **Month 4–6** | Phase 2: Digital Asset Registration (pilot cohort) | Business | Digital IDs and Certificates issued |
| **Month 6–9** | DAC dashboards & scoring engine built | Technical | Commercialisation Dashboard live |
| **Month 7–10**| Phase 3: Commercialisation Assessment | Business | Investment-ready business cases |
| **Month 9–12**| Controlled expansion to all centres of excellence | Rollout | University-wide registration |
| **Month 10–16**| Phase 4: Funding & Investment; Investor Dashboard | Business | First RCF deployments |
| **Month 16–20**| Impact Measurement Platform launched | Technical | Full DAC platform live |
| **Month 16–24+**| Phase 5: Revenue Realisation — ongoing | Business | First revenue recognised |
| **Month 24** | Full programme review & steady state | Governance | Year-1 impact report |

---

## 7. Governance, Risk Management & Budget

### 7.1 Indicative Budget Envelope
- **DAC Platform Development:** RM 1.5m – 3.0m
- **Legal & Fund Structuring:** RM 0.3m – 0.6m
- **Human Capital (Year 1):** RM 0.8m – 1.2m
- **RCF Seed Capital (Year 1 Deployable):** RM 5.0m – 15.0m
- **Change Management & Training:** RM 0.2m – 0.4m
- **Monitoring & Impact Reporting:** RM 0.15m – 0.3m

### 7.2 Key Risks & Mitigations
- **Disputed IP Ownership:** Certificates capture inventorship at point of registration, cross-checked against university IP policy before certification.
- **Data Security / Confidential Exposure:** Role-based access control, encrypted PostgreSQL storage, and strict NDA-gated investor access logs.
- **Overvaluation / Inconsistent Scoring:** Standardised rules-based TRL and Market Readiness Score methodology validated by external valuers.

---

## 8. Conclusion & Ecosystem Precedents

The RCF and DAC model converts dormant academic research into an investable, asset-class pipeline. Supported by international benchmarks (Stanford, Oxford, Penn, Minnesota, Stellenbosch) and aligned with Malaysian ecosystem mechanisms (MRANTI SRF, NTIS, MOSTI-MyIPO IPR Marketplace), the system provides transparent governance backed by an enterprise-grade Percona PostgreSQL and TimescaleDB dual-write engine.
