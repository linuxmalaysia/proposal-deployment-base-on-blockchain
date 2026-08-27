---
okf_version: "0.2"
type: "explanation"
title: "RCF & DAC Proposal: 6. Implementation Methodology & Timeline"
timestamp: "2026-08-25T00:00:00Z"
topics: ["rcf", "dac", "roadmap", "timeline", "agile", "governance"]
description: "Hybrid agile-waterfall implementation strategy, phase-gated governance, and 24-month roadmap with eleven major milestones."
resource: "file:///docs/explanation/rcf-dac-implementation-roadmap.md"
sources: ["docs/explanation/research-commercialisation-fund-dac-proposal.md", ".agents/AGENTS.md"]
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# 6. Implementation Methodology & Timeline

## Executive Overview

The deployment of the Research Commercialisation Fund (RCF) and Digital Asset Custodian (DAC) platform follows a hybrid execution model. This approach combines phase-gated institutional governance with iterative, agile software engineering releases.

By delivering platform features incrementally — beginning with the core Percona Server for PostgreSQL registry and cryptographic evidence repository — the university achieves rapid initial operational capability while systematically expanding assessment engines and investor portals.

---

## 6.1 Rollout & Delivery Strategy

### Hybrid Execution Model

The implementation methodology balances institutional compliance and risk mitigation with agile software delivery:
- **Phase-Gated Governance:** Key policy decisions, fund legal structuring, and budget allocations follow formal university board and steering committee approvals.
- **Iterative Engineering Releases:** The DAC software suite is deployed in modular milestones, ensuring that baseline data structures and evidence storage are verified before launching analytics engines and external investor portals.

```text
+-----------------------------------------------------------------------+
|                    HYBRID EXECUTION METHODOLOGY                       |
+-----------------------------------------------------------------------+
|  GOVERNANCE STREAM (Phase-Gated Milestones)                           |
|  - Steering Committee --> Legal Structure --> Policy Alignment       |
+-----------------------------------------------------------------------+
                                  ||
                                  || Parallel Execution
                                  \/
+-----------------------------------------------------------------------+
|  ENGINEERING STREAM (Agile Platform Releases)                         |
|  - PostgreSQL MVP Registry --> Scoring Engine --> Investor Portal    |
+-----------------------------------------------------------------------+
```

---

## 6.2 Indicative 24-Month Roadmap

The multi-year implementation plan is structured into eleven key milestones across governance, technical development, business operations, and rollout workstreams:

| Timeframe | Milestone | Workstream | Key Deliverable |
| :--- | :--- | :--- | :--- |
| **Month 1–2** | RCF Governance & Legal Structuring | Governance | Steering Committee established; SPV/Trust framework defined. |
| **Month 1–3** | Phase 1: Research Inventory (Pilot Chairs) | Business | Baseline inventory of pilot Chair/CoE research outputs. |
| **Month 2–6** | DAC MVP Build: PostgreSQL Registry + Repository | Technical | DAC Registry & SHA-256 Evidence Repository live on PostgreSQL. |
| **Month 4–6** | Phase 2: Digital Asset Registration (Pilot) | Business | Digital Research IDs and initial Certificates issued for pilot cohort. |
| **Month 6–9** | DAC Dashboards & Scoring Engine Build | Technical | Commercialisation Dashboard and automated TRL/MRS engines live. |
| **Month 7–10**| Phase 3: Commercialisation Assessment | Business | Deep FTO audits and investment scorecards completed for top assets. |
| **Month 9–12**| Controlled Expansion to All Centres of Excellence | Rollout | University-wide research asset registration enabled across faculties. |
| **Month 10–16**| Phase 4: Funding & Investment; Investor Portal | Business | Investor Dashboard live; initial RCF seed capital deployed. |
| **Month 16–20**| Impact Measurement Platform Launch | Technical | TimescaleDB hypertable tracking for royalties and spin-off equity live. |
| **Month 16–24+**| Phase 5: Revenue Realisation (Ongoing) | Business | First licensing royalties and equity returns recognised by RCF. |
| **Month 24** | Full Programme Review & Steady State | Governance | Comprehensive Year-2 economic and social impact report submitted. |

---

## Next Steps & Related Documentation

- Proceed to Section 7: [Governance, Risk Management & Budget](rcf-dac-governance-budget-risks.md)
- Review Section 5: [Proposed DAC Process — Five Phases](rcf-dac-five-phase-process.md)
- Return to [Proposal Overview & Hub Page](research-commercialisation-fund-dac-proposal.md)
