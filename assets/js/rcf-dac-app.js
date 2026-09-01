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
  loadSavedAssets();
});

/**
 * Initializes session status display, role-based controls, and role panel switching.
 */
function initRoleSwitcher() {
  const roleButtons = document.querySelectorAll('.role-select-btn');
  const roleViews = document.querySelectorAll('.role-view-panel');
  const banner = document.getElementById('portalSessionBanner');
  const btnUserMgmt = document.getElementById('btnUserMgmt');

  const userObjStr = localStorage.getItem('rcf_dac_user');
  let currentUser = null;
  try {
    if (userObjStr) currentUser = JSON.parse(userObjStr);
  } catch (e) {}

  if (banner) {
    if (currentUser && currentUser.role) {
      banner.style.background = '#e0f2fe';
      banner.style.color = '#0369a1';
      banner.style.border = '1px solid #bae6fd';
      banner.innerHTML = `<strong>Active User:</strong> ${escapeHtml(currentUser.name || currentUser.username)} | <strong>Role:</strong> <span class="badge badge-primary">${escapeHtml(currentUser.role)}</span>`;
      if (['admin', 'superuser'].includes(currentUser.role) && btnUserMgmt) {
        btnUserMgmt.style.display = 'inline-block';
      }
    } else {
      banner.style.background = '#fef3c7';
      banner.style.color = '#92400e';
      banner.style.border = '1px solid #fde68a';
      banner.innerHTML = `<strong>⚠️ Authentication Required:</strong> You are currently viewing as guest. Operational module submissions require logging in with specific assigned role credentials. <a href="/login" style="color: #b45309; font-weight: bold; text-decoration: underline;">Click here to Login</a>.`;
    }
  }

  if (!roleButtons.length) return;

  roleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const selectedRole = btn.getAttribute('data-role');
      if (!selectedRole) return;

      roleButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      roleViews.forEach(view => {
        const viewRole = view.getAttribute('data-role-view');
        if (selectedRole === 'all') {
          view.style.display = 'block';
        } else if (selectedRole === 'my-role') {
          if (!currentUser || !currentUser.role) {
            view.style.display = 'block';
          } else {
            const role = currentUser.role.toLowerCase();
            if (role === 'admin' || role === 'superuser') {
              view.style.display = 'none';
            } else if (role === 'auditor') {
              view.style.display = 'block';
            } else if (role === 'operator' && (viewRole === 'researcher' || viewRole === 'admin')) {
              view.style.display = 'block';
            } else if (role === 'investor' && viewRole === 'investor') {
              view.style.display = 'block';
            } else {
              view.style.display = 'none';
            }
          }
        } else if (viewRole === selectedRole) {
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
    let savedSuccessfully = false;

    try {
      localStorage.setItem('rcf_dac_user_registration', JSON.stringify(userRecord));
      savedSuccessfully = true;
    } catch (err) {
      console.warn('LocalStorage unavailable:', err);
      savedSuccessfully = false;
    }

    renderRegistrationResult(userRecord, savedSuccessfully);
  });
}

function renderRegistrationResult(userRecord, savedSuccessfully = true) {
  const outputBox = document.getElementById('user-reg-output');
  if (outputBox) {
    if (savedSuccessfully) {
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
    } else {
      outputBox.innerHTML = `
        <div class="result-card hold">
          <h4>⚠️ Identity Generated (Persistence Unavailable)</h4>
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
            <span>BROWSER STORAGE PERSISTENCE: Local storage write failed or unavailable; record not persisted.</span>
          </div>
        </div>
      `;
    }
    outputBox.style.display = 'block';
  }
}

function loadSavedRegistration() {
  try {
    const saved = localStorage.getItem('rcf_dac_user_registration');
    if (saved) {
      const userRecord = JSON.parse(saved);
      renderRegistrationResult(userRecord, true);
    }
  } catch (err) {
    console.warn('Could not load saved user registration:', err);
  }
}

/* -------------------------------------------------------------------------
   3. Asset Registration & Cryptographic Evidence Vault
   ------------------------------------------------------------------------- */
function getSavedAssetCollection() {
  try {
    const saved = localStorage.getItem('rcf_dac_asset_collection');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (typeof parsed === 'object' && parsed !== null) {
        return parsed;
      }
    }
  } catch (err) {
    console.warn('Could not read asset collection:', err);
  }
  return {};
}

/**
 * Initializes the asset registration form and handles evidence submission.
 *
 * Registers asset metadata with the server, computes the evidence file's SHA-256 digest,
 * stores the returned asset record locally, and updates the asset collection display.
 */
function initAssetForm() {
  const form = document.getElementById('asset-reg-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const title = document.getElementById('asset-title').value.trim() || 'High-Efficiency Graphene Supercapacitor Cell';
    const trl = parseInt(document.getElementById('asset-trl').value, 10) || 3;
    const abstract = document.getElementById('asset-abstract').value.trim() || 'Scalable energy storage prototype with 92% retention rate.';
    const fileInput = document.getElementById('asset-file');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      alert('Please select a valid evidence file to register.');
      return;
    }

    const file = fileInput.files[0];
    const fileRef = file.name;

    const bytesBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', bytesBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hexDigest = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    const localSha256Digest = `sha256:${hexDigest}`;

    const token = localStorage.getItem('rcf_dac_jwt');

    let base64Content = "";
    const bytes = new Uint8Array(bytesBuffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      base64Content += String.fromCharCode(bytes[i]);
    }
    base64Content = btoa(base64Content);

    try {
      const resp = await fetch('/api/register-asset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          title: title,
          trl: trl,
          abstract: abstract,
          file_name: fileRef,
          file_content: base64Content,
          content_encoding: "base64"
        })
      });

      const resData = await resp.json();

      if (!resp.ok) {
        alert(`Asset Registration Error (${resp.status}): ${resData.detail || 'Access denied.'}`);
        return;
      }

      const asset = resData.asset;
      const assetRecord = {
        title: asset.title,
        trl: asset.trl,
        abstract: asset.abstract,
        fileRef: asset.file_name,
        assetId: asset.asset_id,
        sha256Digest: asset.sha256_digest || localSha256Digest,
        txOutboxId: asset.tx_outbox_id,
        timestamp: asset.timestamp
      };

      const collection = getSavedAssetCollection();
      collection[assetRecord.assetId] = assetRecord;

      let savedSuccessfully = false;
      try {
        localStorage.setItem('rcf_dac_asset_collection', JSON.stringify(collection));
        savedSuccessfully = true;
      } catch (err) {
        console.warn('LocalStorage unavailable:', err);
        savedSuccessfully = false;
      }

      renderAssetCollection(collection, assetRecord.assetId, savedSuccessfully);
    } catch (err) {
      alert(`Network or Server error: ${err}`);
    }
  });
}

function renderAssetCollection(collection, latestAssetId = null, savedSuccessfully = true) {
  const outputBox = document.getElementById('asset-reg-output');
  if (!outputBox) return;

  const assets = Object.values(collection);
  if (!assets.length) return;

  let html = `<div class="result-card ${savedSuccessfully ? 'success' : 'hold'}">`;
  html += `<h4>📜 Digital Research Asset Registry (${assets.length} Asset${assets.length > 1 ? 's' : ''})</h4>`;

  if (!savedSuccessfully) {
    html += `<p style="font-size:0.8rem; color:#f59e0b;">⚠️ LocalStorage unavailable: newly generated asset was not saved.</p>`;
  }

  assets.reverse().forEach((asset, idx) => {
    const isNew = latestAssetId && asset.assetId === latestAssetId;
    html += `
      <div style="margin-bottom: ${idx < assets.length - 1 ? '1rem' : '0'}; border-bottom: ${idx < assets.length - 1 ? '1px solid var(--border-color)' : 'none'}; padding-bottom: ${idx < assets.length - 1 ? '0.75rem' : '0'};">
        <div class="badge-grid">
          <p><strong>Digital Asset ID:</strong> <code>${escapeHtml(asset.assetId)}</code> ${isNew ? '<span class="badge badge-primary">NEW</span>' : ''}</p>
          <p><strong>Technical Maturity:</strong> <span class="badge badge-primary">TRL ${escapeHtml(asset.trl)}</span></p>
          <p><strong>Title:</strong> ${escapeHtml(asset.title)}</p>
          <p><strong>Evidence File:</strong> ${escapeHtml(asset.fileRef)}</p>
        </div>
        <div class="did-code-box">
          <span class="did-label">SHA-256 Digest:</span>
          <code>${escapeHtml(asset.sha256Digest)}</code>
        </div>
        <div class="outbox-status">
          <span class="status-dot green"></span>
          <strong>Simulated Outbox Batch ID:</strong> <code>${escapeHtml(asset.txOutboxId)}</code>
        </div>
      </div>
    `;
  });

  html += `</div>`;
  outputBox.innerHTML = html;
  outputBox.style.display = 'block';
}

function loadSavedAssets() {
  const collection = getSavedAssetCollection();
  if (Object.keys(collection).length > 0) {
    renderAssetCollection(collection, null, true);
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
