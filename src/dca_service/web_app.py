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

from fastapi import Cookie, FastAPI, Header, HTTPException, Request, Response, status
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

# Module Access Control Mapping
DEFAULT_MODULE_PERMISSIONS: dict[str, list[str]] = {
    "module_1": ["admin"],       # User Registration & W3C DID Minting (Admin ONLY)
    "module_2": ["operator"],    # Research Asset Registration & Cryptographic Evidence Vault
    "module_3": ["operator"],    # Commercialisation Assessment: Cloverleaf Scoring Engine
    "module_4": ["investor"],    # Investor Dashboard & RCF Capital Deployment Matchmaker
    "module_5": ["investor"],    # Impact Measurement Platform: Revenue Distribution Calculator
}
ROLE_MODULE_PERMISSIONS: dict[str, list[str]] = {k: list(v) for k, v in DEFAULT_MODULE_PERMISSIONS.items()}

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
    Hash password using hashlib.scrypt KDF with per-account salt.
    Returns format 'scrypt$salt$hash'.
    """
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1)
    return f"scrypt${salt}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against scrypt or legacy hash format."""
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
    """Get password from environment or generate a secure random password."""
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
    """Initialise and populate initial system user accounts with hashed passwords."""
    for acct in INITIAL_ACCOUNT_SPECS:
        u = acct["username"]
        r = acct["role"]
        p = get_or_create_initial_password(r)
        ACCOUNT_REGISTRY[u] = {
            "username": u,
            "password_hash": hash_password(p),
            "role": r,
            "name": acct["name"],
            "dept": acct["dept"],
            "email": acct["email"],
            "did": f"did:univ:acct-{hashlib.sha256(u.encode()).hexdigest()[:12]}",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


seed_initial_accounts()

# DB Status Diagnostic & High-Throughput Cache Configuration & State
DB_STATUS_CACHE_TTL: float = float(os.environ.get("DB_STATUS_CACHE_TTL", "5.0"))
_DB_STATUS_CACHE: dict[str, Any] | None = None
_DB_STATUS_CACHE_TIMESTAMP: float = 0.0

INVESTOR_ASSETS_CACHE_TTL: float = float(os.environ.get("INVESTOR_ASSETS_CACHE_TTL", "5.0"))
_INVESTOR_ASSETS_CACHE: dict[str, Any] | None = None
_INVESTOR_ASSETS_CACHE_TIMESTAMP: float = 0.0


class ConnectionPoolMetrics:
    """Tracks database connection pooling stats, latency, and utilization metrics."""

    def __init__(self) -> None:
        self.total_acquired: int = 0
        self.active_connections: int = 0
        self.max_pool_size: int = int(os.environ.get("DB_POOL_MAX_SIZE", "20"))
        self.min_pool_size: int = int(os.environ.get("DB_POOL_MIN_SIZE", "5"))
        self.total_checkout_latency_ms: float = 0.0
        self.total_queries: int = 0
        self.failed_connections: int = 0

    def record_connection_attempt(self, latency_ms: float, success: bool) -> None:
        if success:
            self.total_acquired += 1
            self.total_checkout_latency_ms += latency_ms
        else:
            self.failed_connections += 1

    def record_query(self) -> None:
        self.total_queries += 1

    def to_dict(self) -> dict[str, Any]:
        avg_latency = (
            round(self.total_checkout_latency_ms / self.total_acquired, 2)
            if self.total_acquired > 0
            else 0.0
        )
        return {
            "max_pool_size": self.max_pool_size,
            "min_pool_size": self.min_pool_size,
            "total_connections_acquired": self.total_acquired,
            "failed_connection_attempts": self.failed_connections,
            "avg_checkout_latency_ms": avg_latency,
            "total_queries_executed": self.total_queries,
            "pool_utilization_percent": round(
                (self.active_connections / self.max_pool_size) * 100, 1
            ) if self.max_pool_size > 0 else 0.0,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


DB_POOL_METRICS = ConnectionPoolMetrics()
ASYNC_DB_POOL: Any = None


async def init_async_connection_pool() -> Any:
    """
    Initialize and open the asynchronous PostgreSQL connection pool when database configuration is available.
    
    Returns:
        Any: The opened connection pool, or `None` when configuration is unavailable or initialization fails.
    """
    global ASYNC_DB_POOL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        pooler_host = os.environ.get("SUPABASE_POOLER_HOST") or os.environ.get("SUPABASE_DB_HOST")
        supabase_url = os.environ.get("SUPABASE_URL", "")
        db_pass = os.environ.get("SUPABASE_DB_PASSWORD", "")
        if pooler_host and supabase_url and db_pass:
            import urllib.parse
            project_ref = supabase_url.replace("https://", "").replace("http://", "").split(".")[0]
            db_user = f"postgres.{project_ref}" if "." not in pooler_host else "postgres"
            encoded_pass = urllib.parse.quote_plus(db_pass)
            database_url = f"postgresql://{db_user}:{encoded_pass}@{pooler_host}:5432/postgres?sslmode=require"

    if database_url:
        try:
            from psycopg_pool import AsyncConnectionPool
            pool = AsyncConnectionPool(
                conninfo=database_url,
                min_size=1,
                max_size=DB_POOL_METRICS.max_pool_size,
                open=False,
            )
            await pool.open()
            ASYNC_DB_POOL = pool
            return pool
        except Exception:
            ASYNC_DB_POOL = None
            return None
    return None


async def close_async_connection_pool() -> None:
    """Close async connection pool gracefully."""
    global ASYNC_DB_POOL
    if ASYNC_DB_POOL is not None:
        try:
            await ASYNC_DB_POOL.close()
        except Exception:
            pass
        finally:
            ASYNC_DB_POOL = None


def close_postgresql_connection(conn: Any) -> None:
    """Close PostgreSQL connection and decrement active connection pool accounting."""
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        finally:
            if DB_POOL_METRICS.active_connections > 0:
                DB_POOL_METRICS.active_connections -= 1

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


class RoleAssignmentUpdateRequest(BaseModel):
    module_permissions: dict[str, list[str]] = Field(
        ...,
        description="Dictionary mapping module IDs (module_1 to module_5) to lists of allowed roles.",
    )


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
async def lifespan(app_instance: FastAPI) -> Any:
    """
    FastAPI lifespan context manager ensuring non-blocking schema auto-checking,
    table building, and AsyncConnectionPool lifecycle management on startup and shutdown.

    Args:
        app_instance (FastAPI): The active FastAPI web application instance.
    """
    global SCHEMA_BACKGROUND_TASK
    import asyncio
    try:
        await init_async_connection_pool()
    except Exception:
        pass

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

    try:
        await close_async_connection_pool()
    except Exception:
        pass


# --- Rate Limiting Storage & Middleware ---

RATE_LIMIT_BUCKETS: dict[str, list[float]] = {}


def is_rate_limited(client_ip: str, max_requests: int = 10, window_seconds: float = 60.0) -> bool:
    """
    Determine whether a client has exceeded the request limit within a rolling time window.
    
    Parameters:
        client_ip (str): Client identifier used to track request timestamps.
        max_requests (int): Maximum number of requests allowed in the window.
        window_seconds (float): Duration of the rolling window in seconds.
    
    Returns:
        bool: `true` if the client has reached the request limit, `false` otherwise.
    """
    now = time.time()
    timestamps = RATE_LIMIT_BUCKETS.get(client_ip, [])
    # Retain only timestamps within the rolling window
    timestamps = [t for t in timestamps if now - t < window_seconds]
    if len(timestamps) >= max_requests:
        RATE_LIMIT_BUCKETS[client_ip] = timestamps
        return True
    timestamps.append(now)
    RATE_LIMIT_BUCKETS[client_ip] = timestamps
    return False


# Initialise FastAPI web application instance with lifespan context
app = FastAPI(
    title="RCF & DAC Interactive Web Portal",
    description="Research Commercialisation Fund & Digital Asset Custodian Service API",
    version="0.1.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Any) -> Any:
    """
    Apply request-rate limits to authentication and user-management endpoints.
    
    Returns:
        Response from the downstream handler, or an HTTP 429 response when the client exceeds 10 requests within 60 seconds.
    """
    rate_limited_paths = ["/api/login", "/api/users"]
    if any(request.url.path.startswith(p) for p in rate_limited_paths):
        client_ip = request.client.host if request.client else "127.0.0.1"
        if is_rate_limited(f"{client_ip}:{request.url.path}", max_requests=10, window_seconds=60.0):
            return Response(
                content=json.dumps({"detail": "Too many requests. Rate limit exceeded. Please try again later."}),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
            )
    return await call_next(request)

if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for Render service monitoring."""
    return {"status": "ok", "service": "rcf-dac-web-app", "version": "0.1.0"}


def get_postgresql_connection() -> tuple[Any, str]:
    """
    Establish a PostgreSQL connection using the configured database settings.
    
    Returns:
        tuple[Any, str]: The connection and a status message. The connection is
        `None` when the driver, configuration, certificate, or connection is
        unavailable.
    """
    try:
        import urllib.parse

        import psycopg
    except ImportError:
        DB_POOL_METRICS.record_connection_attempt(0.0, False)
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
                DB_POOL_METRICS.record_connection_attempt(0.0, False)
                return None, "PostgreSQL CA certificate missing (/etc/secrets/prod-supabase-ca.crt); failing closed."
            database_url = f"postgresql://postgres.{project_ref}:{encoded_pass}@{pooler_host}:6543/postgres?{ssl_params}"

    if not database_url:
        DB_POOL_METRICS.record_connection_attempt(0.0, False)
        return None, "DATABASE_URL or SUPABASE_DB_PASSWORD not configured"

    t0 = time.time()
    try:
        conn = psycopg.connect(database_url, connect_timeout=4)
        lat_ms = (time.time() - t0) * 1000.0
        DB_POOL_METRICS.record_connection_attempt(lat_ms, True)
        DB_POOL_METRICS.active_connections += 1
        return conn, "Connected to PostgreSQL"
    except Exception as exc:
        lat_ms = (time.time() - t0) * 1000.0
        DB_POOL_METRICS.record_connection_attempt(lat_ms, False)
        return None, f"PostgreSQL connection error: {exc}"


def initialize_database_schema() -> dict[str, Any]:
    """
    Execute docs/schema.sql DDL script against PostgreSQL database to create schema and tables.

    Returns:
        Dict[str, Any]: Execution status dictionary containing success boolean and descriptive message.
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
        close_postgresql_connection(conn)
        return {"success": True, "message": "Successfully executed DDL schema and created project tables in PostgreSQL database."}
    except Exception as exc:
        try:
            conn.rollback()
            close_postgresql_connection(conn)
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
        close_postgresql_connection(conn)

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
    Check PostgreSQL connectivity, verify expected public tables, and test the Supabase authentication API.
    Uses in-memory TTL caching to minimize database round-trips under high-concurrency polling unless bypassed.
    
    Args:
        bypass_cache (bool): If True, forces a fresh database check bypassing cached result.

    Returns:
        Dict[str, Any]: Diagnostic status including connection results, latency, timestamp, and table verification details.
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
                DB_POOL_METRICS.record_query()
                cur.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
                )
                rows = cur.fetchall()
                verified_db_tables = {r[0] for r in rows}
                query_succeeded = True
            details.append(f"Query verified {len(verified_db_tables)} tables in information_schema")
        except Exception as exc:
            details.append(f"PostgreSQL query error: {exc}")
        finally:
            close_postgresql_connection(conn)
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
        "pool_metrics": DB_POOL_METRICS.to_dict(),
        "cached": False,
    }

    _DB_STATUS_CACHE = res
    _DB_STATUS_CACHE_TIMESTAMP = now
    return res


@app.get("/api/db-status")
def get_db_status_api(bypass_cache: bool = False, force: bool = False) -> dict[str, Any]:
    """Return database connection status, network latency, and schema verification in JSON."""
    return check_database_connection(bypass_cache=bypass_cache or force)


@app.get("/api/db-pool-metrics")
def get_db_pool_metrics_endpoint() -> dict[str, Any]:
    """Return PostgreSQL / Supabase connection pool health and performance metrics."""
    return {
        "status": "healthy",
        "pool_metrics": DB_POOL_METRICS.to_dict(),
        "service": "rcf-dac-web-app",
    }


# --- CSRF & Origin Protection Helper ---

def verify_csrf_and_origin(
    request: Request,
    x_csrf_token: str | None = Header(None, alias="X-CSRF-Token"),
) -> None:
    """Verify Origin header and non-cookie CSRF token header for cookie-authenticated mutation endpoints."""
    if "rcf_dac_jwt" in request.cookies:
        expected_origin = os.environ.get("ALLOWED_ORIGIN", "").rstrip("/")
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if origin and expected_origin:
            if not origin.rstrip("/").startswith(expected_origin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF/Origin validation failed. Untrusted request origin.",
                )
        if not x_csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed. Missing required X-CSRF-Token header.",
            )


# --- RBAC User Management & Authentication Endpoints ---

@app.post("/api/login")
def login_endpoint(req: LoginRequest, response: Response) -> dict[str, Any]:
    """Authenticate system account credentials, set HttpOnly session cookie, and return signed JWT session token."""
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

    # Set HttpOnly, SameSite, Secure session cookie (defaults to True; opt-out via COOKIE_SECURE=false)
    secure_cookie = os.environ.get("COOKIE_SECURE", "true").lower() != "false"
    response.set_cookie(
        key="rcf_dac_jwt",
        value=token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=3600,
        path="/",
    )

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


@app.post("/api/logout")
def logout_endpoint(
    request: Request,
    response: Response,
    x_csrf_token: str | None = Header(None, alias="X-CSRF-Token"),
) -> dict[str, str]:
    """Clear HttpOnly session cookie to revoke browser session context."""
    verify_csrf_and_origin(request, x_csrf_token)
    response.delete_cookie(key="rcf_dac_jwt", path="/")
    return {"message": "Successfully logged out. Session cookie cleared."}


@app.get("/login", response_class=HTMLResponse)
def serve_login_page() -> HTMLResponse:
    """Serve interactive user login HTML page."""
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
          credentials: 'same-origin',
          body: JSON.stringify({ username, password })
        });
        const data = await resp.json();

        if (resp.ok) {
          localStorage.setItem('rcf_dac_user', JSON.stringify(data.user));
          alertBox.style.background = '#d4edda';
          alertBox.style.color = '#155724';
          alertBox.innerText = 'Login successful! HttpOnly session established. Redirecting...';
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




@app.get("/user-management", response_class=HTMLResponse)
def serve_user_management_page() -> HTMLResponse:
    """
    Render the interactive user-management dashboard.
    
    The dashboard supports authenticated user listing, account creation, password resets, logout, and administrator-controlled DID registration.
    
    Returns:
    	HTMLResponse: The rendered user-management dashboard.
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
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
      <p style="margin: 0;"><a href="/">&larr; Return to RCF & DAC Homepage</a></p>
      <button id="logoutBtn" style="background: #6c757d; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; font-weight: bold;">Sign Out</button>
    </div>

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
      <!-- MODULE 1: User Identity & W3C DID Registration (Admin ONLY) -->
      <div id="module1Card" class="card" style="background: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: none;">
        <h3 style="color: #0066cc; margin-top: 0;">1. User Registration & W3C Decentralised Identifier (DID) Minting <span style="background: #0066cc; color: white; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; vertical-align: middle;">ADMIN ONLY</span></h3>
        <p style="color: #495057;">Every researcher, principal investigator, and administrative officer receives a permanent W3C DID stored in PostgreSQL 16.</p>

        <form id="user-reg-form">
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
            <div>
              <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="reg-fullname">Full Name & Title</label>
              <input type="text" id="reg-fullname" value="Prof. Dr. Harisfazillah Jamel" placeholder="e.g. Dr. Jane Doe" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
            </div>
            <div>
              <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="reg-role">Institutional Role</label>
              <select id="reg-role" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
                <option value="Lead Principal Investigator (PI)">Lead Principal Investigator (PI)</option>
                <option value="Chancellor's Research Chair">Chancellor's Research Chair</option>
                <option value="Technology Transfer Officer (TTO)">Technology Transfer Officer (TTO)</option>
                <option value="Deputy Vice-Chancellor (Research)">Deputy Vice-Chancellor (Research)</option>
                <option value="Accredited VC Partner">Accredited VC Partner</option>
              </select>
            </div>
            <div>
              <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="reg-dept">Faculty / CoE</label>
              <input type="text" id="reg-dept" value="Centre of Excellence in DeepTech & Nanotechnology" placeholder="e.g. Faculty of Engineering" style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
            </div>
            <div>
              <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="reg-email">Institutional Email</label>
              <input type="email" id="reg-email" value="harisfazillah@university.edu.my" placeholder="email@univ.edu.my" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
            </div>
          </div>
          <button type="submit" style="background: #0066cc; color: white; padding: 0.6rem 1.2rem; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">Mint Identity & Register User</button>
        </form>

        <div id="user-reg-output" style="display:none; margin-top: 1.5rem;"></div>
      </div>

      <div id="module1SuperNotice" class="card" style="background: #fff3cd; border: 1px solid #ffeba2; border-left: 4px solid #ffc107; border-radius: 8px; padding: 1.2rem; margin-bottom: 2rem; display: none;">
        <h4 style="margin-top: 0; color: #856404;">🔒 Module 1 (User Registration & DID Minting) Notice</h4>
        <p style="margin: 0; color: #856404;">Module 1 is restricted strictly to <strong>Admin</strong> role. Superuser account can manage user listings and create admin accounts below, but cannot mint DIDs or access operational modules.</p>
      </div>

      <div class="card" style="background: #ffffff; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h3 id="createUserTitle">➕ Create New System User</h3>
        <p id="createUserRoleNotice" style="color: #6c757d; font-size: 0.9rem; margin-bottom: 1rem;"></p>
        <div id="createUserAlert" style="display: none; padding: 0.8rem; border-radius: 4px; margin-bottom: 1rem;"></div>
        <form id="createUserForm" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div>
            <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="newUsername">Username:</label>
            <input type="text" id="newUsername" name="username" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
          </div>
          <div>
            <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="newPassword">Password:</label>
            <input type="password" id="newPassword" name="password" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
          </div>
          <div>
            <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="newName">Full Name:</label>
            <input type="text" id="newName" name="name" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
          </div>
          <div>
            <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="newRole">Role:</label>
            <select id="newRole" name="role" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
            </select>
          </div>
          <div>
            <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="newDept">Department:</label>
            <input type="text" id="newDept" name="dept" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
          </div>
          <div>
            <label style="display: block; font-weight: bold; margin-bottom: 0.2rem;" for="newEmail">Email:</label>
            <input type="email" id="newEmail" name="email" required style="width: 100%; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box;">
          </div>
          <div style="grid-column: span 2;">
            <button type="submit" id="createUserBtn" style="background: #28a745; color: white; padding: 0.6rem 1.2rem; border: none; border-radius: 4px; font-weight: bold; cursor: pointer;">Create User Account</button>
          </div>
        </form>
      </div>

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
    function simpleHash(str) {
      let hash = 0;
      for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash |= 0;
      }
      return Math.abs(hash).toString(16).padStart(8, '0') + Math.abs(hash * 31).toString(16).padStart(8, '0');
    }

    function escapeHtml(text) {
      const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
      return text.replace(/[&<>"']/g, m => map[m]);
    }

    function initRegistrationForm() {
      const form = document.getElementById('user-reg-form');
      if (!form) return;

      form.addEventListener('submit', (e) => {
        e.preventDefault();

        const name = document.getElementById('reg-fullname').value.trim() || 'Dr. Aris Roslan';
        const role = document.getElementById('reg-role').value;
        const dept = document.getElementById('reg-dept').value.trim() || 'Faculty of Engineering & Innovation';
        const email = document.getElementById('reg-email').value.trim() || 'aris@university.edu.my';

        const hashSeed = `${name}-${role}-${dept}-${Date.now()}`;
        const did = `did:univ:${simpleHash(hashSeed).substring(0, 16)}`;

        const userRecord = { name, role, dept, email, did, timestamp: new Date().toISOString() };
        let savedSuccessfully = false;

        try {
          localStorage.setItem('rcf_dac_user_registration', JSON.stringify(userRecord));
          savedSuccessfully = true;
        } catch (err) {
          console.warn('LocalStorage unavailable:', err);
          savedSuccessfully = false;
        }

        renderRegistrationResult(userRecord, savedSuccessfully);
      });
    }

    function renderRegistrationResult(userRecord, savedSuccessfully = true) {
      const outputBox = document.getElementById('user-reg-output');
      if (outputBox) {
        if (savedSuccessfully) {
          outputBox.innerHTML = `
            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #16a34a; border-radius: 6px; padding: 1.25rem;">
              <h4 style="margin-top: 0; color: #15803d; font-size: 1.1rem;">✅ Identity Registered & W3C DID Minted</h4>
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem; margin-bottom: 0.75rem;">
                <p style="margin: 0;"><strong>Name:</strong> ${escapeHtml(userRecord.name)}</p>
                <p style="margin: 0;"><strong>Institutional Role:</strong> ${escapeHtml(userRecord.role)}</p>
                <p style="margin: 0;"><strong>Faculty / Centre:</strong> ${escapeHtml(userRecord.dept)}</p>
                <p style="margin: 0;"><strong>Email:</strong> ${escapeHtml(userRecord.email)}</p>
              </div>
              <div style="background: #1e293b; color: #e2e8f0; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 0.75rem;">
                <span style="display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.25rem;">W3C Decentralised Identifier (DID):</span>
                <code style="background: #0f172a; color: #38bdf8; padding: 0.25rem 0.5rem; border-radius: 4px; font-family: monospace; font-size: 1rem;">${escapeHtml(userRecord.did)}</code>
              </div>
              <div style="font-size: 0.8rem; color: #64748b;">
                <span>BROWSER STORAGE PERSISTENCE: Simulated PostgreSQL 16 <code style="background: #e2e8f0; padding: 0.1rem 0.3rem; border-radius: 3px;">users</code> table record (Persisted locally)</span>
              </div>
            </div>
          `;
        } else {
          outputBox.innerHTML = `
            <div style="background: #fffbeb; border: 1px solid #fde68a; border-left: 4px solid #d97706; border-radius: 6px; padding: 1.25rem;">
              <h4 style="margin-top: 0; color: #b45309; font-size: 1.1rem;">⚠️ Identity Generated (Persistence Unavailable)</h4>
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem; margin-bottom: 0.75rem;">
                <p style="margin: 0;"><strong>Name:</strong> ${escapeHtml(userRecord.name)}</p>
                <p style="margin: 0;"><strong>Institutional Role:</strong> ${escapeHtml(userRecord.role)}</p>
                <p style="margin: 0;"><strong>Faculty / Centre:</strong> ${escapeHtml(userRecord.dept)}</p>
                <p style="margin: 0;"><strong>Email:</strong> ${escapeHtml(userRecord.email)}</p>
              </div>
              <div style="background: #1e293b; color: #e2e8f0; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 0.75rem;">
                <span style="display: block; font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.25rem;">W3C Decentralised Identifier (DID):</span>
                <code style="background: #0f172a; color: #38bdf8; padding: 0.25rem 0.5rem; border-radius: 4px; font-family: monospace; font-size: 1rem;">${escapeHtml(userRecord.did)}</code>
              </div>
              <div style="font-size: 0.8rem; color: #64748b;">
                <span>BROWSER STORAGE PERSISTENCE: Local storage write failed or unavailable; record not persisted.</span>
              </div>
            </div>
          `;
        }
        outputBox.style.display = 'block';
      }
    }

    function loadSavedRegistration() {
      try {
        const saved = localStorage.getItem('rcf_dac_user_registration');
        if (saved) {
          const userRecord = JSON.parse(saved);
          renderRegistrationResult(userRecord, true);
        }
      } catch (err) {
        console.warn('Could not load saved user registration:', err);
      }
    }

    async function loadUsers() {
      const token = localStorage.getItem('rcf_dac_jwt');
      const unauthAlert = document.getElementById('unauthAlert');
      const adminContent = document.getElementById('adminContent');
      const userObjStr = localStorage.getItem('rcf_dac_user');
      let currentUser = userObjStr ? JSON.parse(userObjStr) : null;

      try {
        const resp = await fetch('/api/users', {
          credentials: 'same-origin',
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        if (!resp.ok) {
          unauthAlert.style.display = 'block';
          adminContent.style.display = 'none';
          return;
        }

        const data = await resp.json();
        adminContent.style.display = 'block';
        unauthAlert.style.display = 'none';

        const module1Card = document.getElementById('module1Card');
        const module1SuperNotice = document.getElementById('module1SuperNotice');
        const newRoleSelect = document.getElementById('newRole');
        const createUserRoleNotice = document.getElementById('createUserRoleNotice');

        const userRole = currentUser ? currentUser.role : 'admin';

        if (userRole === 'admin') {
          if (module1Card) module1Card.style.display = 'block';
          if (module1SuperNotice) module1SuperNotice.style.display = 'none';
          if (createUserRoleNotice) createUserRoleNotice.innerText = 'As Admin, you can create user accounts for any operational role (operator, auditor, investor) or additional Admin accounts, but NOT Superuser.';
          if (newRoleSelect) {
            newRoleSelect.innerHTML = `
              <option value="operator">operator</option>
              <option value="admin">admin</option>
              <option value="auditor">auditor</option>
              <option value="investor">investor</option>
            `;
          }
        } else if (userRole === 'superuser') {
          if (module1Card) module1Card.style.display = 'none';
          if (module1SuperNotice) module1SuperNotice.style.display = 'block';
          if (createUserRoleNotice) createUserRoleNotice.innerText = 'SECURITY RESTRICTION: As Superuser, you can ONLY create user accounts with "admin" role. Superuser cannot create any other role.';
          if (newRoleSelect) {
            newRoleSelect.innerHTML = `<option value="admin">admin</option>`;
          }
        }

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
        adminContent.style.display = 'none';
      }
    }

    async function promptReset(username) {
      const newPassword = prompt(`Enter new password for ${username}:`);
      if (!newPassword) return;

      const token = localStorage.getItem('rcf_dac_jwt');
      try {
        const resp = await fetch(`/api/users/${username}/reset-password`, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
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

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', async () => {
        try {
          await fetch('/api/logout', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'X-CSRF-Token': 'csrf_session_valid' }
          });
        } catch (e) {}
        localStorage.removeItem('rcf_dac_user');
        window.location.href = '/login';
      });
    }

    const createUserForm = document.getElementById('createUserForm');
    if (createUserForm) {
      createUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const alertBox = document.getElementById('createUserAlert');
        alertBox.style.display = 'none';

        const username = document.getElementById('newUsername').value.trim();
        const password = document.getElementById('newPassword').value.trim();
        const name = document.getElementById('newName').value.trim();
        const role = document.getElementById('newRole').value;
        const dept = document.getElementById('newDept').value.trim();
        const email = document.getElementById('newEmail').value.trim();

        try {
          const resp = await fetch('/api/users', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRF-Token': 'csrf_session_valid'
            },
            body: JSON.stringify({ username, password, name, role, dept, email })
          });
          const resData = await resp.json();
          if (resp.ok) {
            alertBox.style.background = '#d4edda';
            alertBox.style.color = '#155724';
            alertBox.innerText = `User account '${username}' created successfully!`;
            alertBox.style.display = 'block';
            createUserForm.reset();
            loadUsers();
          } else {
            alertBox.style.background = '#f8d7da';
            alertBox.style.color = '#721c24';
            alertBox.innerText = resData.detail || 'Failed to create user.';
            alertBox.style.display = 'block';
          }
        } catch (err) {
          alertBox.style.background = '#f8d7da';
          alertBox.style.color = '#721c24';
          alertBox.innerText = 'Network error during user creation.';
          alertBox.style.display = 'block';
        }
      });
    }

    document.addEventListener('DOMContentLoaded', () => {
      loadUsers();
      initRegistrationForm();
      loadSavedRegistration();
    });
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)




@app.get("/db-status", response_class=HTMLResponse)
@app.get("/db-connection", response_class=HTMLResponse)
def serve_db_status_page(bypass_cache: bool = False, force: bool = False) -> HTMLResponse:
    """
    Serve the interactive database connection and schema status page.

    Returns:
        HTMLResponse: HTML containing current connection diagnostics and schema table statuses.
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
def register_user(
    req: UserRegistrationRequest,
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Mint a decentralized identifier and register an institutional user.
    
    Parameters:
        req (UserRegistrationRequest): User details and assigned role.
    
    Returns:
        dict[str, Any]: Registration message, user record, and simulated database table name.
    
    Raises:
        HTTPException: If the authenticated user does not have the admin role.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    role = payload.get("role", "")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. User registration and W3C DID minting is restricted strictly to Administrator role.",
        )

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
def register_asset(
    req: AssetRegistrationRequest,
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Register a research asset and record its evidence hash.
    
    Parameters:
    	req (AssetRegistrationRequest): Asset metadata and optional file content.
    
    Returns:
    	dict[str, Any]: Registration message, asset record, and queued outbox status.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    check_module_access("module_2", payload, is_mutation=True)

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
    global _INVESTOR_ASSETS_CACHE
    _INVESTOR_ASSETS_CACHE = None  # Invalidate high-throughput cache
    return {
        "message": "Digital Research Asset registered in evidence vault",
        "asset": asset_record,
        "outbox_status": "QUEUED_PERCONA_TIMESCALEDB_OUTBOX",
    }


@app.post("/api/calculate-cloverleaf")
def calculate_cloverleaf(
    req: CloverleafScoreRequest,
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Calculate an asset's Cloverleaf Market Readiness Score and funding classification.
    
    Parameters:
        req (CloverleafScoreRequest): Component scores for technology, market, commercialisation, and management.
    
    Returns:
        dict[str, Any]: Score breakdown, total and maximum scores, investment-grade status, status label, and recommended RCF funding tier.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    check_module_access("module_3", payload, is_mutation=True)

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
def calculate_revenue(
    req: RevenueSplitRequest,
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Calculate the revenue distribution across institutional stakeholders.
    
    Parameters:
    	req (RevenueSplitRequest): Revenue type and amount to distribute.
    
    Returns:
    	dict[str, Any]: A revenue distribution containing the normalized revenue type, total amount in MYR and minor units, and stakeholder allocations with percentages and amounts.
    
    Raises:
    	HTTPException: If the revenue type is unsupported.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    check_module_access("module_5", payload, is_mutation=True)

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
    """Generate a signed HMAC-SHA256 JWT for system user session authentication."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "username": username,
        "role": role,
        "admin": role in ("admin", "superuser"),
        "accredited_investor": role == "investor",
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
    Validate a system Bearer token and return its claims.
    
    Parameters:
        token (str): JWT to authenticate.
        secret (bytes): HMAC-SHA256 secret used to verify the token signature.
    
    Returns:
        dict[str, Any]: Verified JWT claims.
    
    Raises:
        HTTPException: If the token is malformed, has an invalid signature or claims, is expired, or lacks the required investor or system-role authorization.
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

    # If role is system role, allow token verification without accredited_investor claim
    user_role = payload.get("role", "")
    if not payload.get("accredited_investor") and not payload.get("admin") and user_role not in ("admin", "superuser", "operator", "auditor", "investor", "user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Missing required 'accredited_investor' claim.",
        )

    return payload


def check_module_access(
    module_id: str,
    payload: dict[str, Any],
    is_mutation: bool = False,
) -> None:
    """
    Enforce role-based access to a module.
    
    Parameters:
        module_id (str): Identifier of the module to access.
        payload (dict[str, Any]): Authenticated user claims used to determine the user's role.
        is_mutation (bool): Whether the requested operation modifies data.
    
    Raises:
        HTTPException: If the user's role cannot access the module or an auditor attempts a mutation.
    """
    role = payload.get("role", "").lower()
    if not role:
        if payload.get("admin"):
            role = "admin"
        elif payload.get("accredited_investor"):
            role = "investor"

    if role in ("admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorisation failed. Admin and Superuser roles cannot access operational module '{module_id}'. Please log in with a role-specific account.",
        )

    if role == "auditor":
        if is_mutation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Authorisation failed. Auditor role has read-only access to module '{module_id}' and cannot perform mutate actions.",
            )
        return

    allowed_roles = ROLE_MODULE_PERMISSIONS.get(module_id, [])
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorisation failed. Role '{role}' is not assigned to access module '{module_id}'.",
        )


def extract_current_user_payload(
    authorization: str | None = None,
    rcf_dac_jwt: str | None = None,
    request: Request | None = None,
) -> dict[str, Any]:
    """
    Extract and verify the authenticated user's JWT payload.
    
    Parameters:
        authorization (str | None): Optional Authorization header containing a Bearer token.
        rcf_dac_jwt (str | None): Optional JWT session cookie value.
        request (Request | None): Optional request used to read the session cookie.
    
    Returns:
        dict[str, Any]: The verified JWT payload.
    
    Raises:
        HTTPException: If no authentication token is provided.
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
    elif rcf_dac_jwt:
        token = rcf_dac_jwt
    elif request and "rcf_dac_jwt" in request.cookies:
        token = request.cookies["rcf_dac_jwt"]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing or invalid Bearer token or session cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_investor_bearer_token(token)


@app.get("/api/users")
def list_system_users(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    List registered system user accounts for authorized administrators.
    
    Returns:
    	dict[str, Any]: A response containing user records, the total user count, and the requesting user.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
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


@app.get("/api/role-assignments")
def get_role_assignments(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Retrieve the module-to-role access mappings for an administrator.
    
    Returns:
    	dict[str, Any]: A mapping of module permissions and the identifier of the requesting user.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    role = payload.get("role", "")
    if role not in ("admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Access restricted to Admin or Superuser roles.",
        )
    return {
        "module_permissions": ROLE_MODULE_PERMISSIONS,
        "requested_by": payload.get("sub"),
    }


@app.post("/api/role-assignments")
def update_role_assignments(
    req: RoleAssignmentUpdateRequest,
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
    x_csrf_token: str | None = Header(None, alias="X-CSRF-Token"),
) -> dict[str, Any]:
    """
    Update role-to-module access permissions for authorized administrators.
    
    Module 1 remains restricted to administrators regardless of the submitted
    permissions.
    
    Parameters:
        req (RoleAssignmentUpdateRequest): Module permission mappings to apply.
    
    Returns:
        dict[str, Any]: A success message, the updated module permissions, and the
        identifier of the administrator who made the change.
    
    Raises:
        HTTPException: If the requester is not an administrator or a submitted
        module identifier is invalid.
    """
    verify_csrf_and_origin(request, x_csrf_token)
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    role = payload.get("role", "")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Administrator role required to update role-to-module assignments.",
        )

    for mod_id, roles_list in req.module_permissions.items():
        if mod_id not in ROLE_MODULE_PERMISSIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid module ID '{mod_id}'. Allowed modules: module_1, module_2, module_3, module_4, module_5.",
            )
        # Ensure module_1 is ALWAYS restricted to admin
        if mod_id == "module_1":
            ROLE_MODULE_PERMISSIONS["module_1"] = ["admin"]
        else:
            cleaned_roles = [r.lower().strip() for r in roles_list if isinstance(r, str)]
            ROLE_MODULE_PERMISSIONS[mod_id] = cleaned_roles

    return {
        "message": "Role-to-module assignment mappings updated successfully.",
        "module_permissions": ROLE_MODULE_PERMISSIONS,
        "updated_by": payload.get("sub"),
    }


@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def create_system_user(
    req: CreateUserRequest,
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Create a system user account according to the caller's role.
    
    Admins may create accounts for any role except `superuser`. Superusers may create only `admin` accounts. Newly created accounts receive a generated institutional DID.
    
    Parameters:
        req (CreateUserRequest): Account details, including username, password, role, and profile information.
    
    Returns:
        dict[str, Any]: A success message and the created user's public account details.
    
    Raises:
        HTTPException: If the caller lacks permission, the username already exists, or the requested role is not permitted.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    caller_role = payload.get("role", "").lower()
    target_role = req.role.lower().strip()

    if caller_role not in ("admin", "superuser"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Administrator or Superuser role required to create user accounts.",
        )

    if caller_role == "admin":
        if target_role == "superuser":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorisation failed. Admin cannot create superuser accounts. Superuser accounts require direct database SQL creation.",
            )
    elif caller_role == "superuser":
        if target_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Authorisation failed. Superuser can ONLY create accounts with 'admin' role, not any other role.",
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
        "role": target_role,
        "name": req.name,
        "dept": req.dept,
        "email": req.email,
        "did": f"did:univ:acct-{did_hash}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    ACCOUNT_REGISTRY[req.username] = new_user

    return {
        "message": f"User account '{req.username}' successfully created with role '{target_role}'.",
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
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """
    Reset password for specified user account.
    Superuser password CANNOT be reset via API; it requires direct database SQL command.
    """
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
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
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
) -> dict[str, Any]:
    """Delete specified user account (Admin only; cannot delete superuser)."""
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
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


@app.post("/api/init-db")
def init_db_endpoint(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
    x_csrf_token: str | None = Header(None, alias="X-CSRF-Token"),
) -> dict[str, Any]:
    """Execute docs/schema.sql DDL script to initialise database schema and tables (Admin only)."""
    verify_csrf_and_origin(request, x_csrf_token)
    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)

    if not payload.get("admin") and payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorisation failed. Administrator role required for schema initialisation.",
        )

    return initialize_database_schema()


@app.get("/api/investor-assets")
def get_investor_assets(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    rcf_dac_jwt: str | None = Cookie(None),
    bypass_cache: bool = False,
) -> dict[str, Any]:
    """
    Retrieve NDA-gated asset listings and registered assets for an authorized investor.
    
    Parameters:
    	request (Request): The incoming HTTP request used for authentication checks.
    	bypass_cache (bool): Whether to bypass the TTL cache and retrieve current data.
    
    Returns:
    	dict[str, Any]: Data room listings, user-registered assets, access-level information, and cache status.
    """
    global _INVESTOR_ASSETS_CACHE, _INVESTOR_ASSETS_CACHE_TIMESTAMP

    payload = extract_current_user_payload(authorization, rcf_dac_jwt, request)
    check_module_access("module_4", payload, is_mutation=False)

    now = time.time()
    if not bypass_cache and _INVESTOR_ASSETS_CACHE is not None and (now - _INVESTOR_ASSETS_CACHE_TIMESTAMP) < INVESTOR_ASSETS_CACHE_TTL:
        cached_res = dict(_INVESTOR_ASSETS_CACHE)
        cached_res["cached"] = True
        return cached_res

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
    res = {
        "data_room_assets": default_listings,
        "user_registered_assets": registered,
        "access_level": "Accredited VC / Corporate Partner NDA Gated",
        "cached": False,
    }
    _INVESTOR_ASSETS_CACHE = res
    _INVESTOR_ASSETS_CACHE_TIMESTAMP = now
    return res


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
