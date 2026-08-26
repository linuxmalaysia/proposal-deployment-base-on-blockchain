---
okf_version: "0.2"
type: "tutorial"
title: "Getting Started with the DCA & DAC Platform on Percona PostgreSQL"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# Getting Started with the DCA & DAC Platform on Percona PostgreSQL

Welcome to the beginner tutorial for setting up and initialising the **Digital Custody Asset (DCA)** and **Digital Asset Custodian (DAC)** platform environment.

In this tutorial, you will learn how to:
1. Initialise the Python environment using `uv`.
2. Configure the primary **Percona Server for PostgreSQL** database backend and TimescaleDB extension hooks.
3. Instantiate core ledger models, policy engines, and key management components.
4. Register a research asset into the DAC system and record a settlement transaction.

---

## Prerequisites

Before starting this tutorial, ensure you have:
- Python 3.12+ installed.
- `uv` installed (`pip install uv` or system installer).
- Access to a running Percona Server for PostgreSQL instance (or local test database container).

---

## Step 1: Initialise the Workspace Environment

Clone the repository and initialise the virtual environment using `uv`:

```bash
# Sync dependencies and build virtual environment
uv sync

# Run tests to confirm environment sanity
uv run pytest
```

---

## Step 2: Configure Percona PostgreSQL Primary Backend

The DCA/DAC platform enforces a dual-write pattern where all transaction ledgers and research asset metadata are written to **Percona Server for PostgreSQL** prior to optional blockchain broadcasting.

Verify the adapter configuration in `src/dca_service/adapters/timescaledb_adapter.py`:

```python
from dca_service.adapters.timescaledb_adapter import TimescaleDBAdapter

# Initialise connection pool to Percona PostgreSQL / TimescaleDB
db_adapter = TimescaleDBAdapter(
    dsn="postgresql://dca_user:secret@localhost:5432/dca_custody_db"
)
db_adapter.initialise_schema()
```

---

## Step 3: Instantiate Core Domain Ledger & Policy Engine

All business entities are pure Python classes in `src/dca_service/core/` with zero third-party framework dependencies.

Create a simple script `tutorial_demo.py`:

```python
from decimal import Decimal
from dca_service.core.account_ledger import AccountLedger, AssetBalance
from dca_service.core.policy_engine import PolicyEngine, PolicyRule, TransactionProposal

# 1. Initialise Segregated Client Sub-Account Ledger
ledger = AccountLedger(account_id="ACC-RESEARCH-CHAIR-001")
ledger.deposit("MYR", Decimal("500000.00"))

# 2. Configure Policy Engine Quorum Rule
policy = PolicyEngine()
policy.add_rule(
    PolicyRule(
        rule_id="RULE-MAX-SINGLE-TRANSFER",
        max_amount=Decimal("100000.00"),
        required_approvals=2,
        authorized_signers=["signer_admin", "signer_custodian"],
    )
)

# 3. Submit Transaction Proposal
proposal = TransactionProposal(
    proposal_id="PROP-001",
    account_id="ACC-RESEARCH-CHAIR-001",
    amount=Decimal("25000.00"),
    asset_symbol="MYR",
    destination_address="0xRecipientAddress",
    signers=["signer_admin", "signer_custodian"],
)

is_approved = policy.evaluate(proposal, verified_authenticated_signers=["signer_admin", "signer_custodian"])
print(f"Policy Approval Result: {is_approved}")
```

Run the demo script:

```bash
uv run python tutorial_demo.py
```

---

## Step 4: Register a Research Asset in the DAC

To register a research output (e.g., patent or prototype) under the DAC system:

1. Generate a unique `Digital Research ID`.
2. Create an initial `Digital Asset Certificate` metadata record.
3. Compute the initial **Technology Readiness Level (TRL)** rating and **Market Readiness Score**.

```python
from dca_service.core.ancillary_audit import AncillaryAuditLogger

# Initialise audit logger bound to Percona PostgreSQL audit hypertable
audit_logger = AncillaryAuditLogger()

audit_logger.log_event(
    event_type="DAC_ASSET_REGISTERED",
    account_id="ACC-RESEARCH-CHAIR-001",
    details={
        "digital_research_id": "DRI-2026-CHAIR-0941",
        "title": "Quantum Cryptography Key Distributer",
        "trl_level": 4,
        "market_readiness_score": 78.5,
        "primary_backend": "Percona Server for PostgreSQL",
    },
)

print("Research Asset Registered Successfully.")
```

---

## Next Steps

Congratulations! You have completed the basic DCA/DAC getting started tutorial.

- Read the [Architecture Overview](../explanation/architecture-overview.md) to understand vault tiering and key management.
- Refer to the [Research Commercialisation Fund (RCF) & DAC Architecture Proposal](../explanation/research-commercialisation-fund-dac-proposal.md) for fund details.
- Review the [Guardrails How-To Guide](../how-to/install-and-configure-guardrails.md) to set up pre-commit validation tools.
