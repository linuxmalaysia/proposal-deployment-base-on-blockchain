---
okf_version: "0.2"
type: "overview"
title: "Digital Custody Asset (DCA) as a Service Platform"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "dca"
  - "custody"
  - "mpc"
  - "postgresql"
  - "timescaledb"
  - "clean-architecture"
description: "Institutional-grade white-label & API-based Digital Asset Custody Platform"
resource: "file:///README.md"
sources:
  - "SUMMARY.md"
  - "AGENTS.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# Digital Custody Asset (DCA) as a Service Platform

Institutional-grade white-label & API-based Digital Asset Custody Platform built following Clean Architecture principles and governed by the Deep State of Mind (DSOM) Protocol.

## 🌟 Key Features
- **Key Management:** Open-source MPC (Multi-Party Computation) threshold quorums via Coinbase `cb-mpc` integration and HSM-backed Hot/Warm/Cold vault tiering (see [Open-Source MPC Wallet Architecture](docs/explanation/open-source-mpc-wallet-architecture.md)).
- **Client Segregation:** Isolated sub-account ledgers enforcing zero commingling of digital assets.
- **Policy Engine:** Granular approval workflows, velocity limits, multi-signer quorums, and address allowlists.
- **Percona PostgreSQL & TimescaleDB Synchronisation:** Dual-write pattern writing transactions to database hypertables first, followed by immutable blockchain settlement (see [Percona & TimescaleDB Architecture Document](docs/explanation/percona-timescaledb-blockchain-sync.md)).
- **Research Commercialisation Fund (RCF) & Digital Asset Custodian (DAC):** Integrated research asset management, interactive web portal (FastAPI backend with Render.com deployment readiness), automatic fail-safe database schema check & table building on application startup, real-time connection status page (`/db-status`), and quantitative valuation framework anchored on Supabase PostgreSQL (see [RCF & DAC Proposal](docs/explanation/research-commercialisation-fund-dac-proposal.md), [Supabase Render Connection Guide](docs/how-to/connect-supabase-postgresql-on-render.md), and [Schema DDL](docs/schema.sql)).
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
