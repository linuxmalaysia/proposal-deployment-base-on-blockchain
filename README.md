---
okf_version: "0.2"
type: "overview"
title: "Digital Custody Asset (DCA) as a Service Platform"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# Digital Custody Asset (DCA) as a Service Platform

Institutional-grade white-label & API-based Digital Asset Custody Platform built following Clean Architecture principles and governed by the Deep State of Mind (DSOM) Protocol.

## 🌟 Key Features
- **Key Management:** MPC (Multi-Party Computation) threshold quorums and HSM-backed Hot/Warm/Cold vault tiering.
- **Client Segregation:** Isolated sub-account ledgers enforcing zero commingling of digital assets.
- **Policy Engine:** Granular approval workflows, velocity limits, multi-signer quorums, and address allowlists.
- **Percona PostgreSQL & TimescaleDB Synchronisation:** Dual-write pattern writing transactions to database hypertables first, followed by immutable blockchain settlement (see [Percona & TimescaleDB Architecture Document](docs/explanation/percona-timescaledb-blockchain-sync.md)).
- **Ancillary Services:** Integrated proof-of-stake hooks and tokenised collateral management interfaces.
- **Immutable Audit Trail:** SOC 1 / SOC 2 compliant structured event auditing.

## 🛠️ Environment & Running Tests
This project uses `uv` for Python dependency management and execution.

```bash
# Run tests
uv run pytest

# Execute pre-commit guardrail checks
uv run python tools/install_git_guardrails.py
```
