---
okf_version: '0.2'
type: explanation
title: Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Architecture
timestamp: '2026-08-25T00:00:00Z'
topics:
- percona
- postgresql
- timescaledb
- dual-write
- hypertables
- blockchain-sync
description: Architectural specification of the database-first dual-write pattern
  using Percona Server for PostgreSQL and TimescaleDB hypertables.
resource: file:///docs/explanation/percona-timescaledb-blockchain-sync.md
sources:
- README.md
- src/dca_service/adapters/timescaledb_adapter.py
generated: jules
verified: true
status: approved
stale_after: '2027-08-25T00:00:00Z'
language: en-GB
---
# Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Architecture

## 1. Architectural Overview & Core Rationale

In institutional digital custody platforms, managing transaction processing, auditability, and real-time analytical queries requires balancing high-throughput database read/write performance with immutable blockchain ledger verification.

Directly relying on blockchain nodes as primary data stores introduces severe analytical bottlenecks, latency overheads, and exorbitant on-chain storage costs. Blockchains are fundamentally time-series structures—append-only, timestamped, and sequentially ordered—yet querying historical or real-time analytical data directly from node RPCs is impractical for production systems.

To resolve these constraints, the Digital Custody Asset (DCA) Platform adopts a **Dual-Write Architecture**:
1. **Primary Database Persistence:** All inbound and outbound transactional data, logs, and account balances are written directly to **Percona Server for PostgreSQL** powered by the **TimescaleDB** time-series extension.
2. **Blockchain Broadcast & Settlement:** Once stored and validated within the local database, essential transaction parameters (timestamp, account ID, transactional value, hash digest) are queued and broadcast to the blockchain node.

```text
+------------------------+      1. Write Transaction       +------------------------------------+
| Application Service /  | ------------------------------> | Percona Server for PostgreSQL      |
| Core Custody Engine    |                                 | (TimescaleDB Hypertables)          |
+------------------------+                                 +------------------------------------+
           |                                                                 |
           | 2. Queue for Broadcast                                          | Analytical Queries
           v                                                                 v
+------------------------+      3. Broadcast Tx Payload    +------------------------------------+
| Blockchain Sync        | ------------------------------> | Blockchain Ledger Node             |
| Worker Engine          |                                 | (Bitcoin / Ethereum / L2 Network)  |
+------------------------+                                 +------------------------------------+
```

---

## 2. Percona Server for PostgreSQL & High Availability

**Percona Server for PostgreSQL** is chosen as the foundational database engine for institutional deployment due to its enterprise-grade operational tooling, enhanced security features, and robust High Availability (HA) capabilities.

### 2.1 High Availability Architecture

- **Patroni & Consensus Clustering:** Automatic failover orchestration managed via Patroni with an Etcd or Distributed Consensus store. Primary nodes handle streaming write workloads, while standby replicas maintain read-scalable read models.

- **Streaming Replication:** Production clusters can be configured using synchronous streaming replication (`synchronous_commit = on` or `remote_apply`) or asynchronous streaming replication. Under synchronous commit, the primary node waits for standby acknowledgement before committing transactions, targeting near-zero RPO (Recovery Point Objective) with failover times bounded by Patroni health check timeouts.

- **Point-In-Time Recovery (PITR):** PITR relies on a valid physical base backup combined with continuous Write-Ahead Logging (WAL) archiving. When a target timestamp or WAL location is specified, PostgreSQL restores from base backup and replays WAL records up to the desired recovery point target.

---

## 3. TimescaleDB Extension & Time-Series Data Optimisation

Blockchains operate as immutable, append-only time-series databases. Using traditional relational table layouts for high-volume blockchain logs causes performance degraded under high transaction velocity due to index bloat.

**TimescaleDB** transforms PostgreSQL into a high-performance time-series database through **Hypertables**:
- **Automatic Partitioning (Chunks):** Hypertables automatically partition incoming data into discrete time-based chunks (e.g., daily or weekly ranges) alongside space partitioning.
- **Append-Only Write Performance:** Write operations hit active, recent memory-resident chunks, avoiding deep index traversals typical of standard B-Trees.
- **Real-Time Analytics & Aggregations:** Continuous aggregate views compute rollups and metrics (e.g., hourly transactional throughput, volume by asset type) in real-time.

---

## 4. Storage Optimisation & Hypertable Archiving Strategy

A critical challenge with dual-write models is storage expansion. While blockchain on-chain data cannot be truncated or pruned easily on node storage, database storage can be dynamically managed.

### 4.1 Chunk Compression & Cold Storage Archiving

- **Native Columnar Compression:** TimescaleDB native compression compresses historical chunks by up to 90%+ using run-length encoding, Delta-of-Delta, and Gorilla compression algorithms.

- **Hypertable Archiving:** In production deployments, aged hypertable chunks (e.g., older than 90 days) can be marked read-only, compressed, or decoupled and moved to object storage (e.g., S3 / MinIO) while remaining queryable via database Foreign Data Wrappers (FDW). Note that `TimescaleDBAdapter.apply_archiving_policy` provides a simulated in-memory metadata state transition for testing and evaluation purposes.

- **Blockchain Storage Partitioning:** High-overhead data remains in database storage. In the reference adapter implementation, `BlockchainNodeAdapter.broadcast_transaction` broadcasts the full transaction payload; maintaining minimal cryptographic proof data on-chain represents a future production target to minimise cost and chain bloat.

---

## 5. Dual-Write Lifecycle & Transactional States

To ensure deterministic consistency between Percona Server for PostgreSQL and the destination blockchain ledger, transactions progress through structured state transitions.

| State Name | Description | Database Action | Blockchain Action |
| :--- | :--- | :--- | :--- |
| `DB_RECORDED` | Transaction record inserted into TimescaleDB hypertable. | Written to local hypertable log. | Not yet submitted. |
| `PENDING_BLOCKCHAIN` | Transaction payload queued for broadcast. | Status updated; retry counter initialised. | Submitted to mempool / node RPC. |
| `CHAIN_CONFIRMED` | Block inclusion verified on-chain. | Block ID & Tx Hash attached (reference implementation behavior). | Confirmed on ledger. |
| `SYNC_FAILED` | Transmission error or execution revert on-chain. | Marked failed; failure reason logged. | Reverted / dropped. |

### 5.1 Dual-Write Flow Logic

1. Core application initialises transaction request.
2. Transaction entry is inserted into TimescaleDB hypertable (`DB_RECORDED`).
3. Blockchain Synchroniser background worker fetches pending records.
4. Transaction is broadcast to target blockchain RPC node (`PENDING_BLOCKCHAIN`).
5. Worker listens for block confirmation; once inclusion is verified, database record status transitions to `CHAIN_CONFIRMED` with block metadata attached.

*Note: In this reference codebase, `DualWriteBlockchainSyncService.process_new_transaction` illustrates the synchronous reference execution path for write-first-then-broadcast state transitions.*

---

## 6. Key Distinction: Blockchain Technology vs Database Encryption

A common point of confusion in institutional architecture is conflating the roles of **Database Encryption** (e.g. Transparent Data Encryption / TDE in PostgreSQL) and **Blockchain Technology**. Both are critical cryptographic mechanisms, yet they solve fundamentally distinct security concerns.

| Dimension / Feature | Database Encryption (Percona PostgreSQL TDE & TLS) | Blockchain Technology (Public/Private Ledgers) |
| :--- | :--- | :--- |
| **Primary Purpose** | **Confidentiality:** Ensures data at rest (via Transparent Data Encryption / TDE) and data in transit (via TLS transport security) cannot be read by unauthorised third parties or external intruders. | **Tamper Evidence & Integrity Verification:** Enables detection of payload changes or historical alterations once confirmed on-chain. |
| **Core Concept** | Encrypts database files on disk (TDE) and network packets on the wire (TLS). Only authorised keyholders / TLS clients can decrypt and access contents. | Open/permissioned append-only ledger recording immutable "digital fingerprints" (cryptographic hash digests). Any modification breaks hash chain verification. |
| **Threat Protection** | Protects against physical hard drive theft, storage media compromise, and network eavesdropping. | Provides tamper evidence against internal fraud, unauthorised database administrator (DBA) manipulation, and retroactive log falsification by allowing reconciliation to detect payload modifications. |

By pairing **Database Encryption** within Percona Server for PostgreSQL (TDE for data at rest, TLS for data in transit) with **Blockchain Synchronization** (to anchor immutable hashes on-chain), the DCA Platform achieves comprehensive security covering confidentiality alongside tamper evidence. Verification procedure: after `BlockchainNodeAdapter.broadcast_transaction` returns the stored transaction hash, fetch the on-chain record using `get_on_chain_transaction(entry.tx_hash)`, recompute SHA-256 digest from `record["payload"]`, and compare the recomputed value with both `record["tx_hash"]` and the stored transaction hash, while retaining independent access-control and security controls.

---

## 7. Summary of Architectural Benefits

- **High Speed & Low Latency:** Queries for balances, audit logs, and analytics execute against Percona PostgreSQL in milliseconds instead of scanning raw blockchain blocks.
- **Immutable On-Chain Verification:** Blockchain storage is leveraged exclusively for settlement and cryptographic immutability.
- **Scalable Archiving:** TimescaleDB chunk compression and archiving keep local storage lean while preserving full history accessibility.
- **Institutional Failover:** Percona HA tooling targets bounded availability and recovery-time objectives (e.g. RPO near zero, RTO bounded by failover orchestration timeouts), where overall disaster-recovery readiness depends on configured backup policies and continuous WAL-archive procedures.
