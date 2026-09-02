"""
Unit and integration tests for Centralized Database API Access Layer and Non-Deletion User Archiving Policy.
Governed by DSOM Protocol // Concentric Clean Architecture // OWASP REST Security Cheat Sheet.
"""

from __future__ import annotations

import copy
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

default_test_secret = "test_rcf_dac_jwt_" + "secret_key_2026"
os.environ.setdefault("INVESTOR_JWT_SECRET", default_test_secret)

from dca_service.adapters import database_api  # noqa: E402
from dca_service.adapters.database_api import (  # noqa: E402
    ACCOUNT_REGISTRY,
    ASSET_REGISTRY,
    ROLE_MODULE_PERMISSIONS,
    USER_REGISTRY,
    ConnectionPoolMetrics,
    DatabaseAPI,
)
from dca_service.web_app import app, create_system_jwt, hash_password  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_database_api_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Keep mutable registries, caches, cookies, and database access test-local."""
    registries = (
        ACCOUNT_REGISTRY,
        USER_REGISTRY,
        ASSET_REGISTRY,
        ROLE_MODULE_PERMISSIONS,
    )
    snapshots = [copy.deepcopy(registry) for registry in registries]
    score_snapshot = copy.deepcopy(database_api._IN_MEMORY_CLOVERLEAF_SCORES)
    split_snapshot = copy.deepcopy(database_api._IN_MEMORY_REVENUE_SPLITS)

    for registry in registries:
        registry.clear()
    database_api._IN_MEMORY_CLOVERLEAF_SCORES.clear()
    database_api._IN_MEMORY_REVENUE_SPLITS.clear()
    client.cookies.clear()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (None, "Database unavailable during unit test"),
    )

    yield

    for registry, snapshot in zip(registries, snapshots):
        registry.clear()
        registry.update(snapshot)
    database_api._IN_MEMORY_CLOVERLEAF_SCORES[:] = score_snapshot
    database_api._IN_MEMORY_REVENUE_SPLITS[:] = split_snapshot
    client.cookies.clear()


def make_user_record(**overrides: Any) -> dict[str, Any]:
    """Return a complete user record with optional field overrides."""
    record = {
        "username": "db_test_user",
        "password_hash": hash_password("Password123!"),
        "role": "operator",
        "name": "Database API Test User",
        "dept": "Software Engineering",
        "email": "dbtest@rcf-dac.univ.edu.my",
        "did": "did:univ:dbtest",
    }
    record.update(overrides)
    return record


def make_connection() -> tuple[MagicMock, MagicMock]:
    """Build a mock connection and its context-managed cursor."""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    return connection, cursor


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
    assert "disabled and archived" in res2.json()["detail"].lower()


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


def test_connection_pool_metrics_report_average_failures_and_utilisation(
    monkeypatch: pytest.MonkeyPatch,
):
    """Metrics should distinguish failed attempts and avoid averaging them as checkouts."""
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "8")
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "2")
    monkeypatch.setattr(database_api.time, "strftime", lambda *_args: "2026-09-02T12:00:00Z")
    metrics = ConnectionPoolMetrics()

    metrics.record_connection_attempt(10.125, success=True)
    metrics.record_connection_attempt(20.135, success=True)
    metrics.record_connection_attempt(999.0, success=False)
    metrics.record_query()
    metrics.active_connections = 2

    assert metrics.to_dict() == {
        "max_pool_size": 8,
        "min_pool_size": 2,
        "total_connections_acquired": 2,
        "failed_connection_attempts": 1,
        "avg_checkout_latency_ms": 15.13,
        "total_queries_executed": 1,
        "pool_utilization_percent": 25.0,
        "timestamp": "2026-09-02T12:00:00Z",
    }


def test_connection_pool_metrics_handle_zero_capacity_without_division_error(
    monkeypatch: pytest.MonkeyPatch,
):
    """A zero-sized pool should report zero latency and utilisation safely."""
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "0")
    metrics = ConnectionPoolMetrics()
    metrics.active_connections = 3

    result = metrics.to_dict()

    assert result["avg_checkout_latency_ms"] == 0.0
    assert result["pool_utilization_percent"] == 0.0


def test_close_postgresql_connection_swallows_driver_error_and_never_underflows_metrics(
    monkeypatch: pytest.MonkeyPatch,
):
    """Closing a failed driver connection must still keep active metrics non-negative."""
    connection = MagicMock()
    connection.close.side_effect = RuntimeError("socket already closed")
    monkeypatch.setattr(database_api.DB_POOL_METRICS, "active_connections", 1)

    database_api.close_postgresql_connection(connection)
    database_api.close_postgresql_connection(connection)
    database_api.close_postgresql_connection(None)

    assert connection.close.call_count == 2
    assert database_api.DB_POOL_METRICS.active_connections == 0


def test_database_api_get_connection_delegates_to_connection_factory(
    monkeypatch: pytest.MonkeyPatch,
):
    """The adapter facade should return the exact connection factory result."""
    connection = MagicMock()
    get_connection = MagicMock(return_value=(connection, "connected"))
    monkeypatch.setattr(database_api, "get_postgresql_connection", get_connection)

    assert DatabaseAPI.get_connection() == (connection, "connected")
    get_connection.assert_called_once_with()


def test_create_user_commits_normalised_record_to_postgresql(
    monkeypatch: pytest.MonkeyPatch,
):
    """User creation should cache a copy and commit all account-state columns."""
    connection, cursor = make_connection()
    close_connection = MagicMock()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "connected"),
    )
    monkeypatch.setattr(database_api, "close_postgresql_connection", close_connection)
    supplied = make_user_record(tags=["review"], is_active=False)

    created = DatabaseAPI.create_user(supplied)

    statement, parameters = cursor.execute.call_args.args
    assert "ON CONFLICT (username) DO UPDATE" in statement
    assert parameters == (
        "db_test_user",
        supplied["password_hash"],
        "operator",
        "Database API Test User",
        "Software Engineering",
        "dbtest@rcf-dac.univ.edu.my",
        "did:univ:dbtest",
        False,
        False,
        True,
        False,
        None,
        ["review"],
    )
    assert created["created_at"]
    assert created["updated_at"]
    assert ACCOUNT_REGISTRY["db_test_user"] == created
    assert USER_REGISTRY["did:univ:dbtest"] == created
    assert ACCOUNT_REGISTRY["db_test_user"] is not created
    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    close_connection.assert_called_once_with(connection)


def test_create_user_rolls_back_but_keeps_offline_fallback(
    monkeypatch: pytest.MonkeyPatch,
):
    """A database write failure should roll back while retaining the usable cache."""
    connection, cursor = make_connection()
    cursor.execute.side_effect = RuntimeError("database unavailable")
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "connected"),
    )

    created = DatabaseAPI.create_user(make_user_record())

    assert ACCOUNT_REGISTRY["db_test_user"] == created
    assert USER_REGISTRY["did:univ:dbtest"] == created
    connection.commit.assert_not_called()
    connection.rollback.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_get_user_maps_database_types_and_refreshes_both_registries(
    monkeypatch: pytest.MonkeyPatch,
):
    """Database rows should become JSON-safe records and refresh both lookup caches."""
    connection, cursor = make_connection()
    archived_at = datetime(2026, 9, 1, 9, 30, tzinfo=UTC)
    created_at = datetime(2026, 8, 31, 8, 15, tzinfo=UTC)
    cursor.fetchone.return_value = (
        "stored_user",
        "stored_hash",
        "auditor",
        "Stored User",
        "Audit",
        "stored@example.test",
        "did:univ:stored",
        False,
        True,
        False,
        True,
        archived_at,
        ("archive",),
        created_at,
    )
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "connected"),
    )

    result = DatabaseAPI.get_user_by_username("stored_user")

    assert result is not None
    assert result["archived_at"] == archived_at.isoformat()
    assert result["created_at"] == created_at.isoformat()
    assert result["tags"] == ["archive"]
    assert ACCOUNT_REGISTRY["stored_user"] == result
    assert USER_REGISTRY["did:univ:stored"] == result
    assert cursor.execute.call_args.args[1] == ("stored_user",)
    connection.close.assert_called_once_with()


def test_get_user_falls_back_to_cache_after_query_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    """Transient read failures should return the previously cached account."""
    cached = make_user_record()
    ACCOUNT_REGISTRY[cached["username"]] = cached
    connection, cursor = make_connection()
    cursor.execute.side_effect = RuntimeError("read failed")
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "connected"),
    )

    assert DatabaseAPI.get_user_by_username("db_test_user") is cached
    connection.close.assert_called_once_with()


def test_list_users_maps_rows_in_database_order_and_handles_nulls(
    monkeypatch: pytest.MonkeyPatch,
):
    """User listing should preserve query order and normalise nullable database values."""
    connection, cursor = make_connection()
    cursor.fetchall.return_value = [
        (
            "first",
            "hash",
            "operator",
            "First User",
            "Ops",
            "first@example.test",
            "did:univ:first",
            True,
            False,
            True,
            False,
            None,
            None,
            None,
        ),
        (
            "second",
            "hash",
            "auditor",
            "Second User",
            "Audit",
            "second@example.test",
            "did:univ:second",
            False,
            True,
            False,
            True,
            datetime(2026, 9, 2, tzinfo=UTC),
            ["archive"],
            datetime(2026, 9, 1, tzinfo=UTC),
        ),
    ]
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "connected"),
    )

    users = DatabaseAPI.list_users()

    assert [user["username"] for user in users] == ["first", "second"]
    assert users[0]["tags"] == []
    assert users[0]["created_at"] is None
    assert users[1]["archived_at"] == "2026-09-02T00:00:00+00:00"
    assert set(ACCOUNT_REGISTRY) == {"first", "second"}
    assert set(USER_REGISTRY) == {"did:univ:first", "did:univ:second"}
    assert "ORDER BY created_at ASC" in cursor.execute.call_args.args[0]


def test_update_password_handles_missing_user_without_opening_write_connection(
    monkeypatch: pytest.MonkeyPatch,
):
    """Missing accounts should produce a false result and no database update."""
    get_connection = MagicMock(return_value=(None, "offline"))
    monkeypatch.setattr(database_api, "get_postgresql_connection", get_connection)

    assert DatabaseAPI.update_password("missing", "new-hash") is False
    assert get_connection.call_count == 1


def test_update_password_commits_for_cached_user(monkeypatch: pytest.MonkeyPatch):
    """Existing users should be updated in memory and PostgreSQL."""
    user = make_user_record()
    ACCOUNT_REGISTRY[user["username"]] = user
    connection, cursor = make_connection()
    connection_results = iter([(None, "offline"), (connection, "connected")])
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: next(connection_results),
    )

    assert DatabaseAPI.update_password("db_test_user", "replacement-hash") is True
    assert ACCOUNT_REGISTRY["db_test_user"]["password_hash"] == "replacement-hash"
    assert cursor.execute.call_args.args[1] == ("replacement-hash", "db_test_user")
    connection.commit.assert_called_once_with()
    connection.close.assert_called_once_with()


def test_archive_missing_user_returns_none_without_write_connection(
    monkeypatch: pytest.MonkeyPatch,
):
    """Archiving an unknown username should be a no-op."""
    get_connection = MagicMock(return_value=(None, "offline"))
    monkeypatch.setattr(database_api, "get_postgresql_connection", get_connection)

    assert DatabaseAPI.disable_and_archive_user("missing") is None
    assert get_connection.call_count == 1


def test_archive_user_commits_non_deletion_state(monkeypatch: pytest.MonkeyPatch):
    """Archiving should update state in place and issue only an UPDATE statement."""
    user = make_user_record(tags=["active", "priority"])
    ACCOUNT_REGISTRY[user["username"]] = user
    connection, cursor = make_connection()
    connection_results = iter([(None, "offline"), (connection, "connected")])
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: next(connection_results),
    )

    archived = DatabaseAPI.disable_and_archive_user("db_test_user")

    assert archived is not None
    assert archived["tags"] == ["archive"]
    assert archived["archived_at"].endswith("Z")
    statement, parameters = cursor.execute.call_args.args
    assert statement.lstrip().startswith("UPDATE users SET")
    assert "DELETE" not in statement.upper()
    assert "tags = ARRAY['archive']" in statement
    assert parameters == ("db_test_user",)
    assert "db_test_user" in ACCOUNT_REGISTRY
    connection.commit.assert_called_once_with()


def test_role_permissions_are_copied_serialised_and_committed(
    monkeypatch: pytest.MonkeyPatch,
):
    """Role permission writes should isolate caller lists and serialise JSON for PostgreSQL."""
    connection, cursor = make_connection()
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "connected"),
    )
    permissions = {"module_2": ["operator", "researcher"]}

    DatabaseAPI.save_role_permissions(permissions)
    permissions["module_2"].append("admin")

    assert ROLE_MODULE_PERMISSIONS["module_2"] == ["operator", "researcher"]
    assert cursor.execute.call_args.args[1] == (
        "module_2",
        '["operator", "researcher"]',
    )
    connection.commit.assert_called_once_with()


def test_load_role_permissions_accepts_json_and_native_json_rows(
    monkeypatch: pytest.MonkeyPatch,
):
    """Permission reads should handle driver-decoded JSON and raw JSON text."""
    connection, cursor = make_connection()
    cursor.fetchall.return_value = [
        ("module_2", ["operator"]),
        ("module_4", '["investor", 7]'),
    ]
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: (connection, "connected"),
    )

    result = DatabaseAPI.load_role_permissions()

    assert result == {
        "module_2": ["operator"],
        "module_4": ["investor", "7"],
    }
    assert ROLE_MODULE_PERMISSIONS == result
    connection.close.assert_called_once_with()


def test_save_and_list_assets_use_postgresql_and_cache_copies(
    monkeypatch: pytest.MonkeyPatch,
):
    """Asset persistence should upsert writes and map database timestamps on reads."""
    write_connection, write_cursor = make_connection()
    read_connection, read_cursor = make_connection()
    read_cursor.fetchall.return_value = [
        (
            "asset-1",
            "Stored Asset",
            6,
            "Abstract",
            "evidence.pdf",
            "sha256:digest",
            "outbox-1",
            datetime(2026, 9, 2, 10, 0, tzinfo=UTC),
        )
    ]
    connection_results = iter(
        [(write_connection, "connected"), (read_connection, "connected")]
    )
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: next(connection_results),
    )
    asset = {
        "asset_id": "asset-1",
        "title": "Pending Asset",
        "trl": 5,
        "abstract": "Draft",
        "file_name": "draft.pdf",
        "sha256_digest": "sha256:draft",
        "tx_outbox_id": "outbox-draft",
    }

    assert DatabaseAPI.save_asset(asset) is asset
    asset["title"] = "Caller mutation"
    listed = DatabaseAPI.list_assets()

    assert ASSET_REGISTRY["asset-1"]["title"] == "Stored Asset"
    assert listed == [
        {
            "asset_id": "asset-1",
            "title": "Stored Asset",
            "trl": 6,
            "abstract": "Abstract",
            "file_name": "evidence.pdf",
            "sha256_digest": "sha256:digest",
            "tx_outbox_id": "outbox-1",
            "timestamp": "2026-09-02T10:00:00+00:00",
        }
    ]
    assert "ON CONFLICT (asset_id) DO UPDATE" in write_cursor.execute.call_args.args[0]
    write_connection.commit.assert_called_once_with()
    assert "ORDER BY created_at DESC" in read_cursor.execute.call_args.args[0]


def test_score_and_revenue_writes_apply_defaults_and_json_encoding(
    monkeypatch: pytest.MonkeyPatch,
):
    """Score and revenue records should be cached and encoded for their SQL columns."""
    score_connection, score_cursor = make_connection()
    split_connection, split_cursor = make_connection()
    connection_results = iter(
        [(score_connection, "connected"), (split_connection, "connected")]
    )
    monkeypatch.setattr(
        database_api,
        "get_postgresql_connection",
        lambda: next(connection_results),
    )
    score = {
        "tech_score": 40,
        "market_score": 50,
        "comm_score": 30,
        "mgmt_score": 20,
        "total_score": 140,
    }
    split = {
        "total_ingested_myr": "1.00",
        "revenue_type": "royalties",
        "distribution_splits": [{"stakeholder": "Treasury", "amount_myr": "1.00"}],
    }

    DatabaseAPI.save_cloverleaf_score(score)
    DatabaseAPI.save_revenue_split(split)

    assert score_cursor.execute.call_args.args[1] == (None, 40, 50, 30, 20, 140, False)
    assert split_cursor.execute.call_args.args[1] == (
        "1.00",
        "royalties",
        '[{"stakeholder": "Treasury", "amount_myr": "1.00"}]',
    )
    assert database_api._IN_MEMORY_CLOVERLEAF_SCORES == [score]
    assert database_api._IN_MEMORY_CLOVERLEAF_SCORES[0] is not score
    assert database_api._IN_MEMORY_REVENUE_SPLITS == [split]
    assert database_api._IN_MEMORY_REVENUE_SPLITS[0] is not split
    score_connection.commit.assert_called_once_with()
    split_connection.commit.assert_called_once_with()


@pytest.mark.parametrize(
    ("state_override", "field"),
    [
        ({"is_disabled": True}, "is_disabled"),
        ({"can_login": False}, "can_login"),
        ({"is_archived": True}, "is_archived"),
    ],
)
def test_login_rejects_each_non_login_state_independently(state_override, field):
    """Every account-state guard should independently prevent authentication."""
    DatabaseAPI.create_user(
        make_user_record(
            username=f"blocked_{field}",
            did=f"did:univ:{field}",
            **state_override,
        )
    )

    response = client.post(
        "/api/login",
        json={"username": f"blocked_{field}", "password": "Password123!"},
    )

    assert response.status_code == 401
    assert "disabled and archived" in response.json()["detail"].lower()


@pytest.mark.parametrize("caller_role", ["operator", "auditor"])
def test_archive_endpoint_denies_callers_without_admin_authority(caller_role):
    """Account-level archive actions should deny roles without admin authority."""
    DatabaseAPI.create_user(make_user_record(username="archive_target"))
    token = create_system_jwt(f"test_{caller_role}", caller_role)

    response = client.delete(
        "/api/users/archive_target",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert ACCOUNT_REGISTRY["archive_target"].get("is_archived", False) is False


def test_archive_endpoint_accepts_superuser_with_admin_claim():
    """The generated superuser token should carry the claim required to archive users."""
    DatabaseAPI.create_user(make_user_record(username="archive_target"))
    token = create_system_jwt("dca_sys_root", "superuser")

    response = client.delete(
        "/api/users/archive_target",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert ACCOUNT_REGISTRY["archive_target"]["is_archived"] is True


def test_archive_endpoint_returns_not_found_without_creating_a_record():
    """A valid admin must receive 404 when the archive target does not exist."""
    token = create_system_jwt("dca_admin_mgr", "admin")

    response = client.delete(
        "/api/users/missing-user",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "missing-user" not in ACCOUNT_REGISTRY


def test_archive_endpoint_protects_superuser_record():
    """The non-deletion endpoint must also refuse to disable a superuser."""
    DatabaseAPI.create_user(
        make_user_record(
            username="protected_root",
            did="did:univ:protected-root",
            role="superuser",
        )
    )
    token = create_system_jwt("dca_admin_mgr", "admin")

    response = client.delete(
        "/api/users/protected_root",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert ACCOUNT_REGISTRY["protected_root"].get("is_archived", False) is False


def test_schema_defines_non_deletion_account_state_and_supporting_indexes():
    """The canonical DDL should retain users and expose explicit archive state."""
    schema = (Path(__file__).parents[1] / "docs" / "schema.sql").read_text(
        encoding="utf-8"
    )
    normalised = " ".join(schema.split())

    assert "is_disabled BOOLEAN NOT NULL DEFAULT FALSE" in normalised
    assert "can_login BOOLEAN NOT NULL DEFAULT TRUE" in normalised
    assert "is_archived BOOLEAN NOT NULL DEFAULT FALSE" in normalised
    assert "archived_at TIMESTAMP WITH TIME ZONE" in normalised
    assert "CREATE TABLE IF NOT EXISTS role_permissions" in normalised
    assert "CREATE TABLE IF NOT EXISTS sub_accounts" in normalised
    assert "idx_users_archived ON users(is_archived, is_disabled)" in normalised
