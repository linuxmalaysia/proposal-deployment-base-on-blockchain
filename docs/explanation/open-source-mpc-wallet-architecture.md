---
okf_version: "0.2"
type: "explanation"
title: "Open-Source MPC Wallet System Architecture via cb-mpc"
created: "2026-08-25"
status: "proposed"
language: "en-GB"
---

# Open-Source MPC Wallet System Architecture via Coinbase `cb-mpc`

## 1. Executive Summary & Strategic Rationale

Multi-Party Computation (MPC) has emerged as the gold standard for institutional digital asset custody. Traditional single-key hardware or multi-signature setups suffer from single points of failure, rigid on-chain execution costs, and lack of cross-chain compatibility.

By integrating Coinbase’s open-source MPC cryptography library ([`cb-mpc`](https://github.com/coinbase/cb-mpc)) as a planned infrastructure component into the Digital Custody Asset (DCA) Platform, we construct a fully open-source, non-custodial or co-custodial wallet architecture. This planned architecture links independent cryptographic signing nodes, enforces strict policy quorums, and seamlessly coordinates with our Percona Server for PostgreSQL and TimescaleDB dual-write blockchain synchronisation engine.

---

## 2. Technical Foundations of Coinbase `cb-mpc`

The `cb-mpc` library provides battle-tested, high-performance C++/Go cryptographic primitives implementing state-of-the-art threshold signature schemes (TSS).

### 2.1 Supported Cryptographic Schemes & Curves (Planned Integration Capabilities)

- **Threshold ECDSA (secp256k1 / secp256r1):** Implements threshold signing for Bitcoin, Ethereum, EVM-compatible networks, and Cosmos based on GG20 (Gennaro-Goldfeder 2020) and Lindell protocols.

- **Threshold EdDSA / Ed25519 vs. Probabilistic Schnorr:** Note that `cb-mpc` implements a probabilistic Schnorr protocol rather than deterministic EdDSA (RFC 8032). Standard Ed25519 signature verification requires strict enforcement of a unique-message signing policy (never signing the same message digest twice under identical nonces) to preserve signature randomness and prevent key leakage.

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
|  MPC Compute Engine   |        |   Co-Signer (Mobile)  |        |  Guard / HSM (Warm)   |
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

- **Node A (Custodian MPC Compute Service):** An isolated compute service execution boundary that utilizes AWS KMS, Google Cloud KMS, or a PKCS#11 HSM exclusively to protect root key material and unwrap local key shares. The KMS/HSM does not host or execute arbitrary `cb-mpc` code.

- **Node B (Client Co-Signer / Mobile / WebAuthn):** Controlled by client end-users via secure enclaves or mobile SDKs. Initiates or confirms transaction requests.

- **Node C (Institutional Recovery Guard Node):** Offline or air-gapped warm backup node managed by an independent trustee or secondary security layer. Activated during client key loss or disaster recovery.

### 3.2 Transport Security & Trust Boundary

- **MPC Orchestrator & Relay Bus Trust Boundary:** The Relay Bus functions purely as a transport routing layer. It terminates mTLS connections for peer authentication and message routing.
- **End-to-End Message Protection:** `cb-mpc` protocols themselves rely on transport-layer peer authentication. All message payloads routed through the Relay Bus are bound to peer identities and encrypted end-to-end to ensure the Relay Bus cannot tamper with or inspect interactive protocol messages.

---

## 4. Operational Protocol Flows

### 4.1 Distributed Key Generation (DKG)

1. **Protocol Initialisation:** The MPC Orchestrator triggers DKG across Node A, Node B, and Node C using `cb-mpc` C++/Go bindings.

2. **Commitment Exchange:** Each node generates a random polynomial, computes public commitments, and broadcasts polynomial commitments while sending encrypted secret shares to peer nodes over authenticated channels.

3. **Zero-Knowledge Verification:** Each node verifies received shares against zero-knowledge range proofs to guarantee valid mathematical structure without disclosing share secrets.

4. **Public Key Derivation:** All parties independently sum public key commitments to derive the master wallet public address $PK = g^{SK}$.

5. **Key Share Persistence:** Encrypted node secret shares $SK_i$ are stored in a dedicated `KeyVault` store (protected via AEAD envelope encryption) rather than directly in sub-account ledgers. The ledger retains only a vault key reference ID and immutable audit hash identifier.

### 4.2 Threshold Signing & Policy Validation Flow

1. **Transaction Proposal & Runtime Validation:** Client or API service submits `TransactionProposal` to the Policy Engine. `TransactionProposal` and `PolicyRule.evaluate` enforce runtime validation ensuring signer values are distinct, non-empty, authenticated, and explicitly present within `authorized_signers`. Duplicate or unauthenticated signers are immediately rejected with `PolicyViolationError`.

2. **Pre-Hashing & Session ID Derivation:** Upon policy approval, the core engine hashes the transaction payload $H(m)$. A unique caller-managed session ID (`SessionID`) is generated for the interactive signing session, with distinct sub-session IDs derived for subprotocols.

3. **MPC Interactive Round Execution (`cb-mpc`):**

   - **Session & Peer Authentication:** Participating nodes authenticate peer identities over mTLS transport and verify `SessionID` context. Replayed or out-of-order messages are dropped immediately.

   - **Round 1 (Nonces & Commitments):** Node A and Node B exchange ephemeral nonces and commitments bound to `SessionID`.

   - **Round 2 (Partial Signatures):** Each participating node validates the unique-message policy and computes partial signature components $s_i$ using its encrypted share $SK_i$ and digest $H(m)$.

   - **Round 3 (Aggregation & Abort Handling):** Node A aggregates partial signatures $s_A$ and $s_B$ using `cb-mpc` interpolation routines to yield final signature $\sigma = (r, s)$. If any node disconnects, times out, or fails zero-knowledge verification, the session aborts cleanly, invalidating ephemeral nonces.

4. **On-Chain Dual-Write Settlement & State Machine:**

   - **`DB_RECORDED`:** Signature $\sigma$ is attached to transaction payload and persisted to TimescaleDB hypertable.

   - **`PENDING_BLOCKCHAIN`:** Payload is queued and broadcast to the target blockchain node RPC.

   - **`CHAIN_CONFIRMED`:** Block inclusion verified on-chain; block metadata attached.

   - **`SYNC_FAILED` Branch & Reconciliation:** If transmission fails or execution reverts on-chain, state transitions to `SYNC_FAILED` with detailed `failure_reason` logged. The background synchroniser executes idempotent retry logic up to configured max attempts. Unresolved failures trigger automated reconciliation alerts for manual inspection or transaction cancellation.

---

## 5. Security Architecture, Key Share Protection & Auditing

### 5.1 Envelope Encryption & AEAD Persistence Contract

Secret key shares $SK_i$ persisted in the `KeyVault` store use an application-managed AEAD encryption contract compatible with `cb-mpc`:
- **AEAD Cipher:** AES-256-GCM symmetric encryption with unique cryptographically random 96-bit nonces generated for every write operation.
- **Tag Storage & Associated Data Binding:** The 128-bit authentication tag is stored alongside the ciphertext. Additional Associated Data (AAD) binds protocol type, curve identifier, blob version, vault ID, and party identity context.
- **Context Validation:** Before decryption, the application validates AAD context parameters and AEAD tags to prevent ciphertext transposition or cross-party substitution attacks.
- **DEK & KEK Responsibilities:** Data Encryption Keys (DEKs) encrypt raw shares, while Key Encryption Keys (KEKs) hosted in KMS/HSM wrap DEKs.

### 5.2 Proactive Secret Sharing & Key Compromise Recovery

- **Refresh Scope:** `cb-mpc` proactive secret reshuffling generates new polynomial shares $SK_i'$ while leaving $PK$ unchanged. This protects against an attacker collecting $t$ shares across multiple epoch boundaries.
- **Compromise Limitation:** Proactive refresh **cannot** revoke or invalidate a key if an attacker has already reconstructed $SK$ or obtained $t$ shares within a single epoch.
- **Key Compromise Response Protocol:** If a key share compromise is detected within an active epoch, the system triggers an emergency compromise response: immediate key revocation, execution of a fresh DKG protocol to generate a new master key $PK_{new}$, and automated migration of on-chain assets to $PK_{new}$.

### 5.3 Audit Trails & Supporting Evidence

All MPC rounds, DKG invocations, policy evaluations, and state transitions generate structured audit events recorded in immutable audit logs. These logs provide supporting audit evidence suitable for SOC 1 Type II and SOC 2 Type II evaluation frameworks when evaluated alongside operational controls and assessment period attestations.

---

## 6. Summary of System Integration Benefits

- **100% Open-Source Cryptography:** Leverages transparent C++/Go implementations from Coinbase (`cb-mpc`), eliminating proprietary vendor lock-in.

- **Universal Chain Compatibility:** Planned support for standard ECDSA and Ed25519 signatures across Bitcoin, Ethereum, Solana, and EVM chains.

- **Clean Architecture Integration:** Pure mathematical constructs interface cleanly with core key management primitives (`src/dca_service/core/key_management.py`), preserving zero-dependency domain boundaries.

- **Enterprise Performance & Resilience:** High-speed off-chain interactive signing linked directly to Percona Server for PostgreSQL and TimescaleDB dual-write pipelines with robust `SYNC_FAILED` reconciliation.
