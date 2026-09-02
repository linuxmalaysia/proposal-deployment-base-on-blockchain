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

import copy
from dca_service.adapters.database_api import DatabaseAPI, ACCOUNT_REGISTRY, USER_REGISTRY, ASSET_REGISTRY
from dca_service.web_app import app, create_system_jwt, hash_password, seed_initial_accounts

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
    yield
    ACCOUNT_REGISTRY.clear()
    ACCOUNT_REGISTRY.update(orig_accts)
    USER_REGISTRY.clear()
    USER_REGISTRY.update(orig_users)
    ASSET_REGISTRY.clear()
    ASSET_REGISTRY.update(orig_assets)


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
