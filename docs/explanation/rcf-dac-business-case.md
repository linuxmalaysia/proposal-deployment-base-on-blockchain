---
okf_version: "0.2"
type: "explanation"
title: "RCF & DAC Proposal: 2. Business Case — Research as an Asset Class"
timestamp: "2026-08-25T00:00:00Z"
topics: ["rcf", "dac", "asset-class", "value-creation", "mystie", "mranti"]
description: "Business case for treating university research outputs as an investable institutional asset class and aligning with national Malaysian innovation frameworks."
resource: "file:///docs/explanation/rcf-dac-business-case.md"
sources: ["docs/explanation/research-commercialisation-fund-dac-proposal.md", ".agents/AGENTS.md"]
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# 2. Business Case: Research as an Asset Class

## Executive Overview

The traditional paradigm of university technology transfer treats research outputs — patents, software code, experimental datasets, industrial designs, and trade secrets — as administrative artifacts or compliance metrics for academic promotion. This passive posture results in vast inventories of institutional intellectual property (IP) lingering indefinitely in legal registries without commercial adoption.

This proposal introduces a fundamental strategic paradigm shift: **reframing university research as an investable, institutional asset class**. Managing research outputs under institutional asset management principles enables universities to unlock significant economic value, accelerate technology transfer, and attract private and venture capital.

---

## 2.1 Reframing Research as an Investable Asset

### Portfolio Management vs. Passive Record-Keeping

Managing research as an asset class requires adopting the disciplined practices of institutional investment management. Rather than viewing research outputs as static files:
- **Active Asset Management:** Each research output is identified, catalogued, assigned a unique digital identity, rated for technology and market readiness, and continuously optimised for commercialisation pathways.
- **Pipeline Visibility:** Capital providers, venture builders, and industrial partners gain clear visibility into a structured pipeline of investment-ready opportunities categorised by maturity, sector, and risk profile.
- **Dynamic Portfolio Optimization:** University management can allocate internal grant resources dynamically toward research outputs demonstrating high Market Readiness Scores and strong intellectual property protection.

```text
+-----------------------------------------------------------------------+
|                 TRADITIONAL vs. ASSET CLASS MODEL                     |
+-----------------------------------------------------------------------+
| Traditional Model:                                                    |
| Research Output --> Academic Journal --> Patent Grant --> File Cabinet|
|                                                                       |
| Asset Class Model:                                                    |
| Research Output --> Digital Asset ID --> Certification & Rating      |
|                 --> Institutional Portfolio --> Capital Allocation    |
+-----------------------------------------------------------------------+
```

---

## 2.2 Trusted Digital Research Assets

### Institutional Characteristics of an Asset Class

For research outputs to function effectively as an investable asset class, they must possess the core characteristics that financial investors demand:
1. **Provenance & Chain of Title:** Verifiable, immutable records documenting inventorship, laboratory origin, funding source history, and legal assignment.
2. **Verifiability:** Cryptographically hashed, tamper-evident digital documentation verifying experimental records, test results, and prototype benchmarks.
3. **Comparability:** Standardised assessment frameworks (such as Technology Readiness Level [TRL 1–9] and composite Market Readiness Scores) that allow investors to compare projects objectively.
4. **Information Liquidity:** Permissioned, transparent due diligence portals that allow qualified investors to evaluate asset viability rapidly under strict confidentiality protocols.

### The Role of Digital Research Certificates

The Digital Asset Custodian (DAC) operationalises these requirements by issuing a **Digital Asset Certificate** for every registered research output. Stored securely within Percona Server for PostgreSQL with audit logs tracked in TimescaleDB hypertables, each certificate links the research asset's unique Digital Research ID directly to its verified evidence base and change ledger.

---

## 2.3 Strategic Alignment with National Initiatives

### Policy Framework Alignment

The Research Commercialisation Fund (RCF) and Digital Asset Custodian (DAC) model directly aligns with national innovation policies and institutional mandates in Malaysia:

- **MOSTI National Science, Technology and Innovation Policy (DSTIN):** Supports national targets to elevate commercialisation rates and gross expenditure on R&D (GERD).
- **10-10 Malaysian Science, Technology, Innovation and Economy (MySTIE) Framework:** Integrates 10 system science and technology drivers with 10 socio-economic sectors to maximise economic yield from local research.
- **MRANTI Commercialisation Mandate:** Aligns with MRANTI’s Strategic Research Fund (SRF) and National Technology & Innovation Sandbox (NTIS) by establishing a structured feeder pipeline of verified research assets.
- **MOSTI-MyIPO IPR Marketplace Portal:** Mirrors national efforts to centralise, standardise, and share intellectual property data across ministries and research universities to facilitate licensing and joint ventures.

---

## 2.4 Expected Value Creation

Implementing the RCF/DAC framework yields measurable returns across five core strategic dimensions:

| Value Driver | Description & Strategic Impact |
| :--- | :--- |
| **Diversified Revenue Streams** | Generates recurring licensing royalties, equity dividends from spin-off ventures, and upfront assignment fees, reducing reliance on tuition revenue and public research grants. |
| **Shorter Time-to-Market** | Accelerates technology transfer cycles by eliminating manual due diligence delays and matching industry partners with pre-assessed, verified research assets. |
| **Higher Investor Confidence** | Increases average deal size and valuation equity entries by presenting standardised TRL scores, clean IP ownership chains, and cryptographically verified proof packages. |
| **National Grant Positioning** | Secures higher success rates for major national co-investment funds (e.g., MRANTI SRF, NTIS, Applied Innovation Fund) by providing instant access to auditable evidence packages. |
| **Auditable Impact Record** | Establishes a verifiable economic and social impact ledger, strengthening university standing in international rankings (QS/THE), accreditation reviews, and government funding allocations. |

---

## Next Steps & Related Documentation

- Proceed to Section 3: [Proposed Solution Architecture](rcf-dac-solution-architecture.md)
- Review Section 1: [Background and Problem Statement](rcf-dac-background-problem.md)
- Return to [Proposal Overview & Hub Page](research-commercialisation-fund-dac-proposal.md)
