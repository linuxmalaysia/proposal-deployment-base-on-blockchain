---
okf_version: "0.2"
type: "tutorial"
title: "University RCF & DAC Web Application User Guide"
timestamp: "2026-08-28T00:00:00Z"
topics: ["rcf", "dac", "user-guide", "web-application", "tutorial", "university-ip"]
description: "Step-by-step user guide for University Leadership, Technology Transfer Officers, Researchers, and VC Investors navigating the RCF and DAC web application portal."
resource: "file:///docs/tutorials/web-application-user-guide.md"
sources: [
  "index.md",
  "docs/explanation/research-commercialisation-fund-dac-proposal.md",
  "docs/explanation/rcf-dac-technical-data-layer.md",
  ".agents/AGENTS.md"
]
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-28T00:00:00Z"
language: "en-GB"
---

# University Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC) Web Application User Guide

This step-by-step tutorial guides institutional stakeholders through operating the **Digital Asset Custodian (DAC)** web application portal.

---

## 👥 Persona-Based Entry Points

The platform supports four primary user personas across the university innovation lifecycle:

| Persona | Primary Goal | Web App Entry Point | Key Capabilities |
| :--- | :--- | :--- | :--- |
| **Researcher / Lead PI** | Protect scientific priority & register IP | Module 1 & Module 2 | Mint W3C DID, upload evidence files, generate SHA-256 hashes |
| **Technology Transfer Officer (TTO)** | Assess commercial readiness & manage pipeline | Module 3 & Module 5 | Execute Cloverleaf MRS scoring (>180 target), calculate revenue splits |
| **University Leadership (VC / Deans)** | Monitor pipeline performance & approve grants | RCF Steering Dashboard | Approve Tier 1 Kickstarter Grants (RM 50k-250k) & track ROI |
| **Accredited VC / Angel Investor** | Discover investment-ready university IP | Module 4 Investor Portal | Access NDA-gated data rooms, review TRL/MRS ratings, request term sheets |

---

## 🚀 Step-by-Step Workflow Instructions

### Step 0: Check Database Connection & Automatic Schema Verification Status (`/db-status`)

1. Open [/db-status](/db-status) or click **🔌 DB Connection Status** in the application banner.
2. Review real-time connection status (`SUCCESSFULLY CONNECTED`), latency diagnostics, masked configuration status flags (`DATABASE_URL_CONFIGURED`, `SUPABASE_SECRET_KEY_CONFIGURED`), and verified project schema tables (`users`, `assets`, `cloverleaf_scores`, `revenue_splits`, `blockchain_transactions`).
3. On application startup or deployment on Render.com, the system automatically runs a fail-safe schema auto-check routine (`auto_check_and_build_schema`), verifying and building any missing database tables defined in `docs/schema.sql` without overwriting existing data.
4. Click **Re-test Database Connection** or access [/api/db-status](/api/db-status) for JSON metrics.

### Step 0.1: System Authentication & User Account Management (`/login` & `/user-management`)

1. Open [/login](/login) or click **🔐 System Login** in the application banner or top navigation bar.
2. Authenticate using system credentials (e.g., initial superuser `dca_sys_root` or admin manager `dca_admin_mgr`).
   - *Note on Superuser Reset:* Superuser (`dca_sys_root`) password resets are restricted to direct SQL database execution or `SUPERUSER_INITIAL_PASSWORD` environment variable configuration (see [How to Reset Superuser Password via SQL](../how-to/reset-superuser-password-and-manage-users.html)).
3. Upon successful login, the system issues an HMAC-SHA256 signed JWT Bearer token stored securely in browser storage.
4. Access [/user-management](/user-management) or click **👥 User Management** to view registered system accounts, create new administrator or operator accounts, or reset user passwords.

### Step 1: User Identity & W3C DID Registration (Module 1)

1. Open the [Interactive Web Application Portal](../../index.html).
2. Enter your full name, institutional role, faculty/centre of excellence, and institutional email.
3. Click **Mint Identity & Register User**.
4. The system issues a W3C Decentralised Identifier (e.g., `did:univ:a8f9e12c4b...`) saved locally in browser storage (simulating PostgreSQL 16 persistence).

### Step 2: Research Asset Registration & Cryptographic Evidence Vault (Module 2)

1. Navigate to Module 2 under the **Researcher** view.
2. Enter your research title, select the current **Technology Readiness Level (TRL 1–9)**, and upload an evidentiary file reference or document.
3. Click **Register Asset & Generate SHA-256 Evidence Hash**.
4. The system computes a genuine SHA-256 cryptographic digest via `crypto.subtle.digest` over the evidence file bytes, labeled clearly as `sha256:...`.

### Step 3: Commercialisation Assessment & Cloverleaf MRS Scoring (Module 3)

1. Under the **University Admin / TTO** view, adjust the four Cloverleaf dimension sliders:
   - **Technology Strengths** (Max 60 Pts, Target ≥ 42)
   - **Market Attractiveness** (Max 80 Pts, Target ≥ 55)
   - **Commercialisation Avenues** (Max 60 Pts, Target ≥ 42)
   - **Management Support** (Max 60 Pts, Target ≥ 41)
2. Verify if the composite score strictly exceeds **180 / 260 points** (scores > 180).
3. Assets scoring > 180 are automatically marked as **Investment-Ready** and cleared for RCF Tier 1 Kickstarter Grant allocation or Tier 2 VC co-investment.

### Step 4: Investor Data Room & Capital Matchmaking (Module 4)

1. Switch to the **VC / Angel Investor** view.
2. Filter registered assets by TRL level, sector, and Cloverleaf score.
3. Click **Access Data Room** after signing digital NDAs to inspect verified evidentiary documents.
4. Click **Request Term Sheet** to initiate co-investment term negotiations with the RCF Investment Committee.

### Step 5: Impact Measurement & Revenue Split Calculation (Module 5)

1. In Module 5, input the ingested revenue amount (e.g., RM 500,000, accepting 0 or positive values).
2. Select the revenue stream type (Running Royalties, Licensing Milestone Fees, Spin-off Equity IPO Exit, or Dividends).
3. The platform automatically displays exact cash flow allocations across:
   - Central University Treasury
   - Originating Department / Laboratory
   - Lead Inventors & Scientific Team
   - RCF Re-investment Pool
