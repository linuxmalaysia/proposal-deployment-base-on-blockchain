"""Focused tests for role-based module access and account administration."""

from __future__ import annotations

import copy
import os
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# The application deliberately fails closed at import time without a JWT secret.
os.environ.setdefault("INVESTOR_JWT_SECRET", "test_module_access_secret_2026")

import dca_service.web_app as web_app


client = TestClient(web_app.app)


@pytest.fixture(autouse=True)
def isolate_access_control_state() -> None:
    """Restore mutable in-memory registries and permission mappings after each test."""
    original_accounts = copy.deepcopy(web_app.ACCOUNT_REGISTRY)
    original_assets = copy.deepcopy(web_app.ASSET_REGISTRY)
    original_users = copy.deepcopy(web_app.USER_REGISTRY)
    original_permissions = copy.deepcopy(web_app.ROLE_MODULE_PERMISSIONS)
    original_cache = web_app._INVESTOR_ASSETS_CACHE
    original_cache_timestamp = web_app._INVESTOR_ASSETS_CACHE_TIMESTAMP

    web_app.ROLE_MODULE_PERMISSIONS.clear()
    web_app.ROLE_MODULE_PERMISSIONS.update(
        copy.deepcopy(web_app.DEFAULT_MODULE_PERMISSIONS)
    )
    yield

    web_app.ACCOUNT_REGISTRY.clear()
    web_app.ACCOUNT_REGISTRY.update(original_accounts)
    web_app.ASSET_REGISTRY.clear()
    web_app.ASSET_REGISTRY.update(original_assets)
    web_app.USER_REGISTRY.clear()
    web_app.USER_REGISTRY.update(original_users)
    web_app.ROLE_MODULE_PERMISSIONS.clear()
    web_app.ROLE_MODULE_PERMISSIONS.update(original_permissions)
    web_app._INVESTOR_ASSETS_CACHE = original_cache
    web_app._INVESTOR_ASSETS_CACHE_TIMESTAMP = original_cache_timestamp


def auth_headers(role: str, username: str | None = None) -> dict[str, str]:
    """Return an Authorization header for a signed system-role JWT."""
    subject = username or f"test_{role}"
    token = web_app.create_system_jwt(username=subject, role=role)
    return {"Authorization": f"Bearer {token}"}


def create_user_payload(username: str, role: str) -> dict[str, str]:
    """Build a valid account-creation request body."""
    return {
        "username": username,
        "password": "SecureTestPassword2026!",
        "name": f"Test {role.title()}",
        "role": role,
        "dept": "Test Operations",
        "email": f"{username}@example.edu.my",
    }


ASSET_PAYLOAD = {
    "title": "Access-Controlled Research Asset",
    "trl": 4,
    "abstract": "Evidence used to exercise module access controls.",
    "file_name": "evidence.txt",
    "file_content": "test evidence",
    "content_encoding": "text",
}
CLOVERLEAF_PAYLOAD = {"tech": 45, "market": 60, "comm": 45, "mgmt": 40}
REVENUE_PAYLOAD = {"amount": "100.00", "revenue_type": "licensing"}
REGISTRATION_PAYLOAD = {
    "name": "Dr Test Researcher",
    "role": "Principal Investigator",
    "dept": "Faculty of Engineering",
    "email": "researcher@example.edu.my",
}


@pytest.mark.parametrize(
    ("role", "module_id", "is_mutation", "allowed"),
    [
        ("operator", "module_2", True, True),
        ("operator", "module_3", True, True),
        ("operator", "module_4", False, False),
        ("operator", "module_5", True, False),
        ("investor", "module_2", True, False),
        ("investor", "module_3", True, False),
        ("investor", "module_4", False, True),
        ("investor", "module_5", True, True),
        ("auditor", "module_4", False, True),
        ("auditor", "module_2", True, False),
        ("admin", "module_2", False, False),
        ("superuser", "module_4", False, False),
        ("user", "module_2", False, False),
        ("", "module_2", False, False),
    ],
)
def test_default_module_access_matrix(
    role: str, module_id: str, is_mutation: bool, allowed: bool
) -> None:
    """Enforce the default operator, investor, auditor, and privileged-role matrix."""
    payload = {"role": role}

    if allowed:
        web_app.check_module_access(module_id, payload, is_mutation=is_mutation)
    else:
        with pytest.raises(HTTPException) as exc_info:
            web_app.check_module_access(module_id, payload, is_mutation=is_mutation)
        assert exc_info.value.status_code == 403


def test_privileged_and_auditor_restrictions_override_dynamic_assignments() -> None:
    """Do not let mutable mappings bypass privileged isolation or auditor read-only rules."""
    web_app.ROLE_MODULE_PERMISSIONS["module_2"] = [
        "admin",
        "superuser",
        "auditor",
    ]

    for role in ("admin", "superuser", "auditor"):
        with pytest.raises(HTTPException) as exc_info:
            web_app.check_module_access(
                "module_2", {"role": role}, is_mutation=True
            )
        assert exc_info.value.status_code == 403

    web_app.check_module_access(
        "module_2", {"role": "auditor"}, is_mutation=False
    )


@pytest.mark.parametrize(
    ("method", "path", "body", "allowed_role", "denied_role"),
    [
        ("post", "/api/register-asset", ASSET_PAYLOAD, "operator", "investor"),
        (
            "post",
            "/api/calculate-cloverleaf",
            CLOVERLEAF_PAYLOAD,
            "operator",
            "investor",
        ),
        (
            "post",
            "/api/calculate-revenue",
            REVENUE_PAYLOAD,
            "investor",
            "operator",
        ),
        ("get", "/api/investor-assets", None, "investor", "operator"),
    ],
)
def test_operational_endpoints_apply_their_module_assignments(
    method: str,
    path: str,
    body: dict[str, Any] | None,
    allowed_role: str,
    denied_role: str,
) -> None:
    """Exercise every endpoint that gained a module-level authorisation check."""
    allowed_response = client.request(
        method, path, json=body, headers=auth_headers(allowed_role)
    )
    assert allowed_response.status_code in (200, 201)

    denied_response = client.request(
        method, path, json=body, headers=auth_headers(denied_role)
    )
    assert denied_response.status_code == 403
    assert "not assigned" in denied_response.json()["detail"].lower()


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api/register-user", REGISTRATION_PAYLOAD),
        ("post", "/api/register-asset", ASSET_PAYLOAD),
        ("post", "/api/calculate-cloverleaf", CLOVERLEAF_PAYLOAD),
        ("post", "/api/calculate-revenue", REVENUE_PAYLOAD),
        ("get", "/api/investor-assets", None),
    ],
)
def test_newly_protected_endpoints_fail_closed_without_authentication(
    method: str, path: str, body: dict[str, Any] | None
) -> None:
    """Require a valid session before running any protected module operation."""
    response = client.request(method, path, json=body)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_operational_endpoint_accepts_httponly_session_cookie() -> None:
    """Keep browser cookie authentication working on newly protected endpoints."""
    token = web_app.create_system_jwt(username="cookie_operator", role="operator")

    response = client.post(
        "/api/calculate-cloverleaf",
        json=CLOVERLEAF_PAYLOAD,
        headers={"Cookie": f"rcf_dac_jwt={token}"},
    )

    assert response.status_code == 200
    assert response.json()["total_score"] == 190


@pytest.mark.parametrize("role", ["admin", "superuser"])
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api/register-asset", ASSET_PAYLOAD),
        ("post", "/api/calculate-cloverleaf", CLOVERLEAF_PAYLOAD),
        ("post", "/api/calculate-revenue", REVENUE_PAYLOAD),
        ("get", "/api/investor-assets", None),
    ],
)
def test_privileged_roles_are_isolated_from_all_operational_endpoints(
    role: str, method: str, path: str, body: dict[str, Any] | None
) -> None:
    """Keep admin and superuser sessions out of all operational modules."""
    response = client.request(method, path, json=body, headers=auth_headers(role))

    assert response.status_code == 403
    assert "cannot access operational module" in response.json()["detail"].lower()


def test_auditor_can_read_assets_but_cannot_mutate_any_module() -> None:
    """Apply the auditor read-only exception consistently at endpoint boundaries."""
    headers = auth_headers("auditor")

    assert client.get("/api/investor-assets", headers=headers).status_code == 200
    for path, body in (
        ("/api/register-asset", ASSET_PAYLOAD),
        ("/api/calculate-cloverleaf", CLOVERLEAF_PAYLOAD),
        ("/api/calculate-revenue", REVENUE_PAYLOAD),
    ):
        response = client.post(path, json=body, headers=headers)
        assert response.status_code == 403
        assert "read-only" in response.json()["detail"].lower()


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [("admin", 200), ("superuser", 200), ("operator", 403), ("investor", 403)],
)
def test_role_assignments_are_readable_only_by_privileged_roles(
    role: str, expected_status: int
) -> None:
    """Restrict permission-map disclosure to administrators and superusers."""
    response = client.get("/api/role-assignments", headers=auth_headers(role))

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["module_permissions"] == web_app.DEFAULT_MODULE_PERMISSIONS


def test_role_assignments_require_authentication() -> None:
    """Fail closed when permission mappings are requested without a session."""
    response = client.get("/api/role-assignments")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("role", ["superuser", "operator", "investor", "auditor"])
def test_only_admin_can_update_role_assignments(role: str) -> None:
    """Prevent every non-admin role, including superuser, from changing mappings."""
    response = client.post(
        "/api/role-assignments",
        json={"module_permissions": {"module_2": ["investor"]}},
        headers=auth_headers(role),
    )

    assert response.status_code == 403
    assert web_app.ROLE_MODULE_PERMISSIONS["module_2"] == ["operator"]


def test_admin_update_normalises_roles_and_preserves_module_1_lock() -> None:
    """Normalise submitted roles while keeping DID minting admin-only."""
    response = client.post(
        "/api/role-assignments",
        json={
            "module_permissions": {
                "module_1": ["operator", "investor"],
                "module_2": [" Investor ", "AUDITOR"],
            }
        },
        headers=auth_headers("admin"),
    )

    assert response.status_code == 200
    permissions = response.json()["module_permissions"]
    assert permissions["module_1"] == ["admin"]
    assert permissions["module_2"] == ["investor", "auditor"]
    assert response.json()["updated_by"] == "test_admin"


def test_invalid_module_update_is_rejected_without_changing_permissions() -> None:
    """Reject unknown module identifiers and retain the existing access map."""
    permissions_before = copy.deepcopy(web_app.ROLE_MODULE_PERMISSIONS)

    response = client.post(
        "/api/role-assignments",
        json={"module_permissions": {"module_99": ["operator"]}},
        headers=auth_headers("admin"),
    )

    assert response.status_code == 422
    assert "invalid module id" in response.json()["detail"].lower()
    assert web_app.ROLE_MODULE_PERMISSIONS == permissions_before


def test_updated_mapping_takes_effect_on_the_next_request() -> None:
    """Apply runtime permission updates immediately at protected endpoints."""
    update_response = client.post(
        "/api/role-assignments",
        json={"module_permissions": {"module_2": ["investor"]}},
        headers=auth_headers("admin"),
    )
    assert update_response.status_code == 200

    operator_response = client.post(
        "/api/register-asset",
        json=ASSET_PAYLOAD,
        headers=auth_headers("operator"),
    )
    investor_response = client.post(
        "/api/register-asset",
        json=ASSET_PAYLOAD,
        headers=auth_headers("investor"),
    )

    assert operator_response.status_code == 403
    assert investor_response.status_code == 201


@pytest.mark.parametrize("role", ["superuser", "operator", "investor", "auditor"])
def test_did_registration_remains_admin_only(role: str) -> None:
    """Deny Module 1 registration to every authenticated non-admin role."""
    response = client.post(
        "/api/register-user",
        json=REGISTRATION_PAYLOAD,
        headers=auth_headers(role),
    )

    assert response.status_code == 403
    assert "restricted strictly to administrator" in response.json()["detail"].lower()


def test_admin_can_register_did_after_module_1_reassignment_attempt() -> None:
    """Regression: submitted Module 1 roles cannot displace administrator access."""
    update_response = client.post(
        "/api/role-assignments",
        json={"module_permissions": {"module_1": ["operator"]}},
        headers=auth_headers("admin"),
    )
    assert update_response.status_code == 200
    assert update_response.json()["module_permissions"]["module_1"] == ["admin"]

    registration_response = client.post(
        "/api/register-user",
        json=REGISTRATION_PAYLOAD,
        headers=auth_headers("admin"),
    )
    assert registration_response.status_code == 201


def test_user_management_page_exposes_role_specific_controls() -> None:
    """Render separate Module 1 and account-role controls for admin and superuser."""
    response = client.get("/user-management")

    assert response.status_code == 200
    assert 'id="module1Card"' in response.text
    assert 'id="module1SuperNotice"' in response.text
    assert "callerRole === 'admin'" in response.text
    assert "callerRole === 'superuser'" in response.text
    assert '<option value="admin">admin</option>' in response.text
    assert "Superuser, you can ONLY create user accounts" in response.text


@pytest.mark.parametrize(
    ("caller_role", "target_role", "expected_status", "stored_role"),
    [
        ("admin", "operator", 201, "operator"),
        ("admin", " Investor ", 201, "investor"),
        ("admin", " SUPERUSER ", 403, None),
        ("superuser", " ADMIN ", 201, "admin"),
        ("superuser", "operator", 403, None),
        ("operator", "operator", 403, None),
    ],
)
def test_account_creation_role_policy_and_normalisation(
    caller_role: str,
    target_role: str,
    expected_status: int,
    stored_role: str | None,
) -> None:
    """Enforce asymmetric admin/superuser creation rules after role normalisation."""
    username = f"created_{caller_role}_{target_role.strip().lower()}"
    response = client.post(
        "/api/users",
        json=create_user_payload(username, target_role),
        headers=auth_headers(caller_role),
    )

    assert response.status_code == expected_status
    if stored_role is None:
        assert username not in web_app.ACCOUNT_REGISTRY
    else:
        assert response.json()["user"]["role"] == stored_role
        assert web_app.ACCOUNT_REGISTRY[username]["role"] == stored_role


def test_duplicate_account_conflict_does_not_expose_or_replace_password() -> None:
    """Keep the original account intact and password material out of public responses."""
    username = "duplicate_operator"
    payload = create_user_payload(username, "operator")
    headers = auth_headers("admin")

    created_response = client.post("/api/users", json=payload, headers=headers)
    assert created_response.status_code == 201
    original_hash = web_app.ACCOUNT_REGISTRY[username]["password_hash"]
    assert "password" not in created_response.text.lower()

    duplicate_payload = {**payload, "password": "ReplacementPassword2026!"}
    duplicate_response = client.post(
        "/api/users", json=duplicate_payload, headers=headers
    )

    assert duplicate_response.status_code == 409
    assert web_app.ACCOUNT_REGISTRY[username]["password_hash"] == original_hash

    listed_user = next(
        user
        for user in client.get("/api/users", headers=headers).json()["users"]
        if user["username"] == username
    )
    assert "password" not in " ".join(listed_user).lower()
