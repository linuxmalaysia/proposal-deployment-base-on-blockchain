---
okf_version: "0.2"
type: "explanation"
title: "RCF & DAC Proposal: 7. Governance, Risk Management & Budget"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# 7. Governance, Risk Management & Budget

## Executive Overview

The successful operation of the Research Commercialisation Fund (RCF) and Digital Asset Custodian (DAC) requires a transparent institutional governance model, a realistic capital budgeting framework, and structured risk mitigation protocols.

This document details the indicative capital allocation required for software development, legal structuring, and deployable seed investment capital, alongside the risk mitigation strategies engineered into the DAC platform.

---

## 7.1 Indicative Budget Envelope

The capital requirements for establishing the RCF and building the DAC software backend over Year 1 and Year 2 are categorized into six core budget streams:

| Budget Item | Estimated Envelope (MYR) | Description & Resource Scope |
| :--- | :--- | :--- |
| **DAC Platform Development** | RM 1.5m – 3.0m | Custom backend development, Percona PostgreSQL database setup, TimescaleDB hypertable integration, scoring engines, and dashboard APIs. |
| **Legal & Fund Structuring** | RM 0.3m – 0.6m | Legal fees for corporate SPV/Trust setup, IP policy alignment, NDA templates, and regulatory compliance filings. |
| **Human Capital (Year 1)** | RM 0.8m – 1.2m | Salaries for technology transfer officers, patent valuation analysts, full-stack software engineers, and fund managers. |
| **RCF Seed Capital (Year 1)** | RM 5.0m – 15.0m | Ring-fenced seed investment capital allocated to certified investment-ready research assets (TRL 4–6+). |
| **Change Management & Training** | RM 0.2m – 0.4m | Faculty onboarding workshops, principal investigator training modules, user documentation, and awareness campaigns. |
| **Monitoring & Impact Reporting** | RM 0.15m – 0.3m | External auditing, independent valuation reviews, and annual socio-economic impact reporting. |

---

## 7.2 Key Risks & Mitigations

To protect institutional capital and preserve academic integrity, the platform addresses three primary risk vectors:

```
+-----------------------------------------------------------------------+
|                      RISK MITIGATION MATRIX                           |
+-----------------------------------------------------------------------+
|  RISK VECTOR 1: IP OWNERSHIP DISPUTES                                 |
|  - Certificate captures inventorship at registration; verified        |
|    against university IP policy before certification.                 |
+-----------------------------------------------------------------------+
|  RISK VECTOR 2: DATA SECURITY & CONFIDENTIAL EXPOSURE                 |
|  - Role-Based Access Control (RBAC), encrypted PostgreSQL storage &    |
|    strict NDA-gated investor audit logs.                              |
+-----------------------------------------------------------------------+
|  RISK VECTOR 3: OVERVALUATION & INCONSISTENT SCORING                  |
|  - Rules-based TRL and Market Readiness Score methodology validated  |
|    by independent external valuation experts.                         |
+-----------------------------------------------------------------------+
```

### 1. Disputed IP Ownership & Inventorship Claims
- **Risk:** Co-inventors or external research sponsors dispute legal ownership rights after funding allocation.
- **Mitigation:** Digital Asset Certificates capture inventorship claims, laboratory logs, and grant funding sources at the point of registration. Baseline legal ownership is cross-checked against university IP policy and joint research agreements before issuing an active certificate.

### 2. Data Security & Unauthorized Confidential Exposure
- **Risk:** Unauthorised access or leakage of pre-patent research data, trade secrets, or experimental code.
- **Mitigation:** Strict Role-Based Access Control (RBAC) isolates internal researcher, administration, and investor views. All evidence files stored within PostgreSQL object layers are encrypted at rest (AES-256). External investor access to granular evidence packages requires an executed NDA and is logged permanently in TimescaleDB hypertable audit records.

### 3. Overvaluation & Inconsistent Project Scoring
- **Risk:** Subjective self-reporting by faculty leads to overvalued research assets and misallocated seed capital.
- **Mitigation:** The DAC Scoring Engine enforces standardized, rules-based algorithms for calculating TRL (1–9) and Market Readiness Scores (MRS). High-value allocations require dual verification by internal technology transfer officers and independent external valuation experts.

---

## Next Steps & Related Documentation

- Proceed to Section 8: [Conclusion & Ecosystem Precedents](rcf-dac-ecosystem-precedents.md)
- Review Section 6: [Implementation Methodology & Timeline](rcf-dac-implementation-roadmap.md)
- Return to [Proposal Overview & Hub Page](research-commercialisation-fund-dac-proposal.md)
