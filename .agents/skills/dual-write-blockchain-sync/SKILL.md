---
okf_version: "0.2"
type: "agent_skill"
title: "Database-First Dual-Write Blockchain Synchronisation Skill"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "dual-write"
  - "blockchain-sync"
  - "postgresql"
  - "reliability"
description: "Enforce database-first dual-write pattern where transactions are committed to PostgreSQL prior to blockchain broadcast."
resource: "file:///.agents/skills/dual-write-blockchain-sync/SKILL.md"
sources:
  - ".agents/AGENTS.md"
  - "README.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
name: "dual-write-blockchain-sync"
---

# Database-First Dual-Write Blockchain Synchronisation Skill

## Overview

Guarantees transaction persistence and state reconciliation during network partitioning.

## Workflow

1. Write transaction record to PostgreSQL database first.
2. Mark transaction status as `SyncState.PENDING_BLOCKCHAIN`.
3. Broadcast transaction to blockchain network.
4. Update status to `SyncState.CHAIN_CONFIRMED` or `SyncState.SYNC_FAILED` based on network receipt.


---

### Deep State of Mind (DSOM) AI Protocol Compliance

* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification
* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)
* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix

---
