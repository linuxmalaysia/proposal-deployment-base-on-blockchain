---
okf_version: "0.2"
type: "explanation"
title: "Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Architecture"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# Percona Server for PostgreSQL & TimescaleDB Dual-Write Blockchain Architecture

## 1. Architectural Overview & Core Rationale

In institutional digital custody platforms, managing transaction processing, auditability, and real-time analytical queries requires balancing high-throughput database read/write performance with immutable blockchain ledger verification.

Directly relying on blockchain nodes as primary data stores introduces severe analytical bottlenecks, latency overheads, and exorbitant on-chain storage costs. Blockchains are fundamentally time-series structures—append-only, timestamped, and sequentially ordered—yet querying historical or real-time analytical data directly from node RPCs is impractical for production systems.

To resolve these constraints, the Digital Custody Asset (DCA) Platform adopts a **Dual-Write Architecture**:
1. **Primary Database Persistence:** All inbound and outbound transactional data, logs, and account balances are written directly to **Percona Server for PostgreSQL** powered by the **TimescaleDB** time-series extension.
2. **Blockchain Broadcast & Settlement:** Once stored and validated within the local database, essential transaction parameters (timestamp, account ID, transactional value, hash digest) are queued and broadcast to the blockchain node.

```
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
- **Streaming Replication:** Asynchronous and synchronous streaming replication ensure standby nodes maintain near-zero lag state replication.
- **Point-In-Time Recovery (PITR):** Continuous Write-Ahead Logging (WAL) archiving paired with full physical base backups enables precise database state recovery to any microsecond timestamp in the event of hardware or system failure.

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
- **Hypertable Archiving:** Aged hypertable chunks (e.g., older than 90 days) can be marked read-only, compressed, or decoupled and moved to object storage (e.g., S3 / MinIO) while remaining queryable via database foreign data wrappers.
- **Blockchain Storage Partitioning:** High-overhead data remains in database storage; only minimal cryptographic proof data is maintained on-chain to minimise cost and chain bloat.

---

## 5. Dual-Write Lifecycle & Transactional States

To ensure deterministic consistency between Percona Server for PostgreSQL and the destination blockchain ledger, transactions progress through structured state transitions.

| State Name | Description | Database Action | Blockchain Action |
| :--- | :--- | :--- | :--- |
| `DB_RECORDED` | Transaction record inserted into TimescaleDB hypertable. | Written to local hypertable log. | Not yet submitted. |
| `PENDING_BLOCKCHAIN` | Transaction payload queued for broadcast. | Status updated; retry counter initialised. | Submitted to mempool / node RPC. |
| `CHAIN_CONFIRMED` | Block inclusion verified on-chain. | Block ID, Tx Hash, & Block Timestamp attached. | Confirmed on ledger. |
| `SYNC_FAILED` | Transmission error or execution revert on-chain. | Marked failed; failure reason logged. | Reverted / dropped. |

### 5.1 Dual-Write Flow Logic
1. Core application initialises transaction request.
2. Transaction entry is inserted into TimescaleDB hypertable (`DB_RECORDED`).
3. Blockchain Synchroniser background worker fetches pending records.
4. Transaction is broadcast to target blockchain RPC node (`PENDING_BLOCKCHAIN`).
5. Worker listens for block confirmation; once inclusion is verified, database record status transitions to `CHAIN_CONFIRMED` with block metadata attached.

---

## 6. Summary of Architectural Benefits

- **High Speed & Low Latency:** Queries for balances, audit logs, and analytics execute against Percona PostgreSQL in milliseconds instead of scanning raw blockchain blocks.
- **Immutable On-Chain Verification:** Blockchain storage is leveraged exclusively for settlement and cryptographic immutability.
- **Scalable Archiving:** TimescaleDB chunk compression and archiving keep local storage lean while preserving full history accessibility.
- **Institutional Failover:** Percona HA tooling ensures continuous availability and disaster recovery readiness.
