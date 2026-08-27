---
okf_version: '0.2'
type: explanation
title: Open-Source MPC Wallet System Architecture via cb-mpc
timestamp: '2026-08-25T00:00:00Z'
topics:
- mpc
- cb-mpc
- threshold-signatures
- dkg
- key-management
- cryptography
description: Technical explanation of Coinbase cb-mpc integration for threshold signature
  quorums and distributed key generation.
resource: file:///docs/explanation/open-source-mpc-wallet-architecture.md
sources:
- README.md
- src/dca_service/core/key_management.py
generated: jules
verified: true
status: approved
stale_after: '2027-08-25T00:00:00Z'
language: en-GB
---
# Open-Source MPC Wallet System Architecture via Coinbase `cb-mpc`

## 1. Executive Summary & Strategic Rationale

Multi-Party Computation (MPC) has emerged as the gold standard for institutional digital asset custody. Traditional single-key hardware or multi-signature setups suffer from single points of failure, rigid on-chain execution costs, and lack of cross-chain compatibility.

By integrating Coinbase’s open-source MPC cryptography library ([`cb-mpc`](https://github.com/coinbase/cb-mpc)) as a planned infrastructure component into the Digital Custody Asset (DCA) Platform, we construct a fully open-source, non-custodial or co-custodial wallet architecture. This planned architecture links independent cryptographic signing nodes, enforces strict policy quorums, and seamlessly coordinates with our Percona Server for PostgreSQL and TimescaleDB dual-write blockchain synchronisation engine.

---

## 2. Technical Foundations of Coinbase `cb-mpc`

The `cb-mpc` library provides battle-tested, high-performance C++/Go cryptographic primitives implementing state-of-the-art threshold signature schemes (TSS).

### 2.1 Supported Cryptographic Schemes & Curves (Target Integration Capabilities)

- **Threshold ECDSA (secp256k1 / secp256r1):** Planned integration for threshold signing across Bitcoin, Ethereum, EVM-compatible networks, and Cosmos based on GG20 (Gennaro-Goldfeder 2020) and Lindell protocols.

- **Threshold EdDSA / Ed25519 vs. Probabilistic Schnorr:** Note that `cb-mpc` implements a probabilistic Schnorr protocol rather than deterministic EdDSA (RFC 8032). Standard Ed25519 signature verification requires strict application-level enforcement of a unique-message signing policy (never signing the same message digest twice regardless of nonce reuse) to preserve signature randomness and prevent key leakage. Byte-for-byte EdDSA compatibility remains conditional on enforcing this unique-message policy.

- **Zero-Knowledge Proofs (ZKPs):** Planned integration of Range Proofs and Paillier key generation verification to prevent rogue-key attacks during Distributed Key Generation (DKG) and signing rounds.

### 2.2 Key Mathematical Properties

1. **Secret Sharing without Reconstruction:** Private key $SK$ is generated across $n$ parties as distinct polynomial secret shares $SK_1, SK_2, \dots, SK_n$. The full secret key $SK$ **never exists** in memory on any single device or server at any point during its lifecycle.

2. **Threshold Quorum Signing ($t$-of-$n$):** Any subset of $t$ out of $n$ participants can co-operatively produce a standard signature $\sigma$ that is byte-for-byte indistinguishable from a conventional single-key signature under the applicable scheme.

3. **On-Chain Privacy & Efficiency:** Blockchain networks observe standard single signatures, eliminating multi-sig transaction gas overheads and obscuring key management policy topologies from public chain inspectors.

---

## 3. End-to-End Wallet System Topology & Component Linkage

To establish an open-source MPC wallet infrastructure, the system orchestrates three primary physical node layers linked over encrypted peer-to-peer (P2P) transport.

```text
+-----------------------+        +-----------------------+        +-----------------------+
|  Node A: Custodian    |        |   Node B: Client      |        |  Node C: Recovery     |
|  MPC Compute Engine   |        |   Approval & Bridge   |        |  Guard / HSM (Warm)   |
+-----------------------+        +-----------------------+        +-----------------------+
            |                                |                                |
            |         Encrypted P2P          |         Encrypted P2P          |
            +--------------------------------+--------------------------------+
                                             |
                                             v
                           +------------------------------------+
                           |  MPC Orchestrator & Relay Bus      |
                           |  (Untrusted gRPC Transport Layer)  |
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

- **Node A (Custodian Engine Node):** An isolated compute service execution boundary that utilizes AWS KMS, Google Cloud KMS, or a PKCS#11 HSM exclusively to protect root key material and unwrap local key shares. The KMS/HSM does not host or execute arbitrary `cb-mpc` code.

- **Node B (Client Co-Signer / Mobile / WebAuthn):** Node B provides client transaction approval and confirmation. Rather than running C++ `cb-mpc` code directly on untrusted mobile devices or WebAuthn runtimes, Node B executes within a defined and validated native bridge server or secure enclave boundary that proxies verified client approvals to native MPC worker processes.

- **Node C (Institutional Recovery Guard Node):** Offline or air-gapped warm backup node managed by an independent trustee or secondary security layer. Activated during client key loss or disaster recovery.

### 3.2 Transport Security & Trust Boundary

- **MPC Orchestrator & Relay Bus Trust Boundary:** The Relay Bus terminates node-to-relay mTLS for network connection routing. The Relay Bus itself is explicitly treated as an **untrusted transport intermediary**.
- **End-to-End Node-to-Node Authentication & Encryption:** Because `cb-mpc` delegates transport security to the integrating application, all node-to-node protocol messages are wrapped in application-layer end-to-end encryption and MAC authentication. Message headers bind the sender identity, recipient identity, caller-supplied `SessionID`, round identifier, and monotonic sequence number to prevent eavesdropping, tampering, or message replay by the Relay Bus or external attackers.

---

## 4. Operational Protocol Flows

### 4.1 Distributed Key Generation (DKG)

1. **Protocol Initialisation:** The MPC Orchestrator triggers DKG as a planned adapter step across Node A, Node B, and Node C using `cb-mpc` C++/Go bindings.

2. **Commitment Exchange:** Each node generates a random polynomial, computes public commitments, and broadcasts polynomial commitments while sending encrypted secret shares to peer nodes over authenticated channels.

3. **Zero-Knowledge Verification:** Each node verifies received shares against zero-knowledge range proofs to guarantee valid mathematical structure without disclosing share secrets.

4. **Public Key Derivation:** All parties independently sum public key commitments to derive the master wallet public address $PK = g^{SK}$.

5. **Key Share Persistence:** Encrypted node secret shares $SK_i$ are stored in a dedicated `KeyVault` store (protected via AEAD envelope encryption) rather than directly in sub-account ledgers. The ledger retains only a vault key reference ID and immutable audit hash identifier.

### 4.2 Threshold Signing & Policy Validation Flow

1. **Transaction Proposal & Runtime Validation:** Client or API service submits `TransactionProposal` to the Policy Engine. `TransactionProposal.__post_init__` verifies that `signers` is supplied as a list of non-empty strings without duplicates. `PolicyRule.evaluate` enforces runtime validation requiring explicit verifier attestations (`verified_authenticated_signers`) and membership in `authorized_signers`.

2. **Pre-Hashing & Session ID Ownership Contract:** Upon policy approval, the core engine hashes the transaction payload to produce digest $H(m)$. The application defines an unambiguous ownership contract for `SessionID`: any caller-supplied `SessionID` is preserved unchanged. Derived subprotocol IDs append deterministic subprotocol suffixes (`{SessionID}#dkg`, `{SessionID}#sign_r1`).

3. **MPC Interactive Round Execution (`cb-mpc`):**

   - **Session & Message Sequence Validation:** Participating nodes validate peer identities and check `SessionID`, round identifier, and monotonic message sequence numbers. Out-of-order, duplicate, or replayed messages are immediately rejected.

   - **Round 1 (Nonces & Commitments):** Node A and Node B exchange ephemeral nonces and commitments bound to `SessionID`.

   - **Round 2 (Scheme-Specific Preimages & Partial Signatures):** Participating nodes enforce scheme-specific inputs: raw transaction preimages for ECDSA / BIP340 Schnorr, and original unhashed messages for EdDSA/Ed25519 APIs with domain separation. Each node validates the application-level unique-message digest policy before computing partial signature $s_i$ using encrypted share $SK_i$.

   - **Round 3 (Aggregation & Abort Handling):** Node A aggregates partial signatures $s_A$ and $s_B$ using `cb-mpc` interpolation routines to yield final signature $\sigma$. If any node disconnects or fails zero-knowledge verification, the abort-handling flow propagates cancellation to every pending `receive` and `receive_all` transport operation, settles blocked callers, marks the session terminal, rejects late messages, and invalidates ephemeral nonces.

4. **On-Chain Dual-Write Settlement & State Machine:**

   - **`DB_RECORDED`:** Signature $\sigma$ is attached to the stable transaction payload and persisted to TimescaleDB hypertable.

   - **`PENDING_BLOCKCHAIN`:** Payload is queued and broadcast to the target blockchain node RPC.

   - **`CHAIN_CONFIRMED`:** Block inclusion verified on-chain; block metadata attached.

   - **`SYNC_FAILED` Reconciliation Flow:** `DualWriteBlockchainSyncService` distinguishes unknown broadcast outcomes from confirmed rejections/reverts. It computes and persists a stable transaction payload digest, queries on-chain state via `get_on_chain_transaction` prior to re-broadcasting to prevent duplicate submissions, and marks confirmed on-chain reverts as terminal failures (`TERMINAL_REVERT`).

---

## 5. Security Architecture, Key Share Protection & Auditing

### 5.1 Envelope Encryption for Key Shares (Planned Infrastructure Contract)

Secret key shares $SK_i$ persisted in the `KeyVault` store are planned to use an application-managed AEAD envelope encryption contract compatible with `cb-mpc`:
- **AEAD Cipher & Nonce Storage:** AES-256-GCM symmetric encryption with a unique cryptographically random 96-bit nonce generated for every write operation. The generated GCM nonce will be stored alongside versioned fields for nonce, AAD, ciphertext, and authentication tag so decryption can reconstruct all required inputs after restart.
- **Tag Storage & Associated Data Binding:** The 128-bit authentication tag will be stored alongside the ciphertext. Additional Associated Data (AAD) binds protocol type, curve identifier, blob version, vault ID, and party identity context.
- **Context Validation:** Before decryption, the application will validate versioned AAD context parameters, nonces, and AEAD tags to prevent ciphertext transposition or cross-party substitution attacks.
- **DEK & KEK Responsibilities:** Data Encryption Key (DEK) encrypts raw shares, while Key Encryption Key (KEK) hosted in KMS/HSM wraps DEK. Note: These specific encryption, DEK/KEK handling, and nonce/tag persistence guarantees represent planned infrastructure specifications for future storage layer integration and are not currently enforced inside core in-memory `KeyVault.add_key_share`.

### 5.2 Proactive Secret Sharing & Key Refresh

- **Refresh Scope:** `cb-mpc` proactive secret reshuffling generates new polynomial shares $SK_i'$ while preserving the same combined public key $PK$. Renders stolen historic key shares mathematically useless. It does not allow arbitrary cross-epoch share combination and protects only when fewer than the signing threshold $t$ of shares are collected within each epoch.
- **Compromise Limitation:** Proactive refresh **cannot** revoke or invalidate a key if an attacker has already obtained $t$ shares within a single epoch or reconstructed $SK$.
- **Key Compromise Response Protocol:** If key share compromise is detected, the protocol requires stopping use of the affected key material immediately, performing a fresh DKG to generate a new master key $PK_{new}$, and migrating on-chain assets to $PK_{new}$.

### 5.3 Audit Trails & Compliance

All MPC rounds, DKG invocations, policy evaluations, and state transitions generate structured audit events recorded in immutable audit logs. These logs provide supporting audit evidence suitable for SOC 1 Type II and SOC 2 Type II evaluation frameworks when evaluated alongside operational controls and assessment period attestations.

---

## 6. Summary of System Integration Benefits

- **100% Open-Source Cryptography:** Target utilisation of transparent C++/Go implementations from Coinbase (`cb-mpc`), eliminating proprietary vendor lock-in.
- **Clean Architecture Integration:** Pure mathematical constructs interface cleanly with core key management primitives (`src/dca_service/core/key_management.py`), preserving zero-dependency domain boundaries.
- **Enterprise Performance:** High-speed off-chain interactive signing linked directly to Percona Server for PostgreSQL and TimescaleDB dual-write pipelines.
