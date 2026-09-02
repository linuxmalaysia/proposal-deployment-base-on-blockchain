"""
Database API Access Layer for Digital Custody Asset Platform.

Provides centralized direct access to PostgreSQL database tables for all application
modules, adhering to OWASP REST Security guidelines, concentric clean architecture,
and microservices readiness.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("dca_service.database_api")

# Centralized memory registries for runtime caching and offline compatibility
ACCOUNT_REGISTRY: dict[str, dict[str, Any]] = {}
USER_REGISTRY: dict[str, dict[str, Any]] = {}
ASSET_REGISTRY: dict[str, dict[str, Any]] = {}
ROLE_MODULE_PERMISSIONS: dict[str, list[str]] = {}

_IN_MEMORY_CLOVERLEAF_SCORES: list[dict[str, Any]] = []
_IN_MEMORY_REVENUE_SPLITS: list[dict[str, Any]] = []


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
        """
        Record the outcome and latency of a connection acquisition attempt.
        
        Parameters:
            latency_ms (float): Connection acquisition latency in milliseconds.
            success (bool): Whether the connection acquisition succeeded.
        """
        if success:
            self.total_acquired += 1
            self.total_checkout_latency_ms += latency_ms
        else:
            self.failed_connections += 1

    def record_query(self) -> None:
        """Record one database query in the connection pool metrics."""
        self.total_queries += 1

    def to_dict(self) -> dict[str, Any]:
        """
        Return the current connection pool metrics as a dictionary.
        
        Returns:
        	dict[str, Any]: Metrics including pool limits, connection and query counts,
        	average checkout latency, utilization percentage, and a UTC timestamp.
        """
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


def get_postgresql_connection() -> tuple[Any, str]:
    """
    Establish a PostgreSQL connection using the configured database URL or Supabase settings.
    
    Returns:
        tuple[Any, str]: The connection and a status message. The connection is `None` when configuration is missing, the CA certificate is unavailable, the driver is not installed, or the connection fails.
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


def close_postgresql_connection(conn: Any) -> None:
    """Close PostgreSQL connection and update active connection metrics."""
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        finally:
            if DB_POOL_METRICS.active_connections > 0:
                DB_POOL_METRICS.active_connections -= 1


class DatabaseAPI:
    """Centralized Database Access Layer for managing direct access to PostgreSQL."""

    @staticmethod
    def get_connection() -> tuple[Any, str]:
        return get_postgresql_connection()

    # --- User Management API Methods ---

    @staticmethod
    def create_user(user_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create or update a user account in the registries and PostgreSQL.
        
        Parameters:
        	user_data (dict[str, Any]): User attributes, including username, credentials, role, profile details, and decentralized identifier.
        
        Returns:
        	dict[str, Any]: The normalized user record with default account-state fields applied.
        """
        username = user_data["username"]
        conn, _ = get_postgresql_connection()

        user_record = {
            "username": username,
            "password_hash": user_data["password_hash"],
            "role": user_data["role"],
            "name": user_data["name"],
            "dept": user_data["dept"],
            "email": user_data["email"],
            "did": user_data["did"],
            "is_active": user_data.get("is_active", True),
            "is_disabled": user_data.get("is_disabled", False),
            "can_login": user_data.get("can_login", True),
            "is_archived": user_data.get("is_archived", False),
            "archived_at": user_data.get("archived_at"),
            "tags": user_data.get("tags", ["active"]),
            "created_at": user_data.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        # Sync to central in-memory registries
        ACCOUNT_REGISTRY[username] = dict(user_record)
        USER_REGISTRY[user_record["did"]] = dict(user_record)

        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO users (
                            username, password_hash, role, name, dept, email, did,
                            is_active, is_disabled, can_login, is_archived, archived_at, tags, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (username) DO UPDATE SET
                            password_hash = EXCLUDED.password_hash,
                            role = EXCLUDED.role,
                            name = EXCLUDED.name,
                            dept = EXCLUDED.dept,
                            email = EXCLUDED.email,
                            did = EXCLUDED.did,
                            is_active = EXCLUDED.is_active,
                            is_disabled = EXCLUDED.is_disabled,
                            can_login = EXCLUDED.can_login,
                            is_archived = EXCLUDED.is_archived,
                            archived_at = EXCLUDED.archived_at,
                            tags = EXCLUDED.tags,
                            updated_at = CURRENT_TIMESTAMP;
                        """,
                        (
                            user_record["username"],
                            user_record["password_hash"],
                            user_record["role"],
                            user_record["name"],
                            user_record["dept"],
                            user_record["email"],
                            user_record["did"],
                            user_record["is_active"],
                            user_record["is_disabled"],
                            user_record["can_login"],
                            user_record["is_archived"],
                            user_record["archived_at"],
                            user_record["tags"],
                        ),
                    )
                conn.commit()
            except Exception as exc:
                logger.warning("PostgreSQL insert user error: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                close_postgresql_connection(conn)

        return user_record

    @staticmethod
    def get_user_by_username(username: str) -> dict[str, Any] | None:
        """
        Fetches a user record by username from PostgreSQL or the in-memory account registry.
        
        Parameters:
        	username (str): The username to look up.
        
        Returns:
        	dict[str, Any] | None: The matching user record, or `None` when no record is available.
        """
        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT username, password_hash, role, name, dept, email, did,
                               is_active, is_disabled, can_login, is_archived, archived_at, tags, created_at
                        FROM users WHERE username = %s;
                        """,
                        (username,),
                    )
                    row = cur.fetchone()
                    if row:
                        user_rec = {
                            "username": row[0],
                            "password_hash": row[1],
                            "role": row[2],
                            "name": row[3],
                            "dept": row[4],
                            "email": row[5],
                            "did": row[6],
                            "is_active": row[7],
                            "is_disabled": row[8],
                            "can_login": row[9],
                            "is_archived": row[10],
                            "archived_at": row[11].isoformat() if row[11] else None,
                            "tags": list(row[12]) if row[12] else [],
                            "created_at": row[13].isoformat() if row[13] else None,
                        }
                        ACCOUNT_REGISTRY[username] = dict(user_rec)
                        USER_REGISTRY[user_rec["did"]] = dict(user_rec)
                        return user_rec
            except Exception as exc:
                logger.warning("PostgreSQL fetch user error: %s", exc)
            finally:
                close_postgresql_connection(conn)

        return ACCOUNT_REGISTRY.get(username)

    @staticmethod
    def list_users() -> list[dict[str, Any]]:
        """
        List all user records in creation order.
        
        Returns:
        	list[dict[str, Any]]: User records retrieved from PostgreSQL, or cached records when PostgreSQL is unavailable or returns no rows.
        """
        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT username, password_hash, role, name, dept, email, did,
                               is_active, is_disabled, can_login, is_archived, archived_at, tags, created_at
                        FROM users ORDER BY created_at ASC;
                        """
                    )
                    rows = cur.fetchall()
                    if rows:
                        results = []
                        for row in rows:
                            u_rec = {
                                "username": row[0],
                                "password_hash": row[1],
                                "role": row[2],
                                "name": row[3],
                                "dept": row[4],
                                "email": row[5],
                                "did": row[6],
                                "is_active": row[7],
                                "is_disabled": row[8],
                                "can_login": row[9],
                                "is_archived": row[10],
                                "archived_at": row[11].isoformat() if row[11] else None,
                                "tags": list(row[12]) if row[12] else [],
                                "created_at": row[13].isoformat() if row[13] else None,
                            }
                            ACCOUNT_REGISTRY[u_rec["username"]] = dict(u_rec)
                            USER_REGISTRY[u_rec["did"]] = dict(u_rec)
                            results.append(u_rec)
                        return results
            except Exception as exc:
                logger.warning("PostgreSQL list users error: %s", exc)
            finally:
                close_postgresql_connection(conn)

        return list(ACCOUNT_REGISTRY.values())

    @staticmethod
    def update_password(username: str, new_password_hash: str) -> bool:
        """
        Update the stored password hash for an existing user.
        
        Parameters:
        	username (str): Username of the user whose password hash is updated.
        	new_password_hash (str): Replacement password hash.
        
        Returns:
        	bool: `True` if the user exists and the update is recorded, `False` if the user does not exist.
        """
        user = DatabaseAPI.get_user_by_username(username)
        if not user:
            return False

        user["password_hash"] = new_password_hash
        ACCOUNT_REGISTRY[username] = user

        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s;",
                        (new_password_hash, username),
                    )
                conn.commit()
            except Exception as exc:
                logger.warning("PostgreSQL update password error: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                close_postgresql_connection(conn)

        return True

    @staticmethod
    def disable_and_archive_user(username: str) -> dict[str, Any] | None:
        """
        Disable and archive an existing user account without deleting its database record.
        
        Parameters:
            username (str): Username of the account to disable and archive.
        
        Returns:
            dict[str, Any] | None: The updated user record, or `None` if the user does not exist.
        """
        user = DatabaseAPI.get_user_by_username(username)
        if not user:
            return None

        archived_at_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        user["is_active"] = False
        user["is_disabled"] = True
        user["can_login"] = False
        user["is_archived"] = True
        user["archived_at"] = archived_at_str
        user["tags"] = ["archive"]

        ACCOUNT_REGISTRY[username] = user

        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE users SET
                            is_active = FALSE,
                            is_disabled = TRUE,
                            can_login = FALSE,
                            is_archived = TRUE,
                            archived_at = CURRENT_TIMESTAMP,
                            tags = ARRAY['archive'],
                            updated_at = CURRENT_TIMESTAMP
                        WHERE username = %s;
                        """,
                        (username,),
                    )
                conn.commit()
            except Exception as exc:
                logger.warning("PostgreSQL disable_and_archive_user error: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                close_postgresql_connection(conn)

        return user

    # --- Role Permissions API Methods ---

    @staticmethod
    def save_role_permissions(permissions: dict[str, list[str]]) -> None:
        """Save role-to-module access permissions to PostgreSQL or in-memory fallback."""
        for mod_id, roles in permissions.items():
            ROLE_MODULE_PERMISSIONS[mod_id] = list(roles)

        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    for mod_id, roles in permissions.items():
                        cur.execute(
                            """
                            INSERT INTO role_permissions (module_id, allowed_roles, updated_at)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (module_id) DO UPDATE SET
                                allowed_roles = EXCLUDED.allowed_roles,
                                updated_at = CURRENT_TIMESTAMP;
                            """,
                            (mod_id, json.dumps(roles)),
                        )
                conn.commit()
            except Exception as exc:
                logger.warning("PostgreSQL save_role_permissions error: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                close_postgresql_connection(conn)

    @staticmethod
    def load_role_permissions() -> dict[str, list[str]]:
        """Load role-to-module access permissions from PostgreSQL or fallback."""
        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT module_id, allowed_roles FROM role_permissions;")
                    rows = cur.fetchall()
                    if rows:
                        res = {}
                        for row in rows:
                            mod_id = row[0]
                            allowed = row[1] if isinstance(row[1], list) else json.loads(row[1])
                            res[mod_id] = [str(r) for r in allowed]
                            ROLE_MODULE_PERMISSIONS[mod_id] = res[mod_id]
                        return res
            except Exception as exc:
                logger.warning("PostgreSQL load_role_permissions error: %s", exc)
            finally:
                close_postgresql_connection(conn)

        return dict(ROLE_MODULE_PERMISSIONS)

    # --- Asset Registration API Methods ---

    @staticmethod
    def save_asset(asset_record: dict[str, Any]) -> dict[str, Any]:
        """
        Persist a research asset record and retain it in the in-memory asset registry.
        
        Parameters:
            asset_record (dict[str, Any]): Asset metadata, including its identifier and
                persistence fields.
        
        Returns:
            dict[str, Any]: The supplied asset record.
        """
        asset_id = asset_record["asset_id"]
        ASSET_REGISTRY[asset_id] = dict(asset_record)

        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO assets (asset_id, title, trl, abstract, file_name, sha256_digest, tx_outbox_id, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (asset_id) DO UPDATE SET
                            title = EXCLUDED.title,
                            trl = EXCLUDED.trl,
                            abstract = EXCLUDED.abstract,
                            file_name = EXCLUDED.file_name,
                            sha256_digest = EXCLUDED.sha256_digest,
                            tx_outbox_id = EXCLUDED.tx_outbox_id;
                        """,
                        (
                            asset_record["asset_id"],
                            asset_record["title"],
                            asset_record["trl"],
                            asset_record["abstract"],
                            asset_record["file_name"],
                            asset_record["sha256_digest"],
                            asset_record["tx_outbox_id"],
                        ),
                    )
                conn.commit()
            except Exception as exc:
                logger.warning("PostgreSQL save_asset error: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                close_postgresql_connection(conn)

        return asset_record

    @staticmethod
    def list_assets() -> list[dict[str, Any]]:
        """
        List research assets ordered by creation time.
        
        Returns:
            list[dict[str, Any]]: Asset records from PostgreSQL, or cached records when PostgreSQL is unavailable.
        """
        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT asset_id, title, trl, abstract, file_name, sha256_digest, tx_outbox_id, created_at
                        FROM assets ORDER BY created_at DESC;
                        """
                    )
                    rows = cur.fetchall()
                    if rows:
                        res = []
                        for row in rows:
                            rec = {
                                "asset_id": row[0],
                                "title": row[1],
                                "trl": row[2],
                                "abstract": row[3],
                                "file_name": row[4],
                                "sha256_digest": row[5],
                                "tx_outbox_id": row[6],
                                "timestamp": row[7].isoformat() if row[7] else None,
                            }
                            ASSET_REGISTRY[rec["asset_id"]] = rec
                            res.append(rec)
                        return res
            except Exception as exc:
                logger.warning("PostgreSQL list_assets error: %s", exc)
            finally:
                close_postgresql_connection(conn)

        return list(ASSET_REGISTRY.values())

    # --- Cloverleaf Score API Methods ---

    @staticmethod
    def save_cloverleaf_score(score_record: dict[str, Any]) -> dict[str, Any]:
        """
        Save a Cloverleaf score record to the database and in-memory storage.
        
        Parameters:
            score_record (dict[str, Any]): Score data, including the asset identifier,
                component scores, total score, and optional qualification status.
        
        Returns:
            dict[str, Any]: The supplied score record.
        """
        _IN_MEMORY_CLOVERLEAF_SCORES.append(dict(score_record))

        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO cloverleaf_scores (asset_id, tech_score, market_score, comm_score, mgmt_score, total_score, is_qualified, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP);
                        """,
                        (
                            score_record.get("asset_id"),
                            score_record["tech_score"],
                            score_record["market_score"],
                            score_record["comm_score"],
                            score_record["mgmt_score"],
                            score_record["total_score"],
                            score_record.get("is_qualified", False),
                        ),
                    )
                conn.commit()
            except Exception as exc:
                logger.warning("PostgreSQL save_cloverleaf_score error: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                close_postgresql_connection(conn)

        return score_record

    # --- Revenue Split API Methods ---

    @staticmethod
    def save_revenue_split(split_record: dict[str, Any]) -> dict[str, Any]:
        """
        Save an IP revenue split allocation and return the supplied record.
        
        Parameters:
            split_record (dict[str, Any]): Revenue split data containing the total ingested amount, revenue type, and distribution splits.
        
        Returns:
            dict[str, Any]: The supplied revenue split record.
        """
        _IN_MEMORY_REVENUE_SPLITS.append(dict(split_record))

        conn, _ = get_postgresql_connection()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO revenue_splits (total_ingested_myr, revenue_type, distribution_splits, created_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP);
                        """,
                        (
                            split_record["total_ingested_myr"],
                            split_record["revenue_type"],
                            json.dumps(split_record["distribution_splits"]),
                        ),
                    )
                conn.commit()
            except Exception as exc:
                logger.warning("PostgreSQL save_revenue_split error: %s", exc)
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                close_postgresql_connection(conn)

        return split_record
