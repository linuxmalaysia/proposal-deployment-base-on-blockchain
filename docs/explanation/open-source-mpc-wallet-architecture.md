---
okf_version: "0.2"
type: "explanation"
title: "Open-Source MPC Wallet System Architecture via cb-mpc"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# Open-Source MPC Wallet System Architecture via Coinbase `cb-mpc`

## 1. Executive Summary & Strategic Rationale

Multi-Party Computation (MPC) has emerged as the gold standard for institutional digital asset custody. Traditional single-key hardware or multi-signature setups suffer from single points of failure, rigid on-chain execution costs, and lack of cross-chain compatibility.

By integrating Coinbase’s open-source MPC cryptography library ([`cb-mpc`](https://github.com/coinbase/cb-mpc)) into the Digital Custody Asset (DCA) Platform, we construct a fully open-source, non-custodial or co-custodial wallet infrastructure. This architecture links independent cryptographic signing nodes, enforces strict policy quorums, and seamlessly coordinates with our Percona Server for PostgreSQL and TimescaleDB dual-write blockchain synchronisation engine.

---

## 2. Technical Foundations of Coinbase `cb-mpc`

The `cb-mpc` library provides battle-tested, high-performance C++/Go cryptographic primitives implementing state-of-the-art threshold signature schemes (TSS).

### 2.1 Supported Cryptographic Schemes & Curves
- **Threshold ECDSA (secp256k1 / secp256r1):** Implements threshold signing for Bitcoin, Ethereum, EVM-compatible networks, and Cosmos based on GG20 (Gennaro-Goldfeder 2020) and Lindell protocols.
- **Threshold EdDSA / Ed25519:** Supports Edwards-curve signatures for Solana, Near, and Cardano networks.
- **Zero-Knowledge Proofs (ZKPs):** Integrates Range Proofs and Paillier key generation verification to prevent rogue-key attacks during Distributed Key Generation (DKG) and signing rounds.

### 2.2 Key Mathematical Properties
1. **Secret Sharing without Reconstruction:** Private key $SK$ is generated across $n$ parties as distinct polynomial secret shares $SK_1, SK_2, \dots, SK_n$. The full secret key $SK$ **never exists** in memory on any single device or server at any point during its lifecycle.
2. **Threshold Quorum Signing ($t$-of-$n$):** Any subset of $t$ out of $n$ participants can co-operatively produce a standard signature $\sigma$ that is byte-for-byte indistinguishable from a conventional single-key ECDSA/Ed25519 signature.
3. **On-Chain Privacy & Efficiency:** Blockchain networks observe standard single signatures, eliminating multi-sig transaction gas overheads and obscuring key management policy topologies from public chain inspectors.

---

## 3. End-to-End Wallet System Topology & Component Linkage

To establish an open-source MPC wallet infrastructure, the system orchestrates three primary physical node layers linked over encrypted peer-to-peer (P2P) transport.

```text
+-----------------------+        +-----------------------+        +-----------------------+
|  Node A: Custodian    |        |   Node B: Client      |        |  Node C: Recovery     |
|  MPC Service (Hot)    |        |   Co-Signer (Mobile)  |        |  Guard / HSM (Warm)   |
+-----------------------+        +-----------------------+        +-----------------------+
            |                                |                                |
            |         Encrypted P2P          |         Encrypted P2P          |
            +--------------------------------+--------------------------------+
                                             |
                                             v
                           +------------------------------------+
                           |  MPC Orchestrator & Relay Bus      |
                           |  (gRPC / mTLS Transport Layer)     |
                           +------------------------------------+
                                             |
                                             v
                           +------------------------------------+
                           |  Policy Engine & Rules Validation  |
                           +------------------------------------+
                                             |
                                             v
                           +------------------------------------+
                           | Percona PostgreSQL & TimescaleDB   |
                           | (Hypertable State & Dual-Write)    |
                           +------------------------------------+
```

### 3.1 Participant Node Roles in a 2-of-3 Quorum Model
- **Node A (Custodian Engine Node):** Hosted within isolated cloud security modules (AWS KMS / GCP Cloud KMS / PKCS#11 HSM). Automatically evaluates policy before signing.
- **Node B (Client Co-Signer / Mobile / WebAuthn):** Controlled by client end-users via secure enclaves or mobile SDKs. Initiates or confirms transaction requests.
- **Node C (Institutional Recovery Guard Node):** Offline or air-gapped warm backup node managed by an independent trustee or secondary security layer. Activated during client key loss or disaster recovery.

---

## 4. Operational Protocol Flows

### 4.1 Distributed Key Generation (DKG)

1. **Protocol Initialisation:** The MPC Orchestrator triggers DKG across Node A, Node B, and Node C using `cb-mpc` bindings.
2. **Commitment Exchange:** Each node generates a random polynomial, computes public commitments, and broadcasts polynomial commitments while sending encrypted secret shares to peer nodes.
3. **Zero-Knowledge Verification:** Each node verifies received shares against zero-knowledge range proofs to guarantee valid mathematical structure without disclosing share secrets.
4. **Public Key Derivation:** All parties independently sum public key commitments to derive the master wallet public address $PK = g^{SK}$.
5. **Key Share Persistence:** Node secret shares $SK_i$ are encrypted using local hardware keys (e.g. envelope encryption via AWS KMS or local Secure Enclave) and persisted to Percona PostgreSQL sub-account ledgers.

### 4.2 Threshold Signing & Policy Validation Flow

1. **Transaction Proposal:** Client or API service submits transaction proposal (amount, asset, destination address) to the DCA Policy Engine.
2. **Policy Engine Evaluation:** The Policy Engine validates spending limits, multi-signer authorization rules, velocity caps, and address allowlists.
3. **Message Pre-Hashing:** Upon policy approval, the core engine hashes the transaction payload to produce digest $H(m)$.
4. **MPC Interactive Round Execution (`cb-mpc`):**
   - **Round 1 (Nonces & Commitments):** Node A and Node B exchange ephemeral nonces and cryptographic commitments via mTLS gRPC relay.
   - **Round 2 (Partial Signatures):** Each participating node computes partial signature components $s_i$ using its encrypted secret share $SK_i$ and the message hash $H(m)$.
   - **Round 3 (Aggregation):** Node A aggregates partial signatures $s_A$ and $s_B$ using `cb-mpc` interpolation routines to yield final signature $\sigma = (r, s)$.
5. **On-Chain Dual-Write Settlement:**
   - Signature $\sigma$ is attached to the raw transaction payload.
   - Transaction entry is logged into TimescaleDB hypertable (`DB_RECORDED` -> `PENDING_BLOCKCHAIN`).
   - Transaction is broadcast to target blockchain RPC node and confirmed (`CHAIN_CONFIRMED`).

---

## 5. Security Architecture, Key Share Protection & Auditing

### 5.1 Envelope Encryption for Key Shares
Secret key shares residing on storage media must be protected using Envelope Encryption:
- **Data Encryption Key (DEK):** Generates AES-256-GCM symmetric keys to encrypt raw `cb-mpc` key share payloads.
- **Key Encryption Key (KEK):** DEKs are wrapped by Hardware Security Modules (HSM) or Cloud Key Management Services (KMS).

### 5.2 Proactive Secret Sharing & Key Refresh
To prevent slow, long-term exfiltration of secret shares from static systems, the infrastructure periodically executes `cb-mpc` proactive secret reshuffling:
- Generates new secret shares $SK_i'$ for all parties.
- Master public address $PK$ and underlying secret key $SK$ remain **unchanged**.
- Renders stolen historic key shares mathematically useless.

### 5.3 Audit Trails & Compliance
All MPC rounds, DKG invocations, and policy evaluations generate structured audit events recorded in immutable audit logs, fully compliant with SOC 1 Type II and SOC 2 Type II audit requirements.

---

## 6. Summary of System Integration Benefits

- **100% Open-Source Cryptography:** Built on transparent, audited C++/Go implementations from Coinbase (`cb-mpc`), eliminating proprietary vendor lock-in.
- **Universal Chain Compatibility:** Supports standard ECDSA and Ed25519 signatures, enabling native integration across Bitcoin, Ethereum, Solana, and EVM chains without smart contract dependencies.
- **Clean Architecture Integration:** Pure mathematical constructs interface cleanly with core key management primitives (`src/dca_service/core/key_management.py`), preserving zero-dependency domain boundaries.
- **Enterprise Performance:** High-speed off-chain interactive signing linked directly to Percona Server for PostgreSQL and TimescaleDB dual-write pipelines.
