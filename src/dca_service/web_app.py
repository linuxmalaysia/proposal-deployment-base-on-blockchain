"""
Digital Research Asset Custodian (DAC) & Research Commercialisation Fund (RCF)
FastAPI Web Application Adapter & Service Entry Point.

Governed by DSOM Protocol // OKF v0.2 Standard // Concentric Clean Architecture.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import secrets
import time
import uuid
from contextlib import asynccontextmanager
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator

# Root directory pathing
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DOCS_DIR = BASE_DIR / "docs"


def load_secrets_from_env_files() -> None:
    """Load environment variables from Render Secret Files or local .env if present."""
    secret_paths = [
        Path("/etc/secrets/.env"),
        BASE_DIR / ".env",
    ]
    for secret_path in secret_paths:
        if secret_path.exists() and secret_path.is_file():
            try:
                for line in secret_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val
            except Exception:
                pass


load_secrets_from_env_files()

# Helper to extract secret key from string or JSON-object format (e.g. for SUPABASE_SECRET_KEYS)
def parse_secret_key_env(val: str | None) -> str | None:
    """
    Extracts a usable secret key from a plain-text or JSON-formatted environment value.
    
    Parameters:
        val (str | None): The environment value containing a secret key or JSON object.
    
    Returns:
        str | None: The first non-empty string value from a JSON object, the stripped input value, or `None` when no value is provided.
    """
    if not val:
        return None
    val = val.strip()
    if val.startswith("{"):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                # Return first string value or default/active key
                for k, v in parsed.items():
                    if isinstance(v, str) and v:
                        return v
        except Exception:
            pass
    return val if val else None

# Mandatory JWT secret lookup (fails closed if neither INVESTOR_JWT_SECRET nor SUPABASE_SECRET_KEY / SUPABASE_SECRET_KEYS is set)
_jwt_secret_env = (
    os.environ.get("INVESTOR_JWT_SECRET")
    or parse_secret_key_env(os.environ.get("SUPABASE_SECRET_KEY"))
    or parse_secret_key_env(os.environ.get("SUPABASE_SECRET_KEYS"))
)
if not _jwt_secret_env:
    raise RuntimeError(
        "FATAL: Missing required environment variable 'INVESTOR_JWT_SECRET', 'SUPABASE_SECRET_KEY', or 'SUPABASE_SECRET_KEYS'"
    )
INVESTOR_JWT_SECRET = _jwt_secret_env.encode()

# Module-level expected claims constants
EXPECTED_ISSUER = "https://auth.rcf-dac.univ.edu.my"
EXPECTED_AUDIENCE = "rcf-dac-data-room"

# In-memory storage for demonstration / web service operation
USER_REGISTRY: dict[str, dict[str, Any]] = {}
ASSET_REGISTRY: dict[str, dict[str, Any]] = {}
ACCOUNT_REGISTRY: dict[str, dict[str, Any]] = {}
LAST_SCHEMA_AUTO_CHECK_RESULT: dict[str, Any] | None = None
SCHEMA_BACKGROUND_TASK: Any | None = None

# Password Hashing & Initial Accounts Setup
PASSWORD_SALT = os.environ.get("RBAC_PASSWORD_SALT", "rcf_dac_rbac_salt_default")


def hash_password(password: str, salt: str | None = None) -> str:
    """
    Create a salted scrypt hash for a password.
    
    Parameters:
    	password (str): The password to hash.
    	salt (str | None): An optional salt; a cryptographically random salt is generated when omitted.
    
    Returns:
    	str: A password hash in the format `scrypt$salt$hash`.
    """
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
    return f"scrypt${salt}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify a password against a stored scrypt or legacy SHA-256 hash.
    
    Parameters:
        password (str): The password to verify.
        stored_hash (str): The stored password hash.
    
    Returns:
        bool: `true` if the password matches the stored hash, `false` otherwise.
    """
    if stored_hash.startswith("scrypt$"):
        parts = stored_hash.split("$")
        if len(parts) != 3:
            return False
        salt = parts[1]
        expected_key = parts[2]
        key = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
        return hmac.compare_digest(key.hex(), expected_key)
    # Fallback legacy SHA-256 comparison for test compatibility
    legacy_hash = hashlib.sha256(f"{PASSWORD_SALT}:{password}".encode()).hexdigest()
    return hmac.compare_digest(stored_hash, legacy_hash)


def get_or_create_initial_password(role: str) -> str:
    """
    Retrieve the initial password configured for a role or generate one when none is configured.
    
    Parameters:
        role (str): Account role used to select the environment variable and generate fallback passwords.
    
    Returns:
        str: The configured password, a deterministic test password, or a randomly generated password.
    """
    env_var = f"{role.upper()}_INITIAL_PASSWORD"
    if os.environ.get(env_var):
        return os.environ[env_var]
    # Standard deterministic fallback for test reproducible runs or generate secure random string
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return f"InitPass_{role}_2026!"
    token = secrets.token_urlsafe(10)
    return f"Secured_{role}_{token}!"


# Initial System Account Definitions
INITIAL_ACCOUNT_SPECS = [
    {
        "username": "dca_sys_root",
        "role": "superuser",
        "name": "System Superuser (Sudo Auditor)",
        "dept": "Security & Governance",
        "email": "superuser@rcf-dac.univ.edu.my",
    },
    {
        "username": "dca_admin_mgr",
        "role": "admin",
        "name": "System Administrator",
        "dept": "IT Infrastructure",
        "email": "admin@rcf-dac.univ.edu.my",
    },
    {
        "username": "dca_auditor_01",
        "role": "auditor",
        "name": "Lead Compliance Auditor",
        "dept": "Risk & Compliance",
        "email": "auditor@rcf-dac.univ.edu.my",
    },
    {
        "username": "dca_operator_01",
        "role": "operator",
        "name": "DCA System Operator",
        "dept": "DCA Operations",
        "email": "operator@rcf-dac.univ.edu.my",
    },
    {
        "username": "dca_investor_01",
        "role": "investor",
        "name": "Accredited Venture Partner",
        "dept": "Investment Office",
        "email": "investor@rcf-dac.univ.edu.my",
    },
]


def seed_initial_accounts() -> None:
    """Create the initial system accounts with hashed passwords and role metadata."""
    print("========================================================================")
    print("🔑 GENERATED SYSTEM ACCOUNTS & INITIAL PASSWORDS (SESSION CONSOLE ONLY):")
    print("========================================================================")
    for acct in INITIAL_ACCOUNT_SPECS:
        u = acct["username"]
        r = acct["role"]
        p = get_or_create_initial_password(r)
        print(f"  • User: {u:<16} | Role: {r:<10} | Password: {p}")
        ACCOUNT_REGISTRY[u] = {
            "username": u,
            "password_hash": hash_password(p),
            "role": r,
            "name": acct["name"],
            "dept": acct["dept"],
            "email": acct["email"],
            "did": f"did:univ:acct-{hashlib.sha256(u.encode()).hexdigest()[:12]}",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "raw_initial_password": p,
        }
    print("========================================================================")


seed_initial_accounts()

# DB Status Diagnostic Cache Configuration & State
DB_STATUS_CACHE_TTL: float = float(os.environ.get("DB_STATUS_CACHE_TTL", "5.0"))
_DB_STATUS_CACHE: dict[str, Any] | None = None
_DB_STATUS_CACHE_TIMESTAMP: float = 0.0

RevenueType = Literal["royalties", "licensing", "equity", "dividend"]
ContentEncoding = Literal["base64", "raw", "text"]


# --- Helper Cryptographic Utilities ---

def base64url_encode(data: bytes) -> str:
    """Encode bytes to URL-safe Base64 without trailing '=' padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def base64url_decode(encoded_str: str) -> bytes:
    """Decode URL-safe Base64 string with optional missing padding restored."""
    padded = encoded_str + "=" * (-len(encoded_str) % 4)
    return base64.urlsafe_b64decode(padded.encode())


# --- Pydantic Request Models ---

class LoginRequest(BaseModel):
    username: str = Field(..., description="System account username")
    password: str = Field(..., description="User account password")


class CreateUserRequest(BaseModel):
    username: str = Field(..., description="Unique system username")
    password: str = Field(..., description="User account password")
    name: str = Field(..., description="Full Name and Title")
    role: str = Field(..., description="User role (admin, auditor, operator, investor, user)")
    dept: str = Field(..., description="Faculty or Centre of Excellence")
    email: EmailStr = Field(..., description="Institutional Email Address")


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., description="New account password")


class UserRegistrationRequest(BaseModel):
    name: str = Field(..., description="Full Name and Title")
    role: str = Field(..., description="Institutional Role")
    dept: str = Field(..., description="Faculty or Centre of Excellence")
    email: EmailStr = Field(..., description="Institutional Email Address")


class AssetRegistrationRequest(BaseModel):
    title: str = Field(..., description="Research Project or Prototype Title")
    trl: int = Field(..., ge=1, le=9, description="Technology Readiness Level (1-9)")
    abstract: str = Field(..., description="Scientific Abstract & Innovation Summary")
    file_name: str = Field(..., description="Evidentiary File Reference Name")
    file_content: str | None = Field(None, description="Raw file payload or base64 representation")
    content_encoding: ContentEncoding | None = Field(
        None, description="Explicit content encoding: base64, raw, or text"
    )


class CloverleafScoreRequest(BaseModel):
    tech: int = Field(48, ge=0, le=60, description="Technology Strengths Score (Max 60)")
    market: int = Field(65, ge=0, le=80, description="Market Attractiveness Score (Max 80)")
    comm: int = Field(46, ge=0, le=60, description="Commercialisation Avenues Score (Max 60)")
    mgmt: int = Field(44, ge=0, le=60, description="Management & Execution Score (Max 60)")


class RevenueSplitRequest(BaseModel):
    amount: Decimal = Field(
        Decimal("500000.00"),
        ge=Decimal("0.00"),
        description="Total Ingested Revenue (MYR)",
    )
    revenue_type: RevenueType = Field(
        "licensing",
        description="Type of revenue stream: royalties, licensing, equity, or dividend",
    )

    @field_validator("amount")
    @classmethod
    def validate_max_two_decimal_places(cls, v: Decimal) -> Decimal:
        """
        Validate that a monetary amount has no more than two decimal places.
        
        Parameters:
            v (Decimal): Monetary amount to validate.
        
        Returns:
            Decimal: The validated monetary amount.
        
        Raises:
            ValueError: If the amount has more than two decimal places.
        """
        exp = v.as_tuple().exponent
        if isinstance(exp, int) and exp < -2:
            raise ValueError("Monetary amount cannot have more than two decimal places.")
        return v


# --- API Endpoints ---

def _safe_auto_check_and_build_schema() -> dict[str, Any]:
    """Fail-safe wrapper ensuring no background thread exception escapes unhandled."""
    try:
        return auto_check_and_build_schema()
    except Exception as exc:
        global LAST_SCHEMA_AUTO_CHECK_RESULT
        res = {
            "success": False,
            "message": f"Fail-safe schema auto-check error: {exc}",
            "db_connected": False,
            "tables_created": [],
            "missing_tables": ["users", "assets", "cloverleaf_scores", "revenue_splits", "blockchain_transactions"],
        }
        LAST_SCHEMA_AUTO_CHECK_RESULT = res
        return res


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """
    FastAPI lifespan context manager ensuring non-blocking schema auto-checking and table building on startup.

    Args:
        app_instance (FastAPI): The active FastAPI web application instance.
    """
    global SCHEMA_BACKGROUND_TASK
    import asyncio
    try:
        SCHEMA_BACKGROUND_TASK = asyncio.create_task(asyncio.to_thread(_safe_auto_check_and_build_schema))
    except Exception:
        pass

    yield

    if SCHEMA_BACKGROUND_TASK is not None and not SCHEMA_BACKGROUND_TASK.done():
        try:
            await asyncio.wait_for(asyncio.shield(SCHEMA_BACKGROUND_TASK), timeout=5.0)
        except Exception:
            pass


# Initialise FastAPI web application instance with lifespan context
app = FastAPI(
    title="RCF & DAC Interactive Web Portal",
    description="Research Commercialisation Fund & Digital Asset Custodian Service API",
    version="0.1.0",
    lifespan=lifespan,
)

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for Render service monitoring."""
    return {"status": "ok", "service": "rcf-dac-web-app", "version": "0.1.0"}


def get_postgresql_connection():
    """
    Establish a PostgreSQL connection using configured credentials and SSL verification.

    Returns:
        connection (psycopg.Connection or None): The PostgreSQL connection on success, or `None` when the driver, configuration, certificate, or connection is unavailable.
        status (str): A success or error message describing the connection result.
    """
    try:
        import urllib.parse

        import psycopg
    except ImportError:
        return None, "psycopg driver not installed"

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pooler_host = os.environ.get("SUPABASE_POOLER_HOST") or os.environ.get("SUPABASE_DB_HOST")
        supabase_url = os.environ.get("SUPABASE_URL", "")
        db_pass = os.environ.get("SUPABASE_DB_PASSWORD", "")
        if pooler_host and supabase_url and db_pass:
            # Extract project ref from URL hostname
            parsed = urllib.parse.urlparse(supabase_url)
            hostname = parsed.netloc or "your-supabase-project-ref.supabase.co"
            project_ref = hostname.split(".")[0]
            encoded_pass = urllib.parse.quote_plus(db_pass)
            ca_file = Path(os.environ.get("SUPABASE_SSLROOTCERT", "/etc/secrets/prod-supabase-ca.crt"))
            if ca_file.exists():
                ssl_params = f"sslmode=verify-full&sslrootcert={ca_file}"
            else:
                return None, "PostgreSQL CA certificate missing (/etc/secrets/prod-supabase-ca.crt); failing closed."
            database_url = f"postgresql://postgres.{project_ref}:{encoded_pass}@{pooler_host}:6543/postgres?{ssl_params}"

    if not database_url:
        return None, "DATABASE_URL or SUPABASE_DB_PASSWORD not configured"

    try:
        conn = psycopg.connect(database_url, connect_timeout=4)
        return conn, "Connected to PostgreSQL"
    except Exception as exc:
        return None, f"PostgreSQL connection error: {exc}"


def initialize_database_schema() -> dict[str, Any]:
    """
    Execute the database schema definition script against PostgreSQL.
    
    Returns:
        dict[str, Any]: A status dictionary containing `success` and a descriptive `message`.
    """
    schema_file = BASE_DIR / "docs" / "schema.sql"
    if not schema_file.exists():
        return {"success": False, "message": "docs/schema.sql file missing"}

    sql_script = schema_file.read_text(encoding="utf-8")
    conn, msg = get_postgresql_connection()
    if not conn:
        return {"success": False, "message": msg}

    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 10000; SET lock_timeout = 5000;")
            cur.execute(sql_script)
        conn.commit()
        conn.close()
        return {"success": True, "message": "Successfully executed DDL schema and created project tables in PostgreSQL database."}
    except Exception as exc:
        try:
            conn.rollback()
            conn.close()
        except Exception:
            pass
        return {"success": False, "message": f"Failed to execute schema DDL: {exc}"}


def auto_check_and_build_schema() -> dict[str, Any]:
    """
    Fail-safe automatic schema check and table build routine for application deployment on Render.com.

    Inspects PostgreSQL information_schema.tables for existing application schema tables, maintaining
    existing data, and automatically executing DDL schema statements if missing tables are detected.
    Retains schema check and initialisation results in module-level state for operator diagnostics.

    Returns:
        Dict[str, Any]: Execution status dictionary containing success boolean, message string,
        db_connected status boolean, tables_created list, and missing_tables list.
    """
    global LAST_SCHEMA_AUTO_CHECK_RESULT
    expected_tables = ["users", "assets", "cloverleaf_scores", "revenue_splits", "blockchain_transactions"]
    conn, msg = get_postgresql_connection()
    if not conn:
        res = {
            "success": False,
            "message": f"Auto schema check skipped: {msg}",
            "db_connected": False,
            "tables_created": [],
            "missing_tables": expected_tables,
        }
        LAST_SCHEMA_AUTO_CHECK_RESULT = res
        return res

    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = 10000; SET lock_timeout = 5000;")
            cur.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            )
            existing_tables = {r[0] for r in cur.fetchall()}

        missing_tables = [tbl for tbl in expected_tables if tbl not in existing_tables]
        conn.close()

        if not missing_tables:
            res = {
                "success": True,
                "message": "All required schema tables verified in PostgreSQL database.",
                "db_connected": True,
                "tables_created": [],
                "missing_tables": [],
            }
            LAST_SCHEMA_AUTO_CHECK_RESULT = res
            return res

        res_init = initialize_database_schema()
        if res_init.get("success"):
            res = {
                "success": True,
                "message": f"Successfully auto-built missing schema tables: {', '.join(missing_tables)}",
                "db_connected": True,
                "tables_created": missing_tables,
                "missing_tables": [],
            }
        else:
            res = {
                "success": False,
                "message": f"Auto-build failed for missing tables ({', '.join(missing_tables)}): {res_init.get('message')}",
                "db_connected": True,
                "tables_created": [],
                "missing_tables": missing_tables,
            }
        LAST_SCHEMA_AUTO_CHECK_RESULT = res
        return res
    except Exception as exc:
        try:
            conn.close()
        except Exception:
            pass
        res = {
            "success": False,
            "message": f"Fail-safe schema auto-check error: {exc}",
            "db_connected": True,
            "tables_created": [],
            "missing_tables": expected_tables,
        }
        LAST_SCHEMA_AUTO_CHECK_RESULT = res
        return res




def check_database_connection(bypass_cache: bool = False) -> dict[str, Any]:
    """
    Check PostgreSQL and Supabase connectivity and report the status of expected database tables.
    
    Parameters:
        bypass_cache (bool): Whether to force a fresh connectivity check instead of using a cached result.
    
    Returns:
        dict[str, Any]: Diagnostic information including connection status, latency, timestamp, and table verification details.
    """
    global _DB_STATUS_CACHE, _DB_STATUS_CACHE_TIMESTAMP
    now = time.time()

    if not bypass_cache and _DB_STATUS_CACHE is not None and (now - _DB_STATUS_CACHE_TIMESTAMP) < DB_STATUS_CACHE_TTL:
        cached = dict(_DB_STATUS_CACHE)
        cached["cached"] = True
        return cached

    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_jwks_url = os.environ.get(
        "SUPABASE_JWKS_URL",
        f"{supabase_url}/auth/v1/.well-known/jwks.json" if supabase_url else "",
    )

    start_time = time.time()
    db_connected = False
    http_connected = False
    details = []
    verified_db_tables = set()

    # 1. Read-only PostgreSQL database connection & table verification
    conn, pg_msg = get_postgresql_connection()
    query_succeeded = False
    if conn:
        db_connected = True
        details.append("PostgreSQL Database Connection Established")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
                )
                rows = cur.fetchall()
                verified_db_tables = {r[0] for r in rows}
                query_succeeded = True
            conn.close()
            details.append(f"Query verified {len(verified_db_tables)} tables in information_schema")
        except Exception as exc:
            details.append(f"PostgreSQL query error: {exc}")
            try:
                conn.close()
            except Exception:
                pass
    else:
        details.append(pg_msg)

    # 2. Test Supabase HTTP API connectivity separately
    if supabase_jwks_url:
        import urllib.request
        try:
            req = urllib.request.Request(
                supabase_jwks_url,
                headers={"User-Agent": "RCF-DAC-DB-Status-Check/1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:  # nosec B310
                if resp.status == 200:
                    http_connected = True
                    details.append("Supabase Auth API Operational")
        except Exception as exc:
            details.append(f"Supabase HTTP API Error: {exc}")

    latency_ms = round((time.time() - start_time) * 1000, 2)

    if db_connected:
        connection_status = "SUCCESSFULLY CONNECTED"
    elif http_connected:
        connection_status = "HTTP API OPERATIONAL (DB DISCONNECTED)"
    else:
        connection_status = "DISCONNECTED"

    table_names = ["users", "assets", "cloverleaf_scores", "revenue_splits", "blockchain_transactions"]
    table_descriptions = [
        "W3C DIDs and Institutional User Registrations",
        "Digital Research Assets & SHA-256 Vault Hash Storage",
        "Cloverleaf Market Readiness Assessment Scores",
        "IP Policy Commercialisation Distribution Allocations",
        "TimescaleDB Hypertables & Dual-Write Ledger",
    ]

    tables = []
    for tbl_name, desc in zip(table_names, table_descriptions):
        if tbl_name in verified_db_tables:
            tbl_status = "VERIFIED IN POSTGRESQL DB"
        elif db_connected and query_succeeded:
            tbl_status = "MISSING IN DATABASE"
        elif db_connected:
            tbl_status = "UNKNOWN (QUERY FAILED)"
        else:
            tbl_status = "VERIFIED DDL SCHEMA FILE"
        tables.append({"table_name": tbl_name, "description": desc, "status": tbl_status})

    res = {
        "status": connection_status,
        "is_connected": db_connected,
        "db_connected": db_connected,
        "http_api_connected": http_connected,
        "latency_ms": latency_ms,
        "status_detail": " | ".join(details),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "schema_tables": tables,
        "schema_file": "docs/schema.sql",
        "cached": False,
    }

    _DB_STATUS_CACHE = res
    _DB_STATUS_CACHE_TIMESTAMP = now
    return res


@app.get("/api/db-status")
def get_db_status_api(bypass_cache: bool = False, force: bool = False) -> dict[str, Any]:
    """
    Provide database connectivity, latency, and schema diagnostics.
    
    Parameters:
        bypass_cache (bool): Whether to perform a fresh database check.
        force (bool): Whether to perform a fresh database check.
    
    Returns:
        dict[str, Any]: Database connection and schema status details.
    """
    return check_database_connection(bypass_cache=bypass_cache or force)


# --- RBAC User Management & Authentication Endpoints ---

@app.post("/api/login")
def login_endpoint(req: LoginRequest) -> dict[str, Any]:
    """
    Authenticate system account credentials and create a signed session token.
    
    Returns:
        dict[str, Any]: Authentication status, bearer token, and authenticated user metadata.
    
    Raises:
        HTTPException: If the username is unknown or the password is invalid.
    """
    account = ACCOUNT_REGISTRY.get(req.username)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Invalid username or password.",
        )

    if not verify_password(req.password, account["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Invalid username or password.",
        )

    role = account["role"]
    token = create_system_jwt(username=account["username"], role=role)

    return {
        "message": "Authentication successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": account["username"],
            "role": account["role"],
            "name": account["name"],
            "dept": account["dept"],
            "email": account["email"],
            "did": account["did"],
        },
    }


@app.get("/login", response_class=HTMLResponse)
def serve_login_page() -> HTMLResponse:
    """
    Serve the interactive login page for system users.
    """
    html_content = """<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <title>System Login | RCF & DAC Platform</title>
  <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
  <div class="container" style="max-width: 500px; margin: 4rem auto; padding: 0 1rem;">
    <p style="margin-bottom: 1.5rem;"><a href="/">&larr; Return to RCF & DAC Homepage</a></p>

    <div style="text-align: center; margin-bottom: 2rem;">
      <h1>🔐 RCF & DAC System Login</h1>
      <p style="color: #666;">Enter your institutional credentials to access RBAC features</p>
    </div>

    <div id="alertBox" style="display: none; padding: 0.8rem 1rem; border-radius: 4px; margin-bottom: 1rem;"></div>

    <div class="card" style="background: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
      <form id="loginForm">
        <div style="margin-bottom: 1.2rem;">
          <label style="display: block; font-weight: bold; margin-bottom: 0.4rem;" for="username">Username:</label>
          <input type="text" id="username" name="username" required style="width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
        </div>

        <div style="margin-bottom: 1.5rem;">
          <label style="display: block; font-weight: bold; margin-bottom: 0.4rem;" for="password">Password:</label>
          <input type="password" id="password" name="password" required style="width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
        </div>

        <button type="submit" style="width: 100%; background: #0066cc; color: white; padding: 0.8rem; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">Sign In</button>
      </form>
    </div>
  </div>

  <script>
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const alertBox = document.getElementById('alertBox');
      alertBox.style.display = 'none';

      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value.trim();

      try {
        const resp = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const data = await resp.json();

        if (resp.ok) {
          localStorage.setItem('rcf_dac_jwt', data.access_token);
          localStorage.setItem('rcf_dac_user', JSON.stringify(data.user));
          alertBox.style.background = '#d4edda';
          alertBox.style.color = '#155724';
          alertBox.innerText = 'Login successful! Redirecting...';
          alertBox.style.display = 'block';

          setTimeout(() => {
            if (['admin', 'superuser'].includes(data.user.role)) {
              window.location.href = '/user-management';
            } else {
              window.location.href = '/';
            }
          }, 1000);
        } else {
          alertBox.style.background = '#f8d7da';
          alertBox.style.color = '#721c24';
          alertBox.innerText = data.detail || 'Login failed.';
          alertBox.style.display = 'block';
        }
      } catch (err) {
        alertBox.style.background = '#f8d7da';
        alertBox.style.color = '#721c24';
        alertBox.innerText = 'Network error during login.';
        alertBox.style.display = 'block';
      }
    });
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.get("/api/users")
def list_system_users(
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    """
    List registered system user accounts for authorized administrators.
    
    Parameters:
    	authorization (str | None): Bearer authorization header for an admin or superuser.
    
    Returns:
    	dict[str, Any]: User summaries, the total account count, and the requesting username.
    """
    payload = extract_current_user_payload(authorization)
    role = payload.get("role", "")
    if role not in ("admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Access restricted to Admin or Superuser roles.",
        )

    users_list = []
    for acct in ACCOUNT_REGISTRY.values():
        users_list.append({
            "username": acct["username"],
            "role": acct["role"],
            "name": acct["name"],
            "dept": acct["dept"],
            "email": acct["email"],
            "did": acct["did"],
            "created_at": acct.get("created_at"),
            "superuser_protected": acct["role"] == "superuser",
        })

    return {
        "users": users_list,
        "total": len(users_list),
        "requested_by": payload.get("sub"),
    }


@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def create_system_user(
    req: CreateUserRequest,
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    """
    Create a system user account for an authorized administrator.
    
    Parameters:
        req (CreateUserRequest): User details and credentials for the new account.
    
    Returns:
        dict[str, Any]: A success message and the created user's public account details.
    
    Raises:
        HTTPException: If authorization fails, a superuser account is requested, or the username already exists.
    """
    payload = extract_current_user_payload(authorization)
    caller_role = payload.get("role", "")

    if caller_role != "admin" and not (caller_role == "superuser" and payload.get("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Administrator role required to create user accounts.",
        )

    if req.role.lower() == "superuser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser accounts cannot be created via API. They require direct database SQL creation.",
        )

    if req.username in ACCOUNT_REGISTRY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User account '{req.username}' already exists.",
        )

    did_hash = hashlib.sha256(f"{req.username}-{time.time()}".encode()).hexdigest()[:12]
    new_user = {
        "username": req.username,
        "password_hash": hash_password(req.password),
        "role": req.role.lower(),
        "name": req.name,
        "dept": req.dept,
        "email": req.email,
        "did": f"did:univ:acct-{did_hash}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ACCOUNT_REGISTRY[req.username] = new_user

    return {
        "message": f"User account '{req.username}' successfully created.",
        "user": {
            "username": new_user["username"],
            "role": new_user["role"],
            "name": new_user["name"],
            "dept": new_user["dept"],
            "email": new_user["email"],
            "did": new_user["did"],
        },
    }


@app.post("/api/users/{username}/reset-password")
def reset_user_password(
    username: str,
    req: ResetPasswordRequest,
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    """
    Reset the password for an eligible user account.
    
    Parameters:
    	username (str): Username of the account whose password is reset.
    	req (ResetPasswordRequest): Request containing the new password.
    	authorization (str | None): Bearer authorization header for an administrator or superuser.
    
    Returns:
    	dict[str, Any]: Confirmation containing the username and identity of the administrator who performed the reset.
    """
    payload = extract_current_user_payload(authorization)
    caller_role = payload.get("role", "")

    if caller_role not in ("admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Administrator or Superuser role required for password reset.",
        )

    target_acct = ACCOUNT_REGISTRY.get(username)
    if not target_acct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account '{username}' not found.",
        )

    # Superuser protection mandate: Superuser password CAN ONLY be reset by direct SQL command
    if target_acct["role"] == "superuser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "SECURITY RESTRICTION: Superuser account password CANNOT be reset via API/web interface. "
                "Superuser password can ONLY be reset via direct PostgreSQL database SQL command."
            ),
        )

    target_acct["password_hash"] = hash_password(req.new_password)
    return {
        "message": f"Password for user '{username}' successfully reset.",
        "username": username,
        "reset_by": payload.get("sub"),
    }


@app.delete("/api/users/{username}")
def delete_system_user(
    username: str,
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    """
    Delete a user account authorized by an administrator.
    
    Parameters:
        username (str): Username of the account to delete.
        authorization (str | None): Bearer token identifying the requesting administrator.
    
    Returns:
        dict[str, Any]: Confirmation message and identifier of the administrator who performed the deletion.
    """
    payload = extract_current_user_payload(authorization)
    caller_role = payload.get("role", "")

    if caller_role != "admin" and not (caller_role == "superuser" and payload.get("admin")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Administrator role required to delete accounts.",
        )

    target_acct = ACCOUNT_REGISTRY.get(username)
    if not target_acct:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User account '{username}' not found.",
        )

    if target_acct["role"] == "superuser":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SECURITY RESTRICTION: Superuser account cannot be deleted via API.",
        )

    del ACCOUNT_REGISTRY[username]
    return {
        "message": f"User account '{username}' successfully deleted.",
        "deleted_by": payload.get("sub"),
    }


@app.get("/user-management", response_class=HTMLResponse)
def serve_user_management_page() -> HTMLResponse:
    """
    Serve the HTML interface for viewing and managing registered users.
    
    Returns:
    	HTMLResponse: The user management page with client-side authentication and account controls.
    """
    html_content = """<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <title>User Management Interface | RCF & DAC Platform</title>
  <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
  <div class="container" style="max-width: 1000px; margin: 2rem auto; padding: 0 1rem;">
    <p style="margin-bottom: 1.5rem;"><a href="/">&larr; Return to RCF & DAC Homepage</a></p>

    <div style="text-align: center; margin-bottom: 2rem;">
      <h1>👥 Institutional User Management Dashboard</h1>
      <p style="color: #666;">RBAC Controlled Account Administration & Governance Interface</p>
    </div>

    <div id="unauthAlert" style="display: none; background: #f8d7da; color: #721c24; padding: 1.5rem; border-radius: 6px; text-align: center; margin-bottom: 2rem;">
      <h3>⛔ Access Denied</h3>
      <p>This interface is restricted strictly to Administrator and Superuser roles.</p>
      <a href="/login" class="btn" style="background: #0066cc; color: white; padding: 0.6rem 1.2rem; border-radius: 4px; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 1rem;">Go to Login Page</a>
    </div>

    <div id="adminContent" style="display: none;">
      <div class="card" style="background: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h3>📋 System Registered Users</h3>
        <table style="width: 100%; border-collapse: collapse; margin-top: 1rem;">
          <thead>
            <tr style="border-bottom: 2px solid #dee2e6; text-align: left;">
              <th style="padding: 0.6rem;">Username</th>
              <th style="padding: 0.6rem;">Name</th>
              <th style="padding: 0.6rem;">Role</th>
              <th style="padding: 0.6rem;">Department</th>
              <th style="padding: 0.6rem;">W3C DID</th>
              <th style="padding: 0.6rem;">Actions</th>
            </tr>
          </thead>
          <tbody id="userTableBody">
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    async function loadUsers() {
      const token = localStorage.getItem('rcf_dac_jwt');
      const unauthAlert = document.getElementById('unauthAlert');
      const adminContent = document.getElementById('adminContent');

      if (!token) {
        unauthAlert.style.display = 'block';
        return;
      }

      try {
        const resp = await fetch('/api/users', {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!resp.ok) {
          unauthAlert.style.display = 'block';
          return;
        }

        const data = await resp.json();
        adminContent.style.display = 'block';

        const tbody = document.getElementById('userTableBody');
        tbody.innerHTML = '';

        data.users.forEach(u => {
          const tr = document.createElement('tr');
          tr.style.borderBottom = '1px solid #e9ecef';

          const tdUser = document.createElement('td');
          tdUser.style.padding = '0.6rem';
          const strongUser = document.createElement('strong');
          strongUser.textContent = u.username;
          tdUser.appendChild(strongUser);

          const tdName = document.createElement('td');
          tdName.style.padding = '0.6rem';
          tdName.textContent = u.name;

          const tdRole = document.createElement('td');
          tdRole.style.padding = '0.6rem';
          const spanRole = document.createElement('span');
          spanRole.style.background = '#e9ecef';
          spanRole.style.padding = '0.2rem 0.5rem';
          spanRole.style.borderRadius = '12px';
          spanRole.style.fontWeight = 'bold';
          spanRole.textContent = u.role;
          tdRole.appendChild(spanRole);

          const tdDept = document.createElement('td');
          tdDept.style.padding = '0.6rem';
          tdDept.textContent = u.dept;

          const tdDid = document.createElement('td');
          tdDid.style.padding = '0.6rem';
          const codeDid = document.createElement('code');
          codeDid.textContent = u.did;
          tdDid.appendChild(codeDid);

          const tdActions = document.createElement('td');
          tdActions.style.padding = '0.6rem';
          if (u.role === 'superuser') {
            const spanSuper = document.createElement('span');
            spanSuper.style.color = '#6c757d';
            spanSuper.style.fontSize = '0.85rem';
            spanSuper.style.fontStyle = 'italic';
            spanSuper.textContent = '🔒 SQL-Only Reset';
            tdActions.appendChild(spanSuper);
          } else {
            const btnReset = document.createElement('button');
            btnReset.style.background = '#dc3545';
            btnReset.style.color = 'white';
            btnReset.style.border = 'none';
            btnReset.style.padding = '0.3rem 0.6rem';
            btnReset.style.borderRadius = '4px';
            btnReset.style.cursor = 'pointer';
            btnReset.textContent = 'Reset Password';
            btnReset.addEventListener('click', () => promptReset(u.username));
            tdActions.appendChild(btnReset);
          }

          tr.appendChild(tdUser);
          tr.appendChild(tdName);
          tr.appendChild(tdRole);
          tr.appendChild(tdDept);
          tr.appendChild(tdDid);
          tr.appendChild(tdActions);
          tbody.appendChild(tr);
        });
      } catch (err) {
        unauthAlert.style.display = 'block';
      }
    }

    async function promptReset(username) {
      const newPassword = prompt(`Enter new password for ${username}:`);
      if (!newPassword) return;

      const token = localStorage.getItem('rcf_dac_jwt');
      try {
        const resp = await fetch(`/api/users/${username}/reset-password`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ new_password: newPassword })
        });
        const resData = await resp.json();
        if (resp.ok) {
          alert(`Password for ${username} reset successfully.`);
        } else {
          alert(`Error: ${resData.detail}`);
        }
      } catch (e) {
        alert('Failed to reset password.');
      }
    }

    document.addEventListener('DOMContentLoaded', loadUsers);
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.post("/api/init-db")
def init_db_endpoint(
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    """
    Initialize the database schema for an authorized administrator.
    
    Parameters:
    	authorization (str | None): Bearer token identifying an administrator.
    
    Returns:
    	dict[str, Any]: Database schema initialization status and diagnostic details.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing or invalid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    payload = verify_investor_bearer_token(token)

    if not payload.get("admin") and payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Administrator role required for schema initialisation.",
        )

    return initialize_database_schema()


@app.get("/db-status", response_class=HTMLResponse)
@app.get("/db-connection", response_class=HTMLResponse)
def serve_db_status_page(bypass_cache: bool = False, force: bool = False) -> HTMLResponse:
    """
    Render an HTML page showing database connectivity and schema verification results.
    
    Parameters:
        bypass_cache (bool): Whether to request fresh database diagnostics.
        force (bool): Whether to force a fresh diagnostic query.
    
    Returns:
        HTMLResponse: The rendered database status page.
    """
    db_info = check_database_connection(bypass_cache=bypass_cache or force)
    is_conn = db_info["is_connected"]

    status_badge = (
        '<span style="background: #28a745; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-weight: bold; font-size: 1.1rem;">🟢 SUCCESSFULLY CONNECTED</span>'
        if is_conn
        else '<span style="background: #dc3545; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-weight: bold; font-size: 1.1rem;">🔴 DISCONNECTED</span>'
    )

    tables_html = ""
    for tbl in db_info["schema_tables"]:
        tables_html += f"""<tr>
          <td style='padding:0.5rem;'><code>{tbl['table_name']}</code></td>
          <td style='padding:0.5rem;'>{tbl['description']}</td>
          <td style='padding:0.5rem;'><span style="color: #28a745; font-weight: bold;">✅ {tbl['status']}</span></td>
        </tr>"""

    cache_indicator = (
        '<span style="color: #6c757d; font-size: 0.9rem; margin-left: 0.5rem;">(⚡ Cached TTL response)</span>'
        if db_info.get("cached")
        else '<span style="color: #28a745; font-size: 0.9rem; margin-left: 0.5rem;">(🔄 Fresh query)</span>'
    )

    html_content = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <title>Database Connection & Schema Verification Status | RCF & DAC</title>
  <link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
  <div class="container" style="max-width: 900px; margin: 2rem auto; padding: 0 1rem;">
    <p style="margin-bottom: 1.5rem;"><a href="/">&larr; Return to RCF & DAC Interactive Portal Homepage</a></p>

    <div style="text-align: center; margin-bottom: 2rem;">
      <h1>🔌 Supabase & PostgreSQL Database Status</h1>
      <p style="font-size: 1.1rem; color: #555;">Real-Time Connection Diagnostic & Schema Table Verification</p>
      <div style="margin-top: 1rem;">
        {status_badge}
      </div>
    </div>

    <div class="card" style="background: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
      <h3 style="margin-top:0;">⚡ Network & Latency Diagnostic</h3>
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 0.5rem 0;"><strong>Connection Status:</strong></td>
          <td style="padding: 0.5rem 0;">{db_info['status']} ({db_info['status_detail']})</td>
        </tr>
        <tr>
          <td style="padding: 0.5rem 0;"><strong>Round-Trip Latency:</strong></td>
          <td style="padding: 0.5rem 0;"><strong>{db_info['latency_ms']} ms</strong> {cache_indicator}</td>
        </tr>
        <tr>
          <td style="padding: 0.5rem 0;"><strong>Checked Timestamp:</strong></td>
          <td style="padding: 0.5rem 0;">{db_info['timestamp']}</td>
        </tr>
      </table>
    </div>

    <div class="card" style="background: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
      <h3 style="margin-top:0;">🗄️ Project Database Tables & Schema Checklist</h3>
      <p style="margin-bottom: 1rem; color: #666;">Defined in DDL schema file: <code>{db_info['schema_file']}</code></p>
      <table style="width: 100%; border-collapse: collapse;">
        <thead>
          <tr style="border-bottom: 2px solid #dee2e6; text-align: left;">
            <th style="padding: 0.5rem;">Table Name</th>
            <th style="padding: 0.5rem;">Domain Purpose</th>
            <th style="padding: 0.5rem;">Schema Status</th>
          </tr>
        </thead>
        <tbody>
          {tables_html}
        </tbody>
      </table>
    </div>

    <div style="text-align: center; margin-top: 2rem; margin-bottom: 3rem;">
      <a href="/db-status?bypass_cache=true" class="btn" style="background: #0066cc; color: white; padding: 0.8rem 1.5rem; border-radius: 4px; text-decoration: none; font-weight: bold;">🔄 Re-test Database Connection</a>
      <a href="/api/db-status" target="_blank" class="btn" style="background: #6c757d; color: white; padding: 0.8rem 1.5rem; border-radius: 4px; text-decoration: none; font-weight: bold; margin-left: 1rem;">View JSON API Endpoint</a>
    </div>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.post("/api/register-user", status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegistrationRequest) -> dict[str, Any]:
    """
    Create a W3C-style decentralized identifier and register the institutional user in memory.
    
    Parameters:
    	req (UserRegistrationRequest): User registration details.
    
    Returns:
    	dict[str, Any]: Registration confirmation containing the user record and simulated database table name.
    """
    unique_nonce = uuid.uuid4()
    seed_str = f"{req.name}-{req.role}-{req.dept}-{time.time()}-{unique_nonce}"
    did_hash = hashlib.sha256(seed_str.encode()).hexdigest()[:16]
    did = f"did:univ:{did_hash}"

    record = {
        "name": req.name,
        "role": req.role,
        "dept": req.dept,
        "email": req.email,
        "did": did,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    USER_REGISTRY[did] = record
    return {
        "message": "User identity registered & W3C DID minted",
        "user": record,
        "simulated_db_table": "percona_postgresql_16.users",
    }


@app.post("/api/register-asset", status_code=status.HTTP_201_CREATED)
def register_asset(req: AssetRegistrationRequest) -> dict[str, Any]:
    """
    Register a research asset and record its evidence hash.
    
    Parameters:
        req (AssetRegistrationRequest): Asset metadata and optional file content to register.
    
    Returns:
        dict[str, Any]: Registration message, stored asset record, and queued outbox status.
    
    Raises:
        HTTPException: If Base64-encoded file content is invalid.
    """
    if req.file_content is not None:
        if req.content_encoding == "base64":
            try:
                file_bytes = base64.b64decode(req.file_content, validate=True)
            except Exception as err:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid Base64 file_content payload: {err}",
                )
        else:
            file_bytes = req.file_content.encode()
    else:
        fallback_str = req.file_name if req.file_name else req.title
        file_bytes = fallback_str.encode()

    sha256_digest = f"sha256:{hashlib.sha256(file_bytes).hexdigest()}"

    asset_seed = f"{req.title}-{req.abstract}-{req.trl}-{time.time()}-{uuid.uuid4()}"
    asset_id_hash = hashlib.sha256(asset_seed.encode()).hexdigest()[:12]
    asset_id = f"did:univ:asset-{asset_id_hash}"
    tx_outbox_id = f"outbox_tx_{int(time.time() * 1000) % 1000000}"

    asset_record = {
        "asset_id": asset_id,
        "title": req.title,
        "trl": req.trl,
        "abstract": req.abstract,
        "file_name": req.file_name,
        "sha256_digest": sha256_digest,
        "tx_outbox_id": tx_outbox_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ASSET_REGISTRY[asset_id] = asset_record
    return {
        "message": "Digital Research Asset registered in evidence vault",
        "asset": asset_record,
        "outbox_status": "QUEUED_PERCONA_TIMESCALEDB_OUTBOX",
    }


@app.post("/api/calculate-cloverleaf")
def calculate_cloverleaf(req: CloverleafScoreRequest) -> dict[str, Any]:
    """
    Calculate the Cloverleaf Market Readiness Score and funding classification.
    
    Parameters:
    	req (CloverleafScoreRequest): Component scores for technology, market, commercialisation, and management.
    
    Returns:
    	dict[str, Any]: Score breakdown, total and maximum scores, investment-grade status, status label, and recommended funding tier.
    """
    total_score = req.tech + req.market + req.comm + req.mgmt
    max_score = 260
    is_qualified = total_score > 180

    if is_qualified:
        funding_tier = "Tier 1 PoC Kickstarter Grant (RM 50,000 - RM 250,000)"
        status_label = "INVESTMENT-READY (Score > 180)"
    else:
        funding_tier = "Requires laboratory TRL escalation & market sizing refinement"
        status_label = f"DEVELOPMENT REQUIRED (Score {total_score} <= 180 Target)"

    return {
        "breakdown": {
            "tech_strengths": {"score": req.tech, "max": 60, "min_target": 42},
            "market_attractiveness": {"score": req.market, "max": 80, "min_target": 55},
            "commercialisation_avenues": {"score": req.comm, "max": 60, "min_target": 42},
            "management_execution": {"score": req.mgmt, "max": 60, "min_target": 41},
        },
        "total_score": total_score,
        "max_score": max_score,
        "is_investment_grade": is_qualified,
        "status_label": status_label,
        "rcf_funding_tier": funding_tier,
    }


@app.post("/api/calculate-revenue")
def calculate_revenue(req: RevenueSplitRequest) -> dict[str, Any]:
    """
    Calculate the revenue distribution across institutional stakeholders.
    
    Parameters:
    	req (RevenueSplitRequest): Revenue amount and supported revenue type to distribute.
    
    Returns:
    	dict[str, Any]: Revenue type, total amount in MYR and minor units, and stakeholder allocation details.
    
    Raises:
    	HTTPException: If the revenue type is unsupported.
    """
    amount = max(Decimal("0.00"), req.amount)
    rev_type = req.revenue_type.lower()

    if rev_type == "royalties":
        percentages = [Decimal("0.333"), Decimal("0.333"), Decimal("0.334"), Decimal("0.000")]
    elif rev_type == "equity":
        percentages = [Decimal("0.35"), Decimal("0.10"), Decimal("0.25"), Decimal("0.30")]
    elif rev_type == "dividend":
        percentages = [Decimal("0.25"), Decimal("0.15"), Decimal("0.30"), Decimal("0.30")]
    elif rev_type == "licensing":
        percentages = [Decimal("0.30"), Decimal("0.20"), Decimal("0.30"), Decimal("0.20")]
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported revenue type: {req.revenue_type}",
        )

    stakeholders = [
        ("🏛️ Central University Treasury", percentages[0]),
        ("🔬 Originating Dept / Lab", percentages[1]),
        ("👩‍🔬 Lead Inventors & Team", percentages[2]),
        ("🚀 RCF Re-investment Fund", percentages[3]),
    ]

    allocations = []
    total_allocated = Decimal("0.00")

    for name, pct in stakeholders:
        alloc = (amount * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        allocations.append(alloc)
        total_allocated += alloc

    remainder = amount - total_allocated
    if remainder != Decimal("0.00"):
        target_idx = 3 if percentages[3] > Decimal(0) else 0
        allocations[target_idx] += remainder

    splits = [
        {
            "stakeholder": name,
            "percentage": str((pct * Decimal(100)).quantize(Decimal("0.1"))),
            "amount_myr": str(alloc.quantize(Decimal("0.01"))),
            "amount_minor_units": int(alloc * 100),
        }
        for (name, pct), alloc in zip(stakeholders, allocations)
    ]

    return {
        "revenue_type": rev_type,
        "total_ingested_myr": str(amount.quantize(Decimal("0.01"))),
        "total_ingested_minor_units": int(amount * 100),
        "distribution_splits": splits,
    }


def create_system_jwt(
    username: str,
    role: str,
    exp_delta: float = 3600.0,
    secret: bytes = INVESTOR_JWT_SECRET,
) -> str:
    """
    Create a signed JWT for system user session authentication.
    
    Parameters:
        username (str): Username to include in the token.
        role (str): User role used to derive authorization claims.
        exp_delta (float): Number of seconds until the token expires.
        secret (bytes): HMAC signing secret.
    
    Returns:
        str: Signed JWT containing the user's identity, role, authorization claims, and expiration.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "username": username,
        "role": role,
        "admin": role in ("admin", "superuser"),
        "accredited_investor": role in ("investor", "admin", "superuser"),
        "iss": EXPECTED_ISSUER,
        "aud": EXPECTED_AUDIENCE,
        "exp": int(time.time() + exp_delta),
    }
    header_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    sig_b64 = base64url_encode(hmac.new(secret, signing_input, hashlib.sha256).digest())
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_investor_bearer_token(
    token: str, secret: bytes = INVESTOR_JWT_SECRET
) -> dict[str, Any]:
    """
    Validate an investor JWT and return its claims.
    
    Parameters:
        token (str): JWT presented as the investor bearer token.
        secret (bytes): HMAC-SHA256 key used to verify the token signature.
    
    Returns:
        dict[str, Any]: The validated JWT claims.
    
    Raises:
        HTTPException: If the token is malformed, has an invalid signature or claims, is expired, or does not identify an accredited investor.
    """
    if not token or not isinstance(token, str):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Invalid or missing token string.",
        )

    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Token is opaque or malformed non-JWT structure.",
        )

    header_b64, payload_b64, sig_b64 = parts

    # Verify HMAC-SHA256 signature
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = base64url_encode(hmac.new(secret, signing_input, hashlib.sha256).digest())

    if not hmac.compare_digest(sig_b64, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Invalid or forged token signature.",
        )

    # Decode and parse payload claims
    try:
        payload_bytes = base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Unparseable or malformed JWT payload.",
        ) from None

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. JWT payload must be a JSON object.",
        )

    # Validate required claims
    if "exp" not in payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing required 'exp' expiration claim.",
        )

    exp_val = payload["exp"]
    if not isinstance(exp_val, (int, float)) or isinstance(exp_val, bool) or not math.isfinite(exp_val):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. 'exp' claim must be a finite numeric value.",
        )

    if exp_val < time.time():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Token has expired.",
        )

    if payload.get("iss") != EXPECTED_ISSUER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing or untrusted token issuer ('iss').",
        )

    if payload.get("aud") != EXPECTED_AUDIENCE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing or invalid token audience ('aud').",
        )

    if not payload.get("accredited_investor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing required 'accredited_investor' claim.",
        )

    return payload


def extract_current_user_payload(authorization: str | None) -> dict[str, Any]:
    """
    Extract and verify the authenticated user's payload from a Bearer authorization header.
    
    Parameters:
        authorization (str | None): The HTTP Authorization header containing a Bearer token.
    
    Returns:
        dict[str, Any]: The verified user payload.
    
    Raises:
        HTTPException: If the header is missing, malformed, or contains an invalid token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing or invalid Bearer token header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split("Bearer ", 1)[1].strip()
    return verify_investor_bearer_token(token)


@app.get("/api/investor-assets")
def get_investor_assets(
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict[str, Any]:
    """
    Retrieve NDA-gated data room listings and registered assets for an authorized accredited investor.
    
    Parameters:
    	authorization (str | None): Bearer token from the Authorization header.
    
    Returns:
    	A dictionary containing data-room listings, user-registered assets, and the access level.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing or invalid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    payload = verify_investor_bearer_token(token)
    if payload.get("role") and payload.get("role") not in ("investor", "admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Accredited investor role required.",
        )

    default_listings = [
        {
            "asset_id": "did:univ:asset-9f82a1",
            "title": "Graphene Solid State Battery Cell",
            "trl": 3,
            "cloverleaf_score": 203,
            "max_score": 260,
            "funding_tier": "Tier 1 PoC Grant (RM 150,000)",
            "status": "Cleared for Fund",
        },
        {
            "asset_id": "did:univ:asset-4b12c8",
            "title": "AI Diagnostic Bio-Chip Array",
            "trl": 5,
            "cloverleaf_score": 218,
            "max_score": 260,
            "funding_tier": "Tier 2 Co-Investment VC (RM 2.5M)",
            "status": "Cleared for Fund",
        },
    ]
    registered = list(ASSET_REGISTRY.values())
    return {
        "data_room_assets": default_listings,
        "user_registered_assets": registered,
        "access_level": "Accredited VC / Corporate Partner NDA Gated",
    }


def render_markdown_to_html(md_text: str) -> str:
    """Simple parser to convert index.md markdown elements to clean HTML."""
    import re

    # Strip Liquid tags like {::options ... /}
    md_text = re.sub(r"\{::options.*?\/\}", "", md_text)

    # Convert horizontal rules
    md_text = re.sub(r"^---$", "<hr>", md_text, flags=re.MULTILINE)

    # Convert headers (###, ##, #)
    md_text = re.sub(r"^### (.*)$", r"<h3>\1</h3>", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"^## (.*)$", r"<h2>\1</h2>", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"^# (.*)$", r"<h1>\1</h1>", md_text, flags=re.MULTILINE)

    # Convert bold text **text**
    md_text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", md_text)

    # Convert markdown links [text](url)
    md_text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', md_text)

    # Convert bullet lists - text
    lines = md_text.splitlines()
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item_text = stripped[2:]
            html_lines.append(f"  <li>{item_text}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(line)

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


@app.get("/docs/{file_path:path}", response_class=HTMLResponse)
def serve_docs(file_path: str) -> HTMLResponse:
    """Serve documentation Markdown files rendered as HTML."""
    target_path = file_path
    if target_path.endswith(".html"):
        target_path = target_path[:-5] + ".md"
    elif not target_path.endswith(".md"):
        target_path = target_path + ".md"

    doc_file = (DOCS_DIR / target_path).resolve()

    # Prevent path traversal outside of DOCS_DIR
    try:
        doc_file.relative_to(DOCS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation page not found")

    if not doc_file.exists() or not doc_file.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation page not found")

    content = doc_file.read_text(encoding="utf-8")
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]

    rendered_html = render_markdown_to_html(content)

    html_wrapper = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <title>RCF & DAC Documentation</title>
  <link rel="stylesheet" href="/assets/css/style.css">
  <script src="/assets/js/rcf-dac-app.js" defer></script>
</head>
<body>
  <div class="container">
    <p style="margin-bottom: 1.5rem;"><a href="/">&larr; Return to RCF & DAC Interactive Portal Homepage</a></p>
    {rendered_html}
  </div>
</body>
</html>"""
    return HTMLResponse(content=html_wrapper)


@app.get("/", response_class=HTMLResponse)
def serve_index() -> HTMLResponse:
    """Serve interactive web application HTML homepage."""
    index_file = BASE_DIR / "index.md"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]

        rendered_html = render_markdown_to_html(content)

        html_wrapper = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <title>RCF & DAC Interactive Web Portal</title>
  <link rel="stylesheet" href="/assets/css/style.css">
  <script src="/assets/js/rcf-dac-app.js" defer></script>
</head>
<body>
  <div class="container">
    {rendered_html}
  </div>
</body>
</html>"""
        return HTMLResponse(content=html_wrapper)
    return HTMLResponse("<h1>RCF & DAC Web Application Service Online</h1>")
