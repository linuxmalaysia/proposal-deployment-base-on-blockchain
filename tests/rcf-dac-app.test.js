const assert = require('node:assert/strict');
const { createHash, webcrypto } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const { TextEncoder } = require('node:util');

const APP_SOURCE = fs.readFileSync(
  path.resolve(__dirname, '..', 'assets', 'js', 'rcf-dac-app.js'),
  'utf8',
);

class FakeClassList {
  constructor(initial = '') {
    this.values = new Set(initial.split(/\s+/).filter(Boolean));
  }

  add(value) {
    this.values.add(value);
  }

  remove(value) {
    this.values.delete(value);
  }

  contains(value) {
    return this.values.has(value);
  }
}

class FakeElement {
  constructor({ id = '', className = '', value = '', attributes = {}, files } = {}) {
    this.id = id;
    this.value = value;
    this.attributes = { ...attributes };
    this.files = files;
    this.innerHTML = '';
    this.innerText = '';
    this.style = {};
    this.className = className;
    this.classList = new FakeClassList(className);
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  getAttribute(name) {
    return this.attributes[name] ?? null;
  }

  async dispatch(type) {
    const event = {
      defaultPrevented: false,
      preventDefault() {
        this.defaultPrevented = true;
      },
    };
    for (const listener of this.listeners.get(type) || []) {
      await listener(event);
    }
    return event;
  }
}

class FakeDocument {
  constructor(elements = []) {
    this.elements = elements;
    this.byId = new Map(elements.filter((element) => element.id).map((element) => [element.id, element]));
    this.listeners = new Map();
  }

  addEventListener(type, listener) {
    const listeners = this.listeners.get(type) || [];
    listeners.push(listener);
    this.listeners.set(type, listeners);
  }

  getElementById(id) {
    return this.byId.get(id) || null;
  }

  querySelectorAll(selector) {
    if (!selector.startsWith('.')) return [];
    const className = selector.slice(1);
    return this.elements.filter((element) => element.classList.contains(className));
  }

  async dispatch(type) {
    for (const listener of this.listeners.get(type) || []) {
      await listener({ type });
    }
  }
}

class FakeStorage {
  constructor(initial = {}, { failReads = false, failWrites = false } = {}) {
    this.values = new Map(Object.entries(initial));
    this.failReads = failReads;
    this.failWrites = failWrites;
  }

  getItem(key) {
    if (this.failReads) throw new Error('storage read denied');
    return this.values.get(key) ?? null;
  }

  setItem(key, value) {
    if (this.failWrites) throw new Error('storage write denied');
    this.values.set(key, String(value));
  }
}

function element(options) {
  return new FakeElement(options);
}

function loadApp({ elements = [], storageInitial = {}, storageOptions = {} } = {}) {
  const document = new FakeDocument(elements);
  const localStorage = new FakeStorage(storageInitial, storageOptions);
  const warnings = [];
  const context = vm.createContext({
    console: { warn: (...args) => warnings.push(args) },
    crypto: webcrypto,
    document,
    localStorage,
    TextEncoder,
  });
  vm.runInContext(APP_SOURCE, context, { filename: 'assets/js/rcf-dac-app.js' });
  return { context, document, localStorage, warnings };
}

function registrationElements(overrides = {}) {
  const values = {
    'reg-fullname': '  Dr. Aisyah <Lead>  ',
    'reg-role': 'researcher',
    'reg-dept': '  Advanced R&D  ',
    'reg-email': 'aisyah@example.my',
    ...overrides,
  };
  return [
    element({ id: 'user-reg-form' }),
    ...Object.entries(values).map(([id, value]) => element({ id, value })),
    element({ id: 'user-reg-output' }),
  ];
}

function assetElements({ fileInput, title = 'Secure <Prototype>', trl = '4', abstract = 'Evidence' } = {}) {
  return [
    element({ id: 'asset-reg-form' }),
    element({ id: 'asset-title', value: title }),
    element({ id: 'asset-trl', value: trl }),
    element({ id: 'asset-abstract', value: abstract }),
    fileInput || element({ id: 'asset-file', value: 'evidence.txt' }),
    element({ id: 'asset-reg-output' }),
  ];
}

function scoreElements(scores = { tech: 45, market: 45, comm: 45, mgmt: 45 }) {
  const elements = [];
  for (const [name, value] of Object.entries(scores)) {
    elements.push(element({ id: `score-${name}`, value: String(value) }));
    elements.push(element({ id: `val-${name}` }));
  }
  elements.push(element({ id: 'total-cloverleaf-score' }));
  elements.push(element({ id: 'cloverleaf-status' }));
  return elements;
}

function revenueElements(amount = '500000', type = 'licensing') {
  return [
    element({ id: 'rev-amount', value: amount }),
    element({ id: 'rev-type', value: type }),
    element({ id: 'revenue-split-body' }),
  ];
}

test('helper utilities hash deterministically and escape every HTML metacharacter', () => {
  const { context } = loadApp();

  assert.equal(context.simpleHash('RCF-DAC'), context.simpleHash('RCF-DAC'));
  assert.match(context.simpleHash('RCF-DAC'), /^[0-9a-f]{16,}$/);
  assert.notEqual(context.simpleHash('RCF-DAC'), context.simpleHash('RCF-DAC!'));
  assert.equal(
    context.escapeHtml(`<&>"'`),
    '&lt;&amp;&gt;&quot;&#039;',
  );
});

test('role switcher activates one persona and restores every panel for all modules', async () => {
  const allButton = element({ className: 'role-select-btn active', attributes: { 'data-role': 'all' } });
  const researcherButton = element({ className: 'role-select-btn', attributes: { 'data-role': 'researcher' } });
  const adminButton = element({ className: 'role-select-btn', attributes: { 'data-role': 'admin' } });
  const researcherPanel = element({ className: 'role-view-panel', attributes: { 'data-role-view': 'researcher' } });
  const adminPanel = element({ className: 'role-view-panel', attributes: { 'data-role-view': 'admin' } });
  const { context } = loadApp({
    elements: [allButton, researcherButton, adminButton, researcherPanel, adminPanel],
  });

  context.initRoleSwitcher();
  await researcherButton.dispatch('click');

  assert.equal(researcherButton.classList.contains('active'), true);
  assert.equal(allButton.classList.contains('active'), false);
  assert.equal(researcherPanel.style.display, 'block');
  assert.equal(adminPanel.style.display, 'none');

  await allButton.dispatch('click');
  assert.equal(allButton.classList.contains('active'), true);
  assert.equal(researcherPanel.style.display, 'block');
  assert.equal(adminPanel.style.display, 'block');
});

test('registration trims fields, persists the complete record, and escapes rendered values', async () => {
  const elements = registrationElements();
  const { context, localStorage } = loadApp({ elements });
  context.initRegistrationForm();

  const event = await elements[0].dispatch('submit');
  const record = JSON.parse(localStorage.getItem('rcf_dac_user_registration'));
  const output = elements.at(-1);

  assert.equal(event.defaultPrevented, true);
  assert.equal(record.name, 'Dr. Aisyah <Lead>');
  assert.equal(record.dept, 'Advanced R&D');
  assert.equal(record.role, 'researcher');
  assert.equal(record.email, 'aisyah@example.my');
  assert.match(record.did, /^did:univ:[0-9a-f]{16}$/);
  assert.doesNotThrow(() => new Date(record.timestamp).toISOString());
  assert.match(output.innerHTML, /Dr\. Aisyah &lt;Lead&gt;/);
  assert.doesNotMatch(output.innerHTML, /Dr\. Aisyah <Lead>/);
  assert.equal(output.style.display, 'block');
});

test('registration applies documented defaults to blank optional values', async () => {
  const elements = registrationElements({
    'reg-fullname': '   ',
    'reg-dept': '',
    'reg-email': ' ',
  });
  const { context, localStorage } = loadApp({ elements });
  context.initRegistrationForm();
  await elements[0].dispatch('submit');

  const record = JSON.parse(localStorage.getItem('rcf_dac_user_registration'));
  assert.equal(record.name, 'Dr. Aris Roslan');
  assert.equal(record.dept, 'Faculty of Engineering & Innovation');
  assert.equal(record.email, 'aris@university.edu.my');
});

test('registration still renders when browser storage rejects writes', async () => {
  const elements = registrationElements();
  const { context, warnings } = loadApp({ elements, storageOptions: { failWrites: true } });
  context.initRegistrationForm();

  await elements[0].dispatch('submit');

  assert.match(elements.at(-1).innerHTML, /Identity Registered/);
  assert.equal(warnings.length, 1);
  assert.equal(warnings[0][0], 'LocalStorage unavailable:');
});

test('saved registration is restored and malformed storage is handled safely', () => {
  const savedRecord = {
    name: 'Prof. Siti',
    role: 'admin',
    dept: 'TTO',
    email: 'siti@example.my',
    did: 'did:univ:abc123',
  };
  const restoredOutput = element({ id: 'user-reg-output' });
  const restored = loadApp({
    elements: [restoredOutput],
    storageInitial: { rcf_dac_user_registration: JSON.stringify(savedRecord) },
  });
  restored.context.loadSavedRegistration();
  assert.match(restoredOutput.innerHTML, /Prof\. Siti/);
  assert.match(restoredOutput.innerHTML, /did:univ:abc123/);

  const malformed = loadApp({
    elements: [element({ id: 'user-reg-output' })],
    storageInitial: { rcf_dac_user_registration: '{not-json' },
  });
  assert.doesNotThrow(() => malformed.context.loadSavedRegistration());
  assert.equal(malformed.warnings[0][0], 'Could not load saved user registration:');
});

test('asset registration hashes uploaded file bytes and persists escaped output', async () => {
  const bytes = Uint8Array.from([0, 1, 2, 127, 128, 255]);
  const fileInput = element({
    id: 'asset-file',
    files: [{ name: 'proof<script>.bin', arrayBuffer: async () => bytes.buffer }],
  });
  const elements = assetElements({ fileInput });
  const { context, localStorage } = loadApp({ elements });
  context.initAssetForm();

  const event = await elements[0].dispatch('submit');
  const record = JSON.parse(localStorage.getItem('rcf_dac_asset_registration'));
  const expectedDigest = createHash('sha256').update(bytes).digest('hex');
  const output = elements.at(-1);

  assert.equal(event.defaultPrevented, true);
  assert.equal(record.sha256Digest, `sha256:${expectedDigest}`);
  assert.equal(record.fileRef, 'proof<script>.bin');
  assert.match(record.assetId, /^did:univ:asset-[0-9a-f]{12}$/);
  assert.match(record.txOutboxId, /^outbox_tx_[1-9][0-9]{5}$/);
  assert.match(output.innerHTML, /Secure &lt;Prototype&gt;/);
  assert.match(output.innerHTML, /proof&lt;script&gt;\.bin/);
  assert.doesNotMatch(output.innerHTML, /proof<script>/);
});

test('asset registration hashes a text file reference when no File object is available', async () => {
  const fileReference = 'lab-notebook.pdf';
  const elements = assetElements({ fileInput: element({ id: 'asset-file', value: fileReference }) });
  const { context, localStorage } = loadApp({ elements });
  context.initAssetForm();
  await elements[0].dispatch('submit');

  const record = JSON.parse(localStorage.getItem('rcf_dac_asset_registration'));
  const expectedDigest = createHash('sha256').update(fileReference).digest('hex');
  assert.equal(record.fileRef, fileReference);
  assert.equal(record.sha256Digest, `sha256:${expectedDigest}`);
});

test('asset registration uses fallback content and still renders if persistence fails', async () => {
  const elements = assetElements({
    fileInput: element({ id: 'asset-file', value: '' }),
    title: ' ',
    abstract: '',
  });
  const { context, warnings } = loadApp({ elements, storageOptions: { failWrites: true } });
  context.initAssetForm();
  await elements[0].dispatch('submit');

  const output = elements.at(-1).innerHTML;
  const fallbackFile = 'lab_notebook_vol4_patent_draft.pdf';
  const expectedDigest = createHash('sha256').update(fallbackFile).digest('hex');
  assert.match(output, /High-Efficiency Graphene Supercapacitor Cell/);
  assert.match(output, new RegExp(`sha256:${expectedDigest}`));
  assert.equal(warnings[0][0], 'LocalStorage unavailable:');
});

test('saved asset is restored and inaccessible storage does not break initialisation', () => {
  const assetRecord = {
    title: 'Stored asset',
    trl: '7',
    fileRef: 'stored.pdf',
    assetId: 'did:univ:asset-stored',
    sha256Digest: 'sha256:stored',
    txOutboxId: 'outbox_tx_123456',
  };
  const output = element({ id: 'asset-reg-output' });
  const restored = loadApp({
    elements: [output],
    storageInitial: { rcf_dac_asset_registration: JSON.stringify(assetRecord) },
  });
  restored.context.loadSavedAsset();
  assert.match(output.innerHTML, /Stored asset/);
  assert.match(output.innerHTML, /TRL 7/);

  const inaccessible = loadApp({ storageOptions: { failReads: true } });
  assert.doesNotThrow(() => inaccessible.context.loadSavedAsset());
  assert.equal(inaccessible.warnings[0][0], 'Could not load saved asset registration:');
});

test('Cloverleaf score requires a strict total above 180', async () => {
  const elements = scoreElements();
  const { context } = loadApp({ elements });
  context.initCloverleafCalculator();

  const total = elements.find((item) => item.id === 'total-cloverleaf-score');
  const status = elements.find((item) => item.id === 'cloverleaf-status');
  assert.equal(total.innerText, '180 / 260');
  assert.equal(status.className, 'status-badge hold');
  assert.match(status.innerHTML, /180 <= 180 Target/);

  const tech = elements.find((item) => item.id === 'score-tech');
  tech.value = '46';
  await tech.dispatch('input');
  assert.equal(total.innerText, '181 / 260');
  assert.equal(status.className, 'status-badge pass');
  assert.match(status.innerHTML, /INVESTMENT-READY/);
  assert.equal(elements.find((item) => item.id === 'val-tech').innerText, '46 / 60');
});

test('revenue calculator preserves zero and applies each stream allocation', async (t) => {
  const cases = [
    ['licensing', ['30.0%', '20.0%', '30.0%', '20.0%']],
    ['equity', ['35.0%', '10.0%', '25.0%', '30.0%']],
    ['dividend', ['25.0%', '15.0%', '30.0%', '30.0%']],
    ['royalty', ['33.3%', '33.3%', '33.4%', '0.0%']],
  ];

  for (const [stream, percentages] of cases) {
    await t.test(stream, () => {
      const elements = revenueElements('0', stream);
      const { context } = loadApp({ elements });
      context.initRevenueCalculator();
      const table = elements.at(-1).innerHTML;

      for (const percentage of percentages) assert.match(table, new RegExp(percentage.replace('.', '\\.')));
      assert.doesNotMatch(table, /500,000/);
      assert.equal((table.match(/0\.00/g) || []).length, 4);
    });
  }
});

test('revenue calculator falls back for negative and non-finite values, then reacts to changes', async () => {
  const elements = revenueElements('-1', 'licensing');
  const { context } = loadApp({ elements });
  context.initRevenueCalculator();
  const amount = elements[0];
  const type = elements[1];
  const table = elements[2];

  assert.match(table.innerHTML, /150,000/);
  amount.value = 'not-a-number';
  await amount.dispatch('input');
  assert.match(table.innerHTML, /150,000/);

  amount.value = '1000';
  type.value = 'equity';
  await type.dispatch('change');
  assert.match(table.innerHTML, /35\.0%/);
  assert.match(table.innerHTML, /350\.00/);
});

test('DOMContentLoaded initialisation is safe on pages without portal controls', async () => {
  const { document, warnings } = loadApp();
  await assert.doesNotReject(document.dispatch('DOMContentLoaded'));
  assert.deepEqual(warnings, []);
});
