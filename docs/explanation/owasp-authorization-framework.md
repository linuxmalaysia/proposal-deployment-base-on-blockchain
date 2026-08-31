---
okf_version: "0.2"
type: "explanation"
title: "OWASP Authorization Framework Adoption & Access Control Architecture"
timestamp: "2026-08-31T00:00:00Z"
topics:
  - "authorization"
  - "owasp"
  - "rbac"
  - "abac"
  - "security"
  - "access-control"
description: "Architectural documentation detailing the adoption and implementation of OWASP Authorization Cheat Sheet principles across the Digital Custody Asset (DCA) as a Service platform."
resource: "file:///docs/explanation/owasp-authorization-framework.md"
sources:
  - "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html"
  - "src/dca_service/web_app.py"
  - "tests/test_rbac_and_resilience_scenarios.py"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-31T00:00:00Z"
language: "en-GB"
---

# 🛡️ OWASP Authorization Framework Adoption & Access Control Architecture

The **Digital Custody Asset (DCA) as a Service** platform and **Research Commercialisation Fund (RCF)** web application enforce multi-layered access control, role separation, and cryptographic authorisation mechanisms.

This document articulates how the platform adopts the 11 core recommendations of the [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) within its Concentric Clean Architecture and FastAPI service endpoints.

---

## 🏛️ Executive Summary of Authorization Governance

Broken Access Control (OWASP Top 10 A01:2021) represents one of the most severe risks to digital asset custodians and financial infrastructure. The platform mitigates authorization vulnerabilities through:

1. **Strict Role-Based & Attribute-Based Access Control (RBAC/ABAC)** across institutional roles (`superuser`, `admin`, `auditor`, `operator`, `investor`, `user`).
2. **Deny-by-Default Execution** failing closed on missing, malformed, or unverified JWT tokens.
3. **Direct SQL Database Mandate for Superuser Password Resets**, enforcing strict separation of administrative privileges and blocking web-based superuser credential modification.
4. **Cryptographic IDOR Prevention** using W3C Decentralised Identifiers (`did:univ:...`) and SHA-256 evidence digests instead of guessable sequential primary keys.

---

## 📋 Comprehensive OWASP Authorization Principles Adoption Matrix

| # | OWASP Recommendation | DCA Service Implementation & Control Architecture |
|---|----------------------|--------------------------------------------------|
| **1** | **Enforce Least Privileges** | Horizontal and vertical role segregation. Superuser (`dca_sys_root`) is restricted to governance audit logs and cannot perform day-to-day administrative user creation via web API without explicit credentials. Administrative management requires the `admin` role (`dca_admin_mgr`). |
| **2** | **Deny by Default** | All protected endpoints (`/api/users`, `/api/init-db`, `/api/investor-assets`) fail closed. Requests lacking valid Bearer JWT tokens or explicit authorization headers immediately return `401 Unauthorized` or `403 Forbidden`. |
| **3** | **Validate Permissions on Every Request** | Stateless HMAC-SHA256 JWT validation executed on every request requiring authentication. Claims checked include expiration (`exp`), issuer (`iss`), audience (`aud`), role (`role`), and accredited investor status (`accredited_investor`). |
| **4** | **Review Authorization Logic & Custom Implementation** | Custom cryptographically sound JWT verification routine using constant-time comparisons (`hmac.compare_digest`) to prevent timing side-channel attacks during signature and password hash verification. |
| **5** | **Prefer ABAC & ReBAC over RBAC** | Combines role hierarchy with dynamic contextual attributes (e.g., NDA execution state for investor data room access, DID ownership, and TimescaleDB transactional outbox state). |
| **6** | **Prevent IDOR & Guessable Lookup IDs** | Eliminates sequential integer primary keys in public interfaces. Objects are referenced via immutable W3C DIDs (`did:univ:asset-9f82a1`), UUIDv4 identifiers, or SHA-256 evidence hashes (`sha256:...`). |
| **7** | **Enforce Authorization Checks on Static Resources** | Confidential data room payloads, evidence vault documentation, and administrative UI dashboards require valid session credentials and role-specific Bearer tokens. |
| **8** | **Verify Authorization Checks in Right Location** | Authorization enforcement is anchored strictly server-side in FastAPI route dependencies (`extract_current_user_payload`), independent of client-side browser controls. |
| **9** | **Exit Safely when Authorization Checks Fail** | Sanitised exception handling returning structured HTTP error payloads without exposing internal stack traces, environment variables, or database secrets. |
| **10** | **Implement Appropriate Logging** | Security and audit logging of authentication events, authorization failures, and password reset attempts without logging raw passwords, secret keys, or JWT tokens. |
| **11** | **Create Unit & Integration Test Cases** | Comprehensive automated test suite (`tests/test_rbac_and_resilience_scenarios.py`) validating login flows, token forging attempts, privilege escalation blocks, and SQL superuser protection rules. |

---

## 🔒 Deep Dive: Core Authorization Controls

### 1. Superuser SQL-Only Password Reset Restriction
To prevent web application compromise from escalating to total superuser takeover, the system enforces a strict security restriction in `src/dca_service/web_app.py`:

```python
# Superuser protection mandate: Superuser password CAN ONLY be reset by direct SQL command
if target_acct["role"] == "superuser":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "SECURITY RESTRICTION: Superuser account password CANNOT be reset via API/web interface. "
            "Superuser password can ONLY be reset via direct PostgreSQL database SQL command."
        ),
    )
```

Attempts by any user (including logged-in admins or superusers) to reset the `superuser` account password via the `/api/users/{username}/reset-password` endpoint are rejected with HTTP 403 Forbidden.

### 2. Cryptographic Token & Claim Verification
JWT tokens are signed using HMAC-SHA256 with constant-time verification:

```python
# Constant-time signature comparison preventing timing attacks
if not hmac.compare_digest(sig_b64, expected_sig):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Authorisation failed. Invalid or forged token signature.",
    )
```

Required claims validation verifies issuer (`https://auth.rcf-dac.univ.edu.my`), audience (`rcf-dac-data-room`), expiration timestamp, and role permissions on every protected request.

---

## 🧪 Verification & Security Testing

Automated verification of authorization logic is conducted via `uv run pytest tests/test_rbac_and_resilience_scenarios.py`:
- `test_rbac_authentication_login_flow`: Validates user credential authentication and JWT generation.
- `test_superuser_password_reset_protection`: Confirms that API-based superuser password reset returns HTTP 403.
- `test_admin_user_management_crud_and_rbac`: Verifies administrative privileges to create and reset non-superuser accounts.
