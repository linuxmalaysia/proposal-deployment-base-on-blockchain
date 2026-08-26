---
okf_version: "0.2"
type: "reference"
title: "DCA & DAC Core API, CLI, and Data Objects Reference"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# DCA & DAC Core API, CLI, and Data Objects Reference

This reference document provides technical specifications for the core domain Python modules, database adapters, command-line utility tools, and primary data objects within the Digital Custody Asset (DCA) and Digital Asset Custodian (DAC) platform.

---

## 1. Core Domain Python Modules (`src/dca_service/core/`)

Core domain entities follow Concentric Clean Architecture principles with **zero external third-party dependencies**.

### 1.1 `AccountLedger` (`src/dca_service/core/account_ledger.py`)
Manages client sub-account ledgers enforcing non-commingling of digital assets.

#### Classes & Methods:
- **`AccountLedger(account_id: str)`**: Constructor initialising a segregated ledger instance.
- **`deposit(asset_symbol: str, amount: Decimal) -> AssetBalance`**: Records an incoming deposit.
- **`withdraw(asset_symbol: str, amount: Decimal) -> AssetBalance`**: Deducts funds, raising `InsufficientFundsError` if balance is inadequate.
- **`get_balance(asset_symbol: str) -> Decimal`**: Returns current available balance for a specific token or fiat currency.

---

### 1.2 `PolicyEngine` (`src/dca_service/core/policy_engine.py`)
Evaluates transaction proposals against institutional policy rules.

#### Classes & Methods:
- **`PolicyEngine()`**: Constructs policy engine instance.
- **`add_rule(rule: PolicyRule) -> None`**: Registers a validation policy rule.
- **`evaluate(proposal: TransactionProposal, verified_authenticated_signers: List[str]) -> bool`**: Evaluates proposal against active rules. Enforces velocity limits, required signer thresholds, and allowlist destinations.

---

### 1.3 `KeyManagementService` (`src/dca_service/core/key_management.py`)
Interfaces with open-source MPC threshold quorums (Coinbase `cb-mpc`) and HSM vault tiering.

#### Classes & Methods:
- **`KeyManagementService()`**: Initialises key management service.
- **`generate_key_share(party_id: str, threshold: int) -> KeyShare`**: Generates polynomial key share under $t$-of-$n$ DKG.
- **`sign_digest(key_id: str, digest: bytes, signers: List[str]) -> bytes`**: Co-ordinates threshold signature generation across quorum nodes.

---

### 1.4 `AncillaryAuditLogger` (`src/dca_service/core/ancillary_audit.py`)
Generates SOC 1 / SOC 2 compliant structured audit logs.

#### Classes & Methods:
- **`AncillaryAuditLogger()`**: Initialises audit logger.
- **`log_event(event_type: str, account_id: str, details: dict) -> AuditRecord`**: Persists immutable event record with timestamp, sequence ID, and SHA-256 payload hash.

---

## 2. Database Adapters (`src/dca_service/adapters/`)

### 2.1 `TimescaleDBAdapter` (`src/dca_service/adapters/timescaledb_adapter.py`)
Primary database driver connecting to **Percona Server for PostgreSQL** with TimescaleDB time-series hypertable support.

#### Primary Table Schema (`custody_transactions`):
| Column Name | Type | Description |
| :--- | :--- | :--- |
| `transaction_id` | `UUID` | Primary key identifier |
| `timestamp` | `TIMESTAMPTZ` | Hypertable partition time |
| `account_id` | `VARCHAR(64)` | Segregated sub-account ledger reference |
| `asset_symbol` | `VARCHAR(16)` | Token or currency code |
| `amount` | `NUMERIC(36, 18)` | Transaction amount |
| `status` | `VARCHAR(32)` | `DB_RECORDED`, `PENDING_BLOCKCHAIN`, `CHAIN_CONFIRMED` |
| `payload_hash` | `CHAR(64)` | SHA-256 state payload hash |

---

## 3. Command-Line Utility Tools (`tools/`)

### 3.1 `tools/generate_summary.py`
Scans `docs/` and root ledgers to dynamically update `SUMMARY.md`.

- **Usage:** `uv run python tools/generate_summary.py`
- **Output:** Writes structured OKF v0.2 Markdown index to `SUMMARY.md`.

### 3.2 `tools/install_git_guardrails.py`
DSOM Pre-Commit Guardrail Validator.

- **Usage:** `uv run python tools/install_git_guardrails.py`
- **Exit Codes:**
  - `0`: All checks passed (OKF frontmatter valid, pytest passed).
  - `1`: Validation or test failure.

---

## 4. Digital Asset Custodian (DAC) Data Objects Reference

| Object Name | Identifier Format | Key Fields | Primary Backend Engine |
| :--- | :--- | :--- | :--- |
| **DigitalResearchID** | `DRI-YYYY-CHAIR-XXXX` | `asset_id`, `chair_origin`, `created_date` | Percona PostgreSQL |
| **DigitalAssetCertificate** | `DAC-CERT-UUIDv4` | `research_id`, `inventors`, `sha256_evidence_hash` | Percona PostgreSQL + TimescaleDB |
| **TRL Rating** | Integer (`1` to `9`) | `trl_level`, `assessment_date`, `evaluator_id` | Percona PostgreSQL Core Entity |
| **MarketReadinessScore** | Decimal (`0.0` to `100.0`) | `score`, `market_size_index`, `regulatory_pathway` | Percona PostgreSQL Analytical View |
