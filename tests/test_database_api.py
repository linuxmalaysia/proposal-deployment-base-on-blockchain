"""
Unit and integration tests for Centralized Database API Access Layer and Non-Deletion User Archiving Policy.
Governed by DSOM Protocol // Concentric Clean Architecture // OWASP REST Security Cheat Sheet.
"""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

default_test_secret = "".join(["test_", "rcf_", "dac_", "jwt_", "secret_", "key_", "2026"])
os.environ.setdefault("INVESTOR_JWT_SECRET", default_test_secret)

import copy  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402
from dca_service.adapters import database_api  # noqa: E402
from dca_service.adapters.database_api import (  # noqa: E402
    ACCOUNT_REGISTRY,
    ASSET_REGISTRY,
    ROLE_MODULE_PERMISSIONS,
    USER_REGISTRY,
    DatabaseAPI,
)
from dca_service.web_app import app, create_system_jwt, hash_password, seed_initial_accounts  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_database_api_registries(monkeypatch):
    """
    Isolate in-memory registries and env vars for clean test execution.
    """
    monkeypatch.setenv("INVESTOR_JWT_SECRET", default_test_secret)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    seed_initial_accounts()
    orig_accts = copy.deepcopy(ACCOUNT_REGISTRY)
    orig_users = copy.deepcopy(USER_REGISTRY)
    orig_assets = copy.deepcopy(ASSET_REGISTRY)
    orig_permissions = copy.deepcopy(ROLE_MODULE_PERMISSIONS)
    yield
    ACCOUNT_REGISTRY.clear()
    ACCOUNT_REGISTRY.update(orig_accts)
    USER_REGISTRY.clear()
    USER_REGISTRY.update(orig_users)
    ASSET_REGISTRY.clear()
    ASSET_REGISTRY.update(orig_assets)
    ROLE_MODULE_PERMISSIONS.clear()
    ROLE_MODULE_PERMISSIONS.update(orig_permissions)


def test_database_api_user_creation_and_fields():
    """Verify DatabaseAPI creates user accounts with standard status flags and archive tag fields."""
    user_record = {
        "username": "db_test_user_01",
        "password_hash": hash_password("Password123!"),
        "role": "operator",
        "name": "Database API Test User",
        "dept": "Software Engineering",
        "email": "dbtest01@rcf-dac.univ.edu.my",
        "did": "did:univ:dbtest01",
    }
    created = DatabaseAPI.create_user(user_record)

    assert created["username"] == "db_test_user_01"
    assert created["is_active"] is True
    assert created["is_disabled"] is False
    assert created["can_login"] is True
    assert created["is_archived"] is False
    assert "active" in created["tags"]

    # Retrieve created user
    retrieved = DatabaseAPI.get_user_by_username("db_test_user_01")
    assert retrieved is not None
    assert retrieved["did"] == "did:univ:dbtest01"


def test_non_deletion_user_archiving_policy():
    """
    POLICY REQUIREMENT: No user created will be deleted.
    Only disabled and set to non login and archive with tag 'archive'.
    """
    user_record = {
        "username": "no_delete_user",
        "password_hash": hash_password("Password123!"),
        "role": "operator",
        "name": "Non Delete User",
        "dept": "Operations",
        "email": "nodelete@rcf-dac.univ.edu.my",
        "did": "did:univ:nodelete01",
    }
    DatabaseAPI.create_user(user_record)

    # Invoke soft delete & archive method
    archived = DatabaseAPI.disable_and_archive_user("no_delete_user")
    assert archived is not None
    assert archived["is_active"] is False
    assert archived["is_disabled"] is True
    assert archived["can_login"] is False
    assert archived["is_archived"] is True
    assert archived["archived_at"] is not None
    assert "archive" in archived["tags"]

    # Verify user STILL exists in database / registry and was NOT deleted
    user_in_db = DatabaseAPI.get_user_by_username("no_delete_user")
    assert user_in_db is not None
    assert user_in_db["username"] == "no_delete_user"
    assert user_in_db["is_archived"] is True


def test_archived_user_login_rejection():
    """Verify that disabled/archived users cannot authenticate via login endpoint."""
    user_record = {
        "username": "disabled_login_user",
        "password_hash": hash_password("ValidPass123!"),
        "role": "operator",
        "name": "Disabled Login User",
        "dept": "Testing Dept",
        "email": "disabled@rcf-dac.univ.edu.my",
        "did": "did:univ:disabledlogin",
    }
    DatabaseAPI.create_user(user_record)

    # First attempt: valid login before archiving
    res1 = client.post("/api/login", json={"username": "disabled_login_user", "password": "ValidPass123!"})
    assert res1.status_code == 200

    # Disable & archive user
    DatabaseAPI.disable_and_archive_user("disabled_login_user")

    # Second attempt: rejected due to disabled/archived status
    res2 = client.post("/api/login", json={"username": "disabled_login_user", "password": "ValidPass123!"})
    assert res2.status_code == 401
    assert "authentication failed" in res2.json()["detail"].lower()


def test_api_user_archive_endpoint():
    """Verify DELETE /api/users/{username} endpoint archives user without record deletion."""
    admin_jwt = create_system_jwt("dca_admin_mgr", "admin")

    user_record = {
        "username": "user_to_archive_via_api",
        "password_hash": hash_password("ValidPass123!"),
        "role": "operator",
        "name": "API Archive User",
        "dept": "Testing Dept",
        "email": "apiarchive@rcf-dac.univ.edu.my",
        "did": "did:univ:apiarchive01",
    }
    DatabaseAPI.create_user(user_record)

    # Call DELETE endpoint
    res = client.delete(
        "/api/users/user_to_archive_via_api",
        headers={"Authorization": f"Bearer {admin_jwt}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "archived" in data["message"].lower()

    # User MUST remain in registry and database
    user_rec = DatabaseAPI.get_user_by_username("user_to_archive_via_api")
    assert user_rec is not None
    assert user_rec["is_archived"] is True
    assert user_rec["can_login"] is False
    assert "archive" in user_rec["tags"]


def test_database_api_asset_and_scores_persistence():
    """Verify DatabaseAPI persists research assets, Cloverleaf scores, and revenue splits."""
    asset_record = {
        "asset_id": "did:univ:asset-db-test-01",
        "title": "Quantum Sensor Array Prototype",
        "trl": 4,
        "abstract": "High precision quantum sensing module",
        "file_name": "quantum_spec.pdf",
        "sha256_digest": "sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "tx_outbox_id": "outbox_tx_123456",
    }
    saved_asset = DatabaseAPI.save_asset(asset_record)
    assert saved_asset["asset_id"] == "did:univ:asset-db-test-01"

    assets = DatabaseAPI.list_assets()
    asset_ids = [a["asset_id"] for a in assets]
    assert "did:univ:asset-db-test-01" in asset_ids

    # Cloverleaf score
    score_rec = {
        "tech_score": 50,
        "market_score": 70,
        "comm_score": 50,
        "mgmt_score": 50,
        "total_score": 220,
        "is_qualified": True,
    }
    saved_score = DatabaseAPI.save_cloverleaf_score(score_rec)
    assert saved_score["total_score"] == 220

    # Revenue split
    split_rec = {
        "total_ingested_myr": "500000.00",
        "revenue_type": "licensing",
        "distribution_splits": [{"stakeholder": "Treasury", "amount_myr": "150000.00"}],
    }
    saved_split = DatabaseAPI.save_revenue_split(split_rec)
    assert saved_split["revenue_type"] == "licensing"


def test_failed_database_write_does_not_populate_registry(monkeypatch: pytest.MonkeyPatch):
    """Verify that a failed PostgreSQL transaction raises RuntimeError and leaves registry unmodified."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = RuntimeError("Simulated Database Error")
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    monkeypatch.setattr(
        "dca_service.adapters.database_api.get_postgresql_connection",
        lambda: (mock_conn, "Connected"),
    )

    user_data = {
        "username": "failed_db_write_user",
        "password_hash": hash_password("ValidPass123!"),
        "role": "operator",
        "name": "Failed Write User",
        "dept": "Testing Dept",
        "email": "failedwrite@rcf-dac.univ.edu.my",
        "did": "did:univ:failedwrite01",
    }

    with pytest.raises(RuntimeError, match="Database user creation failed"):
        DatabaseAPI.create_user(user_data)

    assert "failed_db_write_user" not in ACCOUNT_REGISTRY


def test_duplicate_creation_on_archived_user_preserves_archived_state():
    """Regression test: duplicate create_user calls on an archived user must preserve archived/disabled state and password hash."""
    user_record = {
        "username": "archived_dup_user",
        "password_hash": hash_password("ValidPass123!"),
        "role": "operator",
        "name": "Archived Dup User",
        "dept": "Testing Dept",
        "email": "archiveddup@rcf-dac.univ.edu.my",
        "did": "did:univ:archiveddup01",
    }
    DatabaseAPI.create_user(user_record)
    original_hash = ACCOUNT_REGISTRY["archived_dup_user"]["password_hash"]

    # Disable & archive user
    DatabaseAPI.disable_and_archive_user("archived_dup_user")
    assert ACCOUNT_REGISTRY["archived_dup_user"]["is_archived"] is True
    assert ACCOUNT_REGISTRY["archived_dup_user"]["can_login"] is False

    # Attempt duplicate create_user with updated name/role and new password hash
    duplicate_record = {
        "username": "archived_dup_user",
        "password_hash": hash_password("NewPass123!"),
        "role": "admin",
        "name": "Updated Name",
        "dept": "New Dept",
        "email": "archiveddup@rcf-dac.univ.edu.my",
        "did": "did:univ:archiveddup01",
    }
    DatabaseAPI.create_user(duplicate_record)

    # Verify archived & disabled status preserved and password_hash remains unchanged
    updated_user = ACCOUNT_REGISTRY["archived_dup_user"]
    assert updated_user["is_archived"] is True
    assert updated_user["is_disabled"] is True
    assert updated_user["can_login"] is False
    assert updated_user["name"] == "Updated Name"
    assert updated_user["password_hash"] == original_hash

    # Attempt login using original valid password -> must be rejected due to disabled/archived status
    res = client.post("/api/login", json={"username": "archived_dup_user", "password": "ValidPass123!"})
    assert res.status_code == 401


def test_get_sync_db_pool_uses_connection_pool_metric_limits(
    monkeypatch: pytest.MonkeyPatch,
):
    """Build the synchronous pool with the configured minimum and maximum sizes."""
    pool = MagicMock()
    pool_constructor = MagicMock(return_value=pool)
    monkeypatch.setattr(database_api, "SYNC_DB_POOL", None)
    monkeypatch.setattr(
        database_api,
        "get_database_url",
        lambda: "postgresql://database.example/test?sslmode=verify-full",
    )
    monkeypatch.setattr(database_api.DB_POOL_METRICS, "min_pool_size", 3)
    monkeypatch.setattr(database_api.DB_POOL_METRICS, "max_pool_size", 11)
    monkeypatch.setattr("psycopg_pool.ConnectionPool", pool_constructor)

    result = database_api.get_sync_db_pool()

    assert result is pool
    pool_constructor.assert_called_once_with(
        conninfo="postgresql://database.example/test?sslmode=verify-full",
        min_size=3,
        max_size=11,
        open=True,
    )


def test_get_user_database_failure_does_not_return_stale_registry_record(
    monkeypatch: pytest.MonkeyPatch,
):
    """Fail closed when an active database query fails instead of serving stale user data."""
    ACCOUNT_REGISTRY["stale_user"] = {"username": "stale_user", "role": "admin"}
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = RuntimeError("query interrupted")
    close_connection = MagicMock()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "Connected"),
    )
    monkeypatch.setattr(database_api, "close_postgresql_connection", close_connection)

    assert DatabaseAPI.get_user_by_username("stale_user") is None
    close_connection.assert_called_once_with(connection)


def test_save_role_permissions_commits_before_publishing_defensive_copies(
    monkeypatch: pytest.MonkeyPatch,
):
    """Persist permission changes and detach the published mapping from caller-owned lists."""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    close_connection = MagicMock()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "Connected"),
    )
    monkeypatch.setattr(database_api, "close_postgresql_connection", close_connection)
    permissions = {"module_2": ["operator", "auditor"]}

    DatabaseAPI.save_role_permissions(permissions)

    connection.commit.assert_called_once_with()
    cursor.execute.assert_called_once()
    assert cursor.execute.call_args.args[1] == (
        "module_2",
        '["operator", "auditor"]',
    )
    assert ROLE_MODULE_PERMISSIONS["module_2"] == ["operator", "auditor"]
    permissions["module_2"].append("investor")
    assert ROLE_MODULE_PERMISSIONS["module_2"] == ["operator", "auditor"]
    close_connection.assert_called_once_with(connection)


def test_save_role_permissions_rolls_back_without_publishing_partial_state(
    monkeypatch: pytest.MonkeyPatch,
):
    """Keep the complete in-memory mapping unchanged when database persistence fails."""
    original_permissions = copy.deepcopy(ROLE_MODULE_PERMISSIONS)
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = RuntimeError("write conflict")
    close_connection = MagicMock()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "Connected"),
    )
    monkeypatch.setattr(database_api, "close_postgresql_connection", close_connection)

    with pytest.raises(RuntimeError, match="Database save role permissions failed"):
        DatabaseAPI.save_role_permissions(
            {
                "module_2": ["researcher"],
                "module_3": ["auditor"],
            }
        )

    assert ROLE_MODULE_PERMISSIONS == original_permissions
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once_with()
    close_connection.assert_called_once_with(connection)


def test_load_role_permissions_normalises_database_values_and_returns_copies(
    monkeypatch: pytest.MonkeyPatch,
):
    """Support JSON and list columns while preventing returned values from aliasing cache state."""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [
        ("module_2", '["operator", "auditor"]'),
        ("module_3", ["operator", 7]),
    ]
    close_connection = MagicMock()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "Connected"),
    )
    monkeypatch.setattr(database_api, "close_postgresql_connection", close_connection)

    loaded = DatabaseAPI.load_role_permissions()

    assert loaded == {
        "module_2": ["operator", "auditor"],
        "module_3": ["operator", "7"],
    }
    loaded["module_2"].append("investor")
    assert ROLE_MODULE_PERMISSIONS["module_2"] == ["operator", "auditor"]
    cursor.execute.assert_called_once_with(
        "SELECT module_id, allowed_roles FROM role_permissions;"
    )
    close_connection.assert_called_once_with(connection)


def test_load_role_permissions_query_failure_returns_detached_fallback(
    monkeypatch: pytest.MonkeyPatch,
):
    """Return a defensive fallback snapshot after a database read error."""
    ROLE_MODULE_PERMISSIONS["module_2"] = ["operator"]
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.execute.side_effect = RuntimeError("database unavailable")
    close_connection = MagicMock()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "Connected"),
    )
    monkeypatch.setattr(database_api, "close_postgresql_connection", close_connection)

    loaded = DatabaseAPI.load_role_permissions()

    assert loaded["module_2"] == ["operator"]
    loaded["module_2"].append("auditor")
    assert ROLE_MODULE_PERMISSIONS["module_2"] == ["operator"]
    close_connection.assert_called_once_with(connection)
