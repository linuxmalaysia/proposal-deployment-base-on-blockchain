---
okf_version: "0.2"
type: "overview"
title: "University Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC) Web Application"
timestamp: "2026-08-28T00:00:00Z"
topics: ["rcf", "dac", "web-application", "university-ip", "cloverleaf-model", "percona-postgresql"]
description: "Interactive Web Application Portal for University Leadership, Technology Transfer Officers, Researchers, and VC Investors to register, evaluate, and commercialise research assets."
resource: "file:///index.md"
sources: [
  "docs/explanation/research-commercialisation-fund-dac-proposal.md",
  "docs/explanation/rcf-dac-technical-data-layer.md",
  "docs/explanation/rcf-dac-five-phase-process.md",
  ".agents/AGENTS.md"
]
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-28T00:00:00Z"
language: "en-GB"
layout: "default"
---

# 🏛️ Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC) Web Application

Welcome to the live demonstration portal for the **University Research Commercialisation Fund (RCF)** powered by the **Digital Asset Custodian (DAC)** platform.

This application operationalises the **"Research as an Investable Asset Class"** framework prepared for university leadership, Vice-Chancellors, Technology Transfer Officers (TTOs), research deans, and external venture capital syndicates.

---

## 🎮 Interactive Web Application Portal

Select an institutional stakeholder view below to test registration, asset provenance minting, Cloverleaf quantitative valuation, RCF seed funding, and revenue-split distribution:

{::options parse_block_html="true" /}

<div class="web-app-container">

  <!-- Role Switcher Control Header -->
  <div class="role-switcher-banner">
    <div class="role-switcher-title">
      <h3>👥 Institutional Entry Point Switcher</h3>
      <p>Switch roles to experience tailored views for Researchers, University Admins, and Investors.</p>
    </div>
    <div class="role-btn-group">
      <button type="button" class="role-select-btn active" data-role="all">🌐 All Modules</button>
      <button type="button" class="role-select-btn" data-role="researcher">👩‍🔬 Researcher / Inventor</button>
      <button type="button" class="role-select-btn" data-role="admin">🏛️ University Admin / TTO</button>
      <button type="button" class="role-select-btn" data-role="investor">💼 VC / Angel Investor</button>
    </div>
  </div>

  <!-- MODULE 1: User Identity & W3C DID Registration -->
  <div class="app-module-card role-view-panel" data-role-view="researcher">
    <h3>1. User Registration & W3C Decentralised Identifier (DID) Minting</h3>
    <p>Every researcher, principal investigator, and administrative officer receives a permanent W3C DID stored in PostgreSQL 16.</p>

    <form id="user-reg-form">
      <div class="form-grid">
        <div class="form-group">
          <label for="reg-fullname">Full Name & Title</label>
          <input type="text" id="reg-fullname" value="Prof. Dr. Harisfazillah Jamel" placeholder="e.g. Dr. Jane Doe" required>
        </div>
        <div class="form-group">
          <label for="reg-role">Institutional Role</label>
          <select id="reg-role">
            <option value="Lead Principal Investigator (PI)">Lead Principal Investigator (PI)</option>
            <option value="Chancellor's Research Chair">Chancellor's Research Chair</option>
            <option value="Technology Transfer Officer (TTO)">Technology Transfer Officer (TTO)</option>
            <option value="Deputy Vice-Chancellor (Research)">Deputy Vice-Chancellor (Research)</option>
            <option value="Accredited VC Partner">Accredited VC Partner</option>
          </select>
        </div>
        <div class="form-group">
          <label for="reg-dept">Faculty / CoE</label>
          <input type="text" id="reg-dept" value="Centre of Excellence in DeepTech & Nanotechnology" placeholder="e.g. Faculty of Engineering">
        </div>
        <div class="form-group">
          <label for="reg-email">Institutional Email</label>
          <input type="email" id="reg-email" value="harisfazillah@university.edu.my" placeholder="email@univ.edu.my" required>
        </div>
      </div>
      <button type="submit" class="btn">Mint Identity & Register User</button>
    </form>

    <div id="user-reg-output" style="display:none;"></div>
  </div>

  <!-- MODULE 2: Asset Registration & Evidence Vault Upload -->
  <div class="app-module-card role-view-panel" data-role-view="researcher">
    <h3>2. Research Asset Registration & Cryptographic Evidence Vault</h3>
    <p>Transforms raw laboratory discoveries, CAD files, and patent drafts into structured Digital Research Asset Certificates with AES-256 evidence hashing.</p>

    <form id="asset-reg-form">
      <div class="form-grid">
        <div class="form-group">
          <label for="asset-title">Research Project / Prototype Title</label>
          <input type="text" id="asset-title" value="Graphene-Enhanced Solid State Lithium-Air Battery Cell" required>
        </div>
        <div class="form-group">
          <label for="asset-trl">Initial Technology Readiness Level (TRL)</label>
          <select id="asset-trl">
            <option value="1">TRL 1 - Basic Principles Observed</option>
            <option value="2">TRL 2 - Technology Concept Formulated</option>
            <option value="3" selected>TRL 3 - Experimental Proof of Concept (RCF Kickstart Eligible)</option>
            <option value="4">TRL 4 - Lab Component Validation (MRANTI SRF Target)</option>
            <option value="5">TRL 5 - System Validation in Relevant Environment</option>
            <option value="6">TRL 6 - System Prototype Demonstration (NTIS Sandbox Target)</option>
            <option value="7">TRL 7 - Prototype Demonstration in Operational Environment</option>
          </select>
        </div>
        <div class="form-group">
          <label for="asset-file">Evidentiary File Reference</label>
          <input type="text" id="asset-file" value="lab_notebook_vol4_patent_draft.pdf">
        </div>
      </div>
      <div class="form-group" style="margin-bottom: 1rem;">
        <label for="asset-abstract">Abstract & Scientific Innovation Summary</label>
        <textarea id="asset-abstract" rows="2">Energy density exceeding 650 Wh/kg with 1,500 cycle life validated under laboratory simulated conditions.</textarea>
      </div>
      <button type="submit" class="btn">Register Asset & Generate SHA-256 Evidence Hash</button>
    </form>

    <div id="asset-reg-output" style="display:none;"></div>
  </div>

  <!-- MODULE 3: Cloverleaf Quantitative Scoring Engine -->
  <div class="app-module-card role-view-panel" data-role-view="admin">
    <h3>3. Commercialisation Assessment: Cloverleaf Scoring Engine (>180 Qualification)</h3>
    <p>Evaluates assets across 26 quantitative criteria grouped into 4 dimensions. Assets scoring <strong>>180 / 260 points</strong> achieve investment-grade status for RCF capital deployment.</p>

    <div class="slider-container">
      <div class="slider-header">
        <span>1. Technology Strengths (Max 60 Pts) [Min Target: 42]</span>
        <span id="val-tech">48 / 60</span>
      </div>
      <input type="range" id="score-tech" class="range-slider" min="0" max="60" value="48">
    </div>

    <div class="slider-container">
      <div class="slider-header">
        <span>2. Market Attractiveness (Max 80 Pts) [Min Target: 55]</span>
        <span id="val-market">65 / 80</span>
      </div>
      <input type="range" id="score-market" class="range-slider" min="0" max="80" value="65">
    </div>

    <div class="slider-container">
      <div class="slider-header">
        <span>3. Commercialisation Avenues (Max 60 Pts) [Min Target: 42]</span>
        <span id="val-comm">46 / 60</span>
      </div>
      <input type="range" id="score-comm" class="range-slider" min="0" max="60" value="46">
    </div>

    <div class="slider-container">
      <div class="slider-header">
        <span>4. Management & Execution Support (Max 60 Pts) [Min Target: 41]</span>
        <span id="val-mgmt">44 / 60</span>
      </div>
      <input type="range" id="score-mgmt" class="range-slider" min="0" max="60" value="44">
    </div>

    <div class="score-display-box">
      <div>COMPOSITE CLOVERLEAF MARKET READINESS SCORE (MRS)</div>
      <div class="score-number" id="total-cloverleaf-score">203 / 260</div>
      <div id="cloverleaf-status"></div>
    </div>
  </div>

  <!-- MODULE 4: Investor Data Room & RCF Capital Matchmaking -->
  <div class="app-module-card role-view-panel" data-role-view="investor">
    <h3>4. Investor Dashboard & RCF Capital Deployment Matchmaker</h3>
    <p>NDA-gated data rooms allowing accredited investors, corporate partners, and national funding bodies (MRANTI SRF / NTIS) to discover investment-ready university IP.</p>

    <table>
      <thead>
        <tr>
          <th>Asset ID & Title</th>
          <th>TRL</th>
          <th>Cloverleaf Score</th>
          <th>RCF Funding Tier</th>
          <th>Status</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>did:univ:asset-9f82a1</code><br>Graphene Solid State Battery Cell</td>
          <td><span class="lab-badge">TRL 3</span></td>
          <td><strong>203 / 260</strong></td>
          <td>Tier 1 PoC Grant (RM 150,000)</td>
          <td><span style="color:#10b981; font-weight:bold;">Cleared for Fund</span></td>
          <td><button type="button" class="btn" onclick="alert('NDA executed. Opening encrypted data room payload...');">Access Data Room</button></td>
        </tr>
        <tr>
          <td><code>did:univ:asset-4b12c8</code><br>AI Diagnostic Bio-Chip Array</td>
          <td><span class="lab-badge">TRL 5</span></td>
          <td><strong>218 / 260</strong></td>
          <td>Tier 2 Co-Investment VC (RM 2.5M)</td>
          <td><span style="color:#10b981; font-weight:bold;">Cleared for Fund</span></td>
          <td><button type="button" class="btn" onclick="alert('Term sheet request submitted to RCF Steering Committee.');">Request Term Sheet</button></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- MODULE 5: Impact Measurement & Revenue-Split Matrix -->
  <div class="app-module-card role-view-panel" data-role-view="admin">
    <h3>5. Impact Measurement Platform: Revenue Distribution Calculator</h3>
    <p>Calculates exact cash flow distributions across university treasury, originating departments, lead inventors, and the RCF re-investment pool in accordance with university IP policy.</p>

    <div class="form-grid">
      <div class="form-group">
        <label for="rev-amount">Total Ingested Revenue (MYR)</label>
        <input type="number" id="rev-amount" value="500000" step="10000">
      </div>
      <div class="form-group">
        <label for="rev-type">Revenue Stream Type</label>
        <select id="rev-type">
          <option value="royalties">Running Patent Royalties (33.3% / 33.3% / 33.4%)</option>
          <option value="licensing" selected>Licensing Milestone Fees (30% / 20% / 30% / 20% RCF)</option>
          <option value="equity">Spin-off Equity IPO Exit (35% / 10% / 25% / 30% RCF)</option>
          <option value="dividend">Spin-Off Dividend Income (25% / 15% / 30% / 30% RCF)</option>
        </select>
      </div>
    </div>

    <table>
      <thead>
        <tr>
          <th>Stakeholder Entity</th>
          <th>Allocation Percentage</th>
          <th>Calculated Allocation (MYR)</th>
        </tr>
      </thead>
      <tbody id="revenue-split-body">
        <!-- Dynamically filled by JavaScript -->
      </tbody>
    </table>
  </div>

</div>

---

## 📚 Key Strategic & Architectural Documentation

- 📄 **[Research Commercialisation Fund (RCF) & DAC Proposal](docs/explanation/research-commercialisation-fund-dac-proposal.html)** - Master proposal prepared for Vice-Chancellor & Board of Directors.
- 💼 **[Business Case: Research as an Asset Class](docs/explanation/rcf-dac-business-case.html)** - Paradigm shift, trusted digital research assets, and national policy alignment (MOSTI, 10-10 MySTIE, MRANTI, MyIPO).
- ⚡ **[Technical Architecture & Data Layer](docs/explanation/rcf-dac-technical-data-layer.html)** - Percona Server for PostgreSQL 16 + TimescaleDB single source of truth and transactional outbox pattern.
- 🔄 **[Five-Phase Execution Pipeline](docs/explanation/rcf-dac-five-phase-process.html)** - Phase-gated methodology from lab inventory to revenue realization.
- 📊 **[Governance & 24-Month Implementation Roadmap](docs/explanation/rcf-dac-governance-budget-risks.html)** - Steering committee structure, RM 7.9M - RM 20.5M budget breakdown, and risk mitigations.
- 🌐 **[International Precedents & Ecosystem Integration](docs/explanation/rcf-dac-ecosystem-precedents.html)** - Case studies (Stanford, Oxford, Penn, Stellenbosch) and Malaysian ecosystem links.
- 📖 **[Web Application User Guide](docs/tutorials/web-application-user-guide.html)** - Comprehensive step-by-step user guide for all stakeholder personas.
