---
okf_version: '0.2'
type: changelog
title: DCA Service Platform Changelog & Release History
timestamp: '2026-08-25T00:00:00Z'
topics:
- changelog
- releases
- dca-service
- versioning
description: Chronological ledger of user-facing changes, features, security updates,
  and documentation additions.
resource: file:///CHANGELOG.md
sources:
- HISTORY.md
- README.md
generated: jules
verified: true
status: approved
stale_after: '2027-08-25T00:00:00Z'
language: en-GB
---
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-25

### Added
- Greenfield project setup with Python `uv` toolchain.
- DSOM Protocol 6-Pillar downstream footprint (`AGENTS.md`, `.agents/brain/`, spatial memory anchors).
- Core domain models for MPC Key Management, Segregated Client Ledger, Policy Engine, and Ancillary Audit logging.
- Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Synchroniser architecture, domain entities (`src/dca_service/core/blockchain_sync.py`), and storage adapters (`src/dca_service/adapters/timescaledb_adapter.py`).
- Comprehensive pytest suite covering dual-write workflows, error recovery, and TimescaleDB hypertable chunk archiving policies.
- Diátaxis documentation suite covering institutional DCA-as-a-Service architecture, implementation patterns, regulatory frameworks, and PostgreSQL/TimescaleDB time-series sync design.
- Open-Source MPC Wallet System Architecture documentation based on Coinbase `cb-mpc` cryptography library ([`docs/explanation/open-source-mpc-wallet-architecture.md`](docs/explanation/open-source-mpc-wallet-architecture.md)).
- Research Commercialisation Fund (RCF) and Digital Asset Custodian (DAC) proposal documentation anchored on Percona Server for PostgreSQL ([`docs/explanation/research-commercialisation-fund-dac-proposal.md`](docs/explanation/research-commercialisation-fund-dac-proposal.md)).
- Complete Diátaxis Framework documentation expansion (Tutorials, How-To Guides, and Technical Reference).
