"""
Scenario Tests for Database Resilience, JWT Extended Claim Edge Cases, and RBAC User Management.

Governed by DSOM Protocol // OKF v0.2 Standard.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from dca_service.web_app import (
    ACCOUNT_REGISTRY,
    EXPECTED_AUDIENCE,
    EXPECTED_ISSUER,
    INVESTOR_JWT_SECRET,
    app,
    base64url_encode,
    check_database_connection,
    create_system_jwt,
    get_postgresql_connection,
    hash_password,
)

client = TestClient(app)


# --- Database Reconnect Resilience Tests ---

def test_database_reconnect_resilience_drop_and_recovery():
    """Simulate transient PostgreSQL database connection failures and recovery."""
    with patch("dca_service.web_app.get_postgresql_connection") as mock_get_conn:
        # 1. Connection fails with database unavailable error
        mock_get_conn.return_value = (None, "PostgreSQL connection timeout / connection refused")
        res_fail = check_database_connection(bypass_cache=True)
        assert res_fail["is_connected"] is False
        assert "DISCONNECTED" in res_fail["status"]
        assert "timeout" in res_fail["status_detail"].lower()

        # 2. Connection recovers successfully
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("users",), ("assets",), ("cloverleaf_scores",)]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = (mock_conn, "Connected to PostgreSQL")

        res_recovered = check_database_connection(bypass_cache=True)
        assert res_recovered["is_connected"] is True
        assert res_recovered["status"] == "SUCCESSFULLY CONNECTED"
        assert res_recovered["schema_tables"][0]["status"] == "VERIFIED IN POSTGRESQL DB"


# --- Extended JWT Claim Edge Case Tests ---

def test_jwt_extended_claims_edge_cases():
    """Test extended JWT claims including sub mismatch, custom claims, and boundary exp values."""
    header = {"alg": "HS256", "typ": "JWT"}

    # 1. Zero/Negative exp timestamp
    payload_neg_exp = {
        "sub": "user_zero_exp",
        "iss": EXPECTED_ISSUER,
        "aud": EXPECTED_AUDIENCE,
        "exp": 0,
        "accredited_investor": True,
    }
    jwt_neg_exp = _sign_jwt(header, payload_neg_exp)
    res_neg = client.get("/api/investor-assets", headers={"Authorization": f"Bearer {jwt_neg_exp}"})
    assert res_neg.status_code == 403
    assert "expired" in res_neg.json()["detail"].lower()

    # 2. Infinite / NaN exp claim
    payload_nan_exp = {
        "sub": "user_nan",
        "iss": EXPECTED_ISSUER,
        "aud": EXPECTED_AUDIENCE,
        "exp": "non_numeric_exp",
        "accredited_investor": True,
    }
    jwt_nan = _sign_jwt(header, payload_nan_exp)
    res_nan = client.get("/api/investor-assets", headers={"Authorization": f"Bearer {jwt_nan}"})
    assert res_nan.status_code == 403
    assert "numeric" in res_nan.json()["detail"].lower()

    # 3. Missing 'sub' or empty claims -> Handled cleanly
    payload_no_sub = {
        "iss": EXPECTED_ISSUER,
        "aud": EXPECTED_AUDIENCE,
        "exp": int(time.time() + 3600),
        "accredited_investor": True,
    }
    jwt_no_sub = _sign_jwt(header, payload_no_sub)
    res_no_sub = client.get("/api/investor-assets", headers={"Authorization": f"Bearer {jwt_no_sub}"})
    assert res_no_sub.status_code == 200


def _sign_jwt(header: dict[str, Any], payload: dict[str, Any], secret: bytes = INVESTOR_JWT_SECRET) -> str:
    h_b64 = base64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p_b64 = base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = base64url_encode(hmac.new(secret, f"{h_b64}.{p_b64}".encode(), hashlib.sha256).digest())
    return f"{h_b64}.{p_b64}.{sig}"


# --- Login & RBAC Scenario Tests ---

def test_rbac_authentication_login_flow():
    """Test login API endpoint with valid, invalid, and missing credentials."""
    # 1. Valid Admin Login
    admin_pass = ACCOUNT_REGISTRY["dca_admin_mgr"]["raw_initial_password"]
    res_admin = client.post("/api/login", json={"username": "dca_admin_mgr", "password": admin_pass})
    assert res_admin.status_code == 200
    data_admin = res_admin.json()
    assert "access_token" in data_admin
    assert data_admin["user"]["role"] == "admin"

    # 2. Valid Superuser Login
    super_pass = ACCOUNT_REGISTRY["dca_sys_root"]["raw_initial_password"]
    res_super = client.post("/api/login", json={"username": "dca_sys_root", "password": super_pass})
    assert res_super.status_code == 200
    assert res_super.json()["user"]["role"] == "superuser"

    # 3. Invalid Password
    res_wrong_pass = client.post("/api/login", json={"username": "dca_admin_mgr", "password": "WrongPassword"})
    assert res_wrong_pass.status_code == 401

    # 4. Non-existent User
    res_no_user = client.post("/api/login", json={"username": "ghost_user", "password": "Password123!"})
    assert res_no_user.status_code == 401


def test_superuser_password_reset_protection():
    """Verify that Superuser password CANNOT be reset via API/web interface."""
    admin_jwt = create_system_jwt(username="dca_admin_mgr", role="admin")
    super_jwt = create_system_jwt(username="dca_sys_root", role="superuser")

    # 1. Admin attempting to reset superuser password via API -> 403 Forbidden
    res_admin_reset = client.post(
        "/api/users/dca_sys_root/reset-password",
        json={"new_password": "test_reset_password"},
        headers={"Authorization": f"Bearer {admin_jwt}"},
    )
    assert res_admin_reset.status_code == 403
    assert "direct postgresql database sql command" in res_admin_reset.json()["detail"].lower()

    # 2. Superuser attempting to reset own password via API -> 403 Forbidden
    res_self_reset = client.post(
        "/api/users/dca_sys_root/reset-password",
        json={"new_password": "test_reset_password"},
        headers={"Authorization": f"Bearer {super_jwt}"},
    )
    assert res_self_reset.status_code == 403
    assert "direct postgresql database sql command" in res_self_reset.json()["detail"].lower()


def test_admin_user_management_crud_and_rbac():
    """Test Admin capabilities to create, list, and reset non-superuser user accounts."""
    admin_jwt = create_system_jwt(username="dca_admin_mgr", role="admin")

    # 1. Create new user account
    create_payload = {
        "username": "test_operator_99",
        "password": "test_initial_password",
        "name": "Jane Doe Operator",
        "role": "operator",
        "dept": "Operations Hub",
        "email": "janedoe@rcf-dac.univ.edu.my",
    }
    res_create = client.post("/api/users", json=create_payload, headers={"Authorization": f"Bearer {admin_jwt}"})
    assert res_create.status_code == 201
    assert "test_operator_99" in ACCOUNT_REGISTRY

    # 2. Reset password for created user account
    res_reset = client.post(
        "/api/users/test_operator_99/reset-password",
        json={"new_password": "test_updated_password"},
        headers={"Authorization": f"Bearer {admin_jwt}"},
    )
    assert res_reset.status_code == 200
    assert ACCOUNT_REGISTRY["test_operator_99"]["password_hash"] == hash_password("test_updated_password")

    # 3. List system users
    res_list = client.get("/api/users", headers={"Authorization": f"Bearer {admin_jwt}"})
    assert res_list.status_code == 200
    usernames = [u["username"] for u in res_list.json()["users"]]
    assert "test_operator_99" in usernames
    assert "dca_sys_root" in usernames

    # 4. Delete non-superuser account
    res_delete = client.delete("/api/users/test_operator_99", headers={"Authorization": f"Bearer {admin_jwt}"})
    assert res_delete.status_code == 200
    assert "test_operator_99" not in ACCOUNT_REGISTRY


def test_html_login_and_user_management_views():
    """Test HTML rendering of login and user management pages."""
    res_login_page = client.get("/login")
    assert res_login_page.status_code == 200
    assert "<!DOCTYPE html>" in res_login_page.text
    assert "RCF &amp; DAC System Login" in res_login_page.text or "RCF & DAC System Login" in res_login_page.text

    res_user_mgmt_page = client.get("/user-management")
    assert res_user_mgmt_page.status_code == 200
    assert "<!DOCTYPE html>" in res_user_mgmt_page.text
    assert "User Management Dashboard" in res_user_mgmt_page.text
