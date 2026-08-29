/**
 * Digital Research Asset Custodian (DAC) & Research Commercialisation Fund (RCF)
 * Interactive Web Application Engine
 *
 * Governed by DSOM Protocol // OKF v0.2 Standard // Concentric Clean Architecture
 */

document.addEventListener('DOMContentLoaded', () => {
  initRoleSwitcher();
  initRegistrationForm();
  initAssetForm();
  initCloverleafCalculator();
  initRevenueCalculator();
  loadSavedRegistration();
  loadSavedAsset();
});

/* -------------------------------------------------------------------------
   1. Role Switcher Logic
   ------------------------------------------------------------------------- */
function initRoleSwitcher() {
  const roleButtons = document.querySelectorAll('.role-select-btn');
  const roleViews = document.querySelectorAll('.role-view-panel');

  if (!roleButtons.length) return;

  roleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const selectedRole = btn.getAttribute('data-role');

      roleButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      roleViews.forEach(view => {
        if (view.getAttribute('data-role-view') === selectedRole || selectedRole === 'all') {
          view.style.display = 'block';
        } else {
          view.style.display = 'none';
        }
      });
    });
  });
}

/* -------------------------------------------------------------------------
   2. User Registration & W3C DID Generator
   ------------------------------------------------------------------------- */
function initRegistrationForm() {
  const form = document.getElementById('user-reg-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const name = document.getElementById('reg-fullname').value.trim() || 'Dr. Aris Roslan';
    const role = document.getElementById('reg-role').value;
    const dept = document.getElementById('reg-dept').value.trim() || 'Faculty of Engineering & Innovation';
    const email = document.getElementById('reg-email').value.trim() || 'aris@university.edu.my';

    const hashSeed = `${name}-${role}-${dept}-${Date.now()}`;
    const did = `did:univ:${simpleHash(hashSeed).substring(0, 16)}`;

    const userRecord = { name, role, dept, email, did, timestamp: new Date().toISOString() };
    try {
      localStorage.setItem('rcf_dac_user_registration', JSON.stringify(userRecord));
    } catch (err) {
      console.warn('LocalStorage unavailable:', err);
    }

    renderRegistrationResult(userRecord);
  });
}

function renderRegistrationResult(userRecord) {
  const outputBox = document.getElementById('user-reg-output');
  if (outputBox) {
    outputBox.innerHTML = `
      <div class="result-card success">
        <h4>✅ Identity Registered & W3C DID Minted</h4>
        <div class="badge-grid">
          <p><strong>Name:</strong> ${escapeHtml(userRecord.name)}</p>
          <p><strong>Institutional Role:</strong> ${escapeHtml(userRecord.role)}</p>
          <p><strong>Faculty / Centre:</strong> ${escapeHtml(userRecord.dept)}</p>
          <p><strong>Email:</strong> ${escapeHtml(userRecord.email)}</p>
        </div>
        <div class="did-code-box">
          <span class="did-label">W3C Decentralized Identifier (DID):</span>
          <code>${escapeHtml(userRecord.did)}</code>
        </div>
        <div class="audit-badge">
          <span>BROWSER STORAGE PERSISTENCE: Simulated PostgreSQL 16 <code>users</code> table record (Persisted locally)</span>
        </div>
      </div>
    `;
    outputBox.style.display = 'block';
  }
}

function loadSavedRegistration() {
  try {
    const saved = localStorage.getItem('rcf_dac_user_registration');
    if (saved) {
      const userRecord = JSON.parse(saved);
      renderRegistrationResult(userRecord);
    }
  } catch (err) {
    console.warn('Could not load saved user registration:', err);
  }
}

/* -------------------------------------------------------------------------
   3. Asset Registration & Cryptographic Evidence Vault
   ------------------------------------------------------------------------- */
function initAssetForm() {
  const form = document.getElementById('asset-reg-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const title = document.getElementById('asset-title').value.trim() || 'High-Efficiency Graphene Supercapacitor Cell';
    const trl = document.getElementById('asset-trl').value;
    const abstract = document.getElementById('asset-abstract').value.trim() || 'Scalable energy storage prototype with 92% retention rate.';
    const fileInput = document.getElementById('asset-file');

    let fileRef = 'lab_notebook_vol4_patent_draft.pdf';
    let bytesBuffer;

    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      const file = fileInput.files[0];
      fileRef = file.name;
      bytesBuffer = await file.arrayBuffer();
    } else if (fileInput && fileInput.value) {
      fileRef = fileInput.value.trim();
      bytesBuffer = new TextEncoder().encode(fileRef);
    } else {
      bytesBuffer = new TextEncoder().encode(fileRef);
    }

    const hashBuffer = await crypto.subtle.digest('SHA-256', bytesBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hexDigest = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    const sha256Digest = `sha256:${hexDigest}`;

    const assetHashSeed = `${title}-${abstract}-${trl}-${Date.now()}`;
    const assetId = `did:univ:asset-${simpleHash(assetHashSeed).substring(0, 12)}`;
    const txOutboxId = `outbox_tx_${Math.floor(100000 + Math.random() * 900000)}`;

    const assetRecord = { title, trl, abstract, fileRef, assetId, sha256Digest, txOutboxId, timestamp: new Date().toISOString() };
    try {
      localStorage.setItem('rcf_dac_asset_registration', JSON.stringify(assetRecord));
    } catch (err) {
      console.warn('LocalStorage unavailable:', err);
    }

    renderAssetResult(assetRecord);
  });
}

function renderAssetResult(assetRecord) {
  const outputBox = document.getElementById('asset-reg-output');
  if (outputBox) {
    outputBox.innerHTML = `
      <div class="result-card success">
        <h4>📜 Digital Research Asset Registered</h4>
        <div class="badge-grid">
          <p><strong>Digital Asset ID:</strong> <code>${escapeHtml(assetRecord.assetId)}</code></p>
          <p><strong>Technical Maturity:</strong> <span class="badge badge-primary">TRL ${escapeHtml(assetRecord.trl)}</span></p>
          <p><strong>Title:</strong> ${escapeHtml(assetRecord.title)}</p>
          <p><strong>Evidence File:</strong> ${escapeHtml(assetRecord.fileRef)}</p>
        </div>
        <div class="did-code-box">
          <span class="did-label">SHA-256 Digest:</span>
          <code>${escapeHtml(assetRecord.sha256Digest)}</code>
        </div>
        <div class="outbox-status">
          <span class="status-dot green"></span>
          <strong>Simulated Transactional Outbox Status:</strong> Queued locally (Batch ID: <code>${escapeHtml(assetRecord.txOutboxId)}</code>) ready for Merkle notarisation.
        </div>
      </div>
    `;
    outputBox.style.display = 'block';
  }
}

function loadSavedAsset() {
  try {
    const saved = localStorage.getItem('rcf_dac_asset_registration');
    if (saved) {
      const assetRecord = JSON.parse(saved);
      renderAssetResult(assetRecord);
    }
  } catch (err) {
    console.warn('Could not load saved asset registration:', err);
  }
}

/* -------------------------------------------------------------------------
   4. Cloverleaf Quantitative Score Calculator (Target > 180)
   ------------------------------------------------------------------------- */
function initCloverleafCalculator() {
  const sliders = ['tech', 'market', 'comm', 'mgmt'];

  function calculate() {
    const tech = parseInt(document.getElementById('score-tech')?.value || 45, 10);
    const market = parseInt(document.getElementById('score-market')?.value || 60, 10);
    const comm = parseInt(document.getElementById('score-comm')?.value || 45, 10);
    const mgmt = parseInt(document.getElementById('score-mgmt')?.value || 45, 10);

    const techVal = document.getElementById('val-tech');
    const marketVal = document.getElementById('val-market');
    const commVal = document.getElementById('val-comm');
    const mgmtVal = document.getElementById('val-mgmt');

    if (techVal) techVal.innerText = `${tech} / 60`;
    if (marketVal) marketVal.innerText = `${market} / 80`;
    if (commVal) commVal.innerText = `${comm} / 60`;
    if (mgmtVal) mgmtVal.innerText = `${mgmt} / 60`;

    const total = tech + market + comm + mgmt;
    const totalDisplay = document.getElementById('total-cloverleaf-score');
    const statusDisplay = document.getElementById('cloverleaf-status');

    if (totalDisplay) totalDisplay.innerText = `${total} / 260`;

    if (statusDisplay) {
      if (total > 180) {
        statusDisplay.className = 'status-badge pass';
        statusDisplay.innerHTML = `
          <strong>✅ INVESTMENT-READY (Score > 180)</strong>
          <p>Eligible for RCF Tier 1 PoC Kickstarter Grant (RM 50k-250k) and Tier 2 VC Syndicate Co-Investment.</p>
        `;
      } else {
        statusDisplay.className = 'status-badge hold';
        statusDisplay.innerHTML = `
          <strong>⚠️ DEVELOPMENT REQUIRED (Score ${total} <= 180 Target)</strong>
          <p>Requires additional laboratory validation (TRL escalation) or market sizing refinement before RCF clearing.</p>
        `;
      }
    }
  }

  sliders.forEach(id => {
    const el = document.getElementById(`score-${id}`);
    if (el) {
      el.addEventListener('input', calculate);
    }
  });

  calculate();
}

/* -------------------------------------------------------------------------
   5. Impact Measurement & Revenue-Split Matrix Calculator
   ------------------------------------------------------------------------- */
function initRevenueCalculator() {
  const amountInput = document.getElementById('rev-amount');
  const typeSelect = document.getElementById('rev-type');

  if (!amountInput || !typeSelect) return;

  function calculateRevenue() {
    let rawAmount = parseFloat(amountInput.value);
    if (!Number.isFinite(rawAmount) || rawAmount < 0) {
      rawAmount = 500000;
    }

    const revType = typeSelect.value;

    let treasuryPct = 0.333;
    let deptPct = 0.333;
    let inventorPct = 0.334;
    let rcfPct = 0.0;

    if (revType === 'licensing') {
      treasuryPct = 0.30;
      deptPct = 0.20;
      inventorPct = 0.30;
      rcfPct = 0.20;
    } else if (revType === 'equity') {
      treasuryPct = 0.35;
      deptPct = 0.10;
      inventorPct = 0.25;
      rcfPct = 0.30;
    } else if (revType === 'dividend') {
      treasuryPct = 0.25;
      deptPct = 0.15;
      inventorPct = 0.30;
      rcfPct = 0.30;
    }

    const treasuryVal = rawAmount * treasuryPct;
    const deptVal = rawAmount * deptPct;
    const inventorVal = rawAmount * inventorPct;
    const rcfVal = rawAmount * rcfPct;

    const formatMYR = (val) => new Intl.NumberFormat('en-MY', { style: 'currency', currency: 'MYR' }).format(val);

    const tableBody = document.getElementById('revenue-split-body');
    if (tableBody) {
      tableBody.innerHTML = `
        <tr>
          <td><strong>🏛️ Central University Treasury</strong></td>
          <td>${(treasuryPct * 100).toFixed(1)}%</td>
          <td><strong>${formatMYR(treasuryVal)}</strong></td>
        </tr>
        <tr>
          <td><strong>🔬 Originating Dept / Lab</strong></td>
          <td>${(deptPct * 100).toFixed(1)}%</td>
          <td><strong>${formatMYR(deptVal)}</strong></td>
        </tr>
        <tr>
          <td><strong>👩‍🔬 Lead Inventors & Team</strong></td>
          <td>${(inventorPct * 100).toFixed(1)}%</td>
          <td><strong>${formatMYR(inventorVal)}</strong></td>
        </tr>
        <tr>
          <td><strong>🚀 RCF Re-investment Fund</strong></td>
          <td>${(rcfPct * 100).toFixed(1)}%</td>
          <td><strong>${formatMYR(rcfVal)}</strong></td>
        </tr>
      `;
    }
  }

  amountInput.addEventListener('input', calculateRevenue);
  typeSelect.addEventListener('change', calculateRevenue);
  calculateRevenue();
}

/* Helper Utilities */
function simpleHash(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0;
  }
  return Math.abs(hash).toString(16).padStart(8, '0') + Math.abs(hash * 31).toString(16).padStart(8, '0');
}

function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}
