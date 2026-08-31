---
okf_version: "0.2"
type: "how-to"
title: "How to Reset Superuser Password via Environment Configuration & Create Initial Admin Users"
timestamp: "2026-08-31T00:00:00Z"
topics:
  - "superuser"
  - "password-reset"
  - "admin-user"
  - "postgresql"
  - "sql"
  - "rbac"
description: "Step-by-step guide explaining how to re-seed the system superuser password via environment configuration and create the first administrator account."
resource: "file:///docs/how-to/reset-superuser-password-and-manage-users.md"
sources:
  - "src/dca_service/web_app.py"
  - "docs/explanation/owasp-authorization-framework.md"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-31T00:00:00Z"
language: "en-GB"
---

# 🔑 How to Reset Superuser Password via Environment Configuration & Create Initial Admin Users

This guide provides step-by-step procedures for platform operators and system administrators to reset the `dca_sys_root` superuser password and create initial administrator accounts (`dca_admin_mgr` or custom admin users).

---

## 🔒 Security Policy: Direct Environment Mandate for Superuser Reset

In compliance with the **OWASP Authorization Framework** and platform security policies:

> **RESTRICTION:** The system superuser account (`dca_sys_root`) password **CANNOT** be reset via public API endpoints or web interfaces. API password reset calls targeting `dca_sys_root` are blocked with **HTTP 403 Forbidden**.
>
> **REASON:** Restricting superuser credential modification to direct environment configuration or backend seeding prevents web application compromises from escalating to full superuser account takeover.

---

## 🛠️ Step 1: Reset the Superuser Password via Supported Environment Re-Seeding

Operators reset the superuser password using the supported environment configuration flow:

### Environment Variable Startup Seeding (Supported Reset Mechanism)

1. Access your Render.com Web Service Dashboard (or local `/etc/secrets/.env` file).

2. Add or update the environment variable `SUPERUSER_INITIAL_PASSWORD`:

   ```bash
   SUPERUSER_INITIAL_PASSWORD="YourSecureSuperuserPassword2026!"
   ```

3. Restart or redeploy the Web Service. During system startup, `get_or_create_initial_password("superuser")` and `seed_initial_accounts()` populate `ACCOUNT_REGISTRY` for `dca_sys_root` with the `scrypt` password hash derived from `SUPERUSER_INITIAL_PASSWORD`.

4. When PostgreSQL database persistence is active, the superuser record is also synchronized during initialization:

   ```sql
   -- Verification query for superuser record in PostgreSQL database
   SELECT username, role, email FROM users WHERE username = 'dca_sys_root' AND role = 'superuser';
   ```

---

## 🔐 Step 2: Log In as Superuser (`dca_sys_root`)

1. Open the web browser and navigate to the System Login page:
   `https://<your-render-app-url>/login` (or `http://localhost:8000/login`).
2. Enter the superuser credentials:
   - **Username:** `dca_sys_root`
   - **Password:** `YourSecureSuperuserPassword2026!`
3. Click **Sign In**.
4. Upon successful authentication, an HMAC-SHA256-signed JWT bearer token is issued. For browser sessions, the token is passed in the `Authorization: Bearer <token>` header (or handled via protected session cookies in production environments), redirecting you to `/user-management`.

---

## 👥 Step 3: Create Initial Admin Users via UI or REST API

Once authenticated as `dca_sys_root` (or using an existing `admin` account), you can create and manage administrator users.

### Option 1: Using the Interactive User Management Interface (`/user-management`)

1. Navigate to `https://<your-render-app-url>/user-management`.
2. View the table of registered system accounts.
3. Use the administrative controls to create new accounts or reset passwords for non-superuser users (e.g. `dca_admin_mgr`).

---

### Option 2: Using the REST API (`POST /api/users`)

Send an HTTP POST request to the `/api/users` endpoint with your Bearer token in the `Authorization` header:

```bash
curl -X POST "https://<your-render-app-url>/api/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_superuser_jwt_token>" \
  -d '{
    "username": "dca_admin_mgr",
    "password": "AdminSecurePassword2026!",
    "name": "System Administrator",
    "role": "admin",
    "dept": "IT Infrastructure",
    "email": "admin@rcf-dac.univ.edu.my"
  }'
```

**Expected Response (HTTP 201 Created):**
```json
{
  "message": "User account 'dca_admin_mgr' successfully created.",
  "user": {
    "username": "dca_admin_mgr",
    "role": "admin",
    "name": "System Administrator",
    "dept": "IT Infrastructure",
    "email": "admin@rcf-dac.univ.edu.my",
    "did": "did:univ:acct-a1b2c3d4e5f6"
  }
}
```

---

## 📋 Summary of Institutional Roles & Capabilities

| Role | Default Username | Web Password Reset Allowed? | Administrative Privileges |
|------|------------------|-----------------------------|---------------------------|
| `superuser` | `dca_sys_root` | ❌ **No (API Blocked / Env Only)** | Sudo Auditor / Global Governance |
| `admin` | `dca_admin_mgr` | ✅ Yes (by Admin/Superuser) | Account Management & Schema Init |
| `auditor` | `dca_auditor_01` | ✅ Yes | Read-Only Audit & Compliance |
| `operator` | `dca_operator_01` | ✅ Yes | Asset Vault Operations |
| `investor` | `dca_investor_01` | ✅ Yes | NDA Data Room Access |

---

## 🧪 Testing User Account Administration

To run automated integration tests verifying login, password reset restrictions, and admin account creation:

```bash
uv run pytest tests/test_rbac_and_resilience_scenarios.py
```
