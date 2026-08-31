"""Focused unit tests for RBAC authentication and user management."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from typing import Any

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("INVESTOR_JWT_SECRET", "test-suite-only-jwt-secret")

from dca_service import web_app


@pytest.fixture(autouse=True)
def isolate_account_registry() -> None:
    """Restore the in-memory account registry after each test."""
    original = copy.deepcopy(web_app.ACCOUNT_REGISTRY)
    yield
    web_app.ACCOUNT_REGISTRY.clear()
    web_app.ACCOUNT_REGISTRY.update(original)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(web_app.app)


def bearer_headers(role: str, username: str = "requesting-user") -> dict[str, str]:
    """Build an authorization header for a system role."""
    token = web_app.create_system_jwt(username=username, role=role)
    return {"Authorization": f"Bearer {token}"}


def create_user_payload(username: str = "new_operator") -> dict[str, str]:
    """Return a valid user-creation request body."""
    return {
        "username": username,
        "password": "unit-test-initial-credential",
        "name": "New Operations User",
        "role": "OpErAtOr",
        "dept": "Operations",
        "email": f"{username}@example.com",
    }


def decode_payload(token: str) -> dict[str, Any]:
    """Decode claims from a token created by the application."""
    payload_segment = token.split(".")[1]
    return json.loads(web_app.base64url_decode(payload_segment))


def test_password_hashing_uses_scrypt_unique_salts_and_legacy_compatibility() -> None:
    credential = "unit-test-password-material"

    first_hash = web_app.hash_password(credential)
    second_hash = web_app.hash_password(credential)

    assert first_hash.startswith("scrypt$")
    assert second_hash.startswith("scrypt$")
    assert first_hash != second_hash
    assert web_app.verify_password(credential, first_hash) is True
    assert web_app.verify_password("incorrect-test-value", first_hash) is False
    assert web_app.verify_password(credential, "scrypt$malformed") is False

    legacy_hash = hashlib.sha256(
        f"{web_app.PASSWORD_SALT}:{credential}".encode()
    ).hexdigest()
    assert web_app.verify_password(credential, legacy_hash) is True
    assert web_app.verify_password("incorrect-test-value", legacy_hash) is False


@pytest.mark.parametrize(
    ("role", "is_admin", "is_accredited"),
    [
        ("operator", False, False),
        ("investor", False, True),
        ("admin", True, True),
        ("superuser", True, True),
    ],
)
def test_system_jwt_contains_role_appropriate_authorisation_claims(
    role: str, is_admin: bool, is_accredited: bool
) -> None:
    token = web_app.create_system_jwt("claims-user", role)

    assert len(token.split(".")) == 3
    payload = decode_payload(token)
    assert payload["sub"] == "claims-user"
    assert payload["username"] == "claims-user"
    assert payload["role"] == role
    assert payload["admin"] is is_admin
    assert payload["accredited_investor"] is is_accredited
    assert payload["iss"] == web_app.EXPECTED_ISSUER
    assert payload["aud"] == web_app.EXPECTED_AUDIENCE


def test_user_listing_requires_admin_and_redacts_credentials(client: TestClient) -> None:
    unauthenticated = client.get("/api/users")
    investor = client.get("/api/users", headers=bearer_headers("investor"))
    authorised = client.get(
        "/api/users", headers=bearer_headers("admin", "dca_admin_mgr")
    )

    assert unauthenticated.status_code == 401
    assert unauthenticated.headers["www-authenticate"] == "Bearer"
    assert investor.status_code == 403
    assert authorised.status_code == 200
    body = authorised.json()
    assert body["total"] == len(web_app.ACCOUNT_REGISTRY)
    assert body["requested_by"] == "dca_admin_mgr"
    assert all("password_hash" not in user for user in body["users"])
    assert all("raw_initial_password" not in user for user in body["users"])
    superuser = next(user for user in body["users"] if user["role"] == "superuser")
    assert superuser["superuser_protected"] is True


def test_admin_creates_normalised_user_without_exposing_password(
    client: TestClient,
) -> None:
    payload = create_user_payload()

    response = client.post(
        "/api/users", json=payload, headers=bearer_headers("admin", "dca_admin_mgr")
    )

    assert response.status_code == 201
    returned_user = response.json()["user"]
    stored_user = web_app.ACCOUNT_REGISTRY[payload["username"]]
    assert returned_user["role"] == "operator"
    assert "password" not in response.text.lower()
    assert stored_user["password_hash"] != payload["password"]
    assert web_app.verify_password(payload["password"], stored_user["password_hash"])
    assert stored_user["did"].startswith("did:univ:acct-")


def test_user_creation_rejects_duplicates_and_superuser_role(
    client: TestClient,
) -> None:
    headers = bearer_headers("admin")
    duplicate = create_user_payload("dca_operator_01")
    original = copy.deepcopy(web_app.ACCOUNT_REGISTRY["dca_operator_01"])

    duplicate_response = client.post("/api/users", json=duplicate, headers=headers)
    protected_payload = create_user_payload("another_root")
    protected_payload["role"] = "SUPERUSER"
    protected_response = client.post(
        "/api/users", json=protected_payload, headers=headers
    )

    assert duplicate_response.status_code == 409
    assert web_app.ACCOUNT_REGISTRY["dca_operator_01"] == original
    assert protected_response.status_code == 403
    assert "another_root" not in web_app.ACCOUNT_REGISTRY


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api/users", create_user_payload("forbidden_create")),
        (
            "post",
            "/api/users/dca_operator_01/reset-password",
            {"new_password": "forbidden-reset-value"},
        ),
        ("delete", "/api/users/dca_operator_01", None),
    ],
)
def test_non_administrator_cannot_mutate_accounts(
    client: TestClient, method: str, path: str, body: dict[str, str] | None
) -> None:
    before = copy.deepcopy(web_app.ACCOUNT_REGISTRY)

    response = client.request(
        method, path, json=body, headers=bearer_headers("investor")
    )

    assert response.status_code == 403
    assert web_app.ACCOUNT_REGISTRY == before


def test_password_reset_rotates_hash_and_login_credentials(client: TestClient) -> None:
    payload = create_user_payload("rotation_user")
    headers = bearer_headers("admin", "dca_admin_mgr")
    client.post("/api/users", json=payload, headers=headers)
    old_hash = web_app.ACCOUNT_REGISTRY["rotation_user"]["password_hash"]

    reset_response = client.post(
        "/api/users/rotation_user/reset-password",
        json={"new_password": "unit-test-rotated-credential"},
        headers=headers,
    )
    old_login = client.post(
        "/api/login",
        json={"username": "rotation_user", "password": payload["password"]},
    )
    new_login = client.post(
        "/api/login",
        json={
            "username": "rotation_user",
            "password": "unit-test-rotated-credential",
        },
    )

    assert reset_response.status_code == 200
    assert reset_response.json()["reset_by"] == "dca_admin_mgr"
    assert web_app.ACCOUNT_REGISTRY["rotation_user"]["password_hash"] != old_hash
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert new_login.json()["user"]["username"] == "rotation_user"


def test_reset_and_delete_report_missing_users_without_mutation(
    client: TestClient,
) -> None:
    headers = bearer_headers("admin")
    before = copy.deepcopy(web_app.ACCOUNT_REGISTRY)

    reset = client.post(
        "/api/users/missing-user/reset-password",
        json={"new_password": "unused-test-value"},
        headers=headers,
    )
    delete = client.delete("/api/users/missing-user", headers=headers)

    assert reset.status_code == 404
    assert delete.status_code == 404
    assert web_app.ACCOUNT_REGISTRY == before


def test_deleting_user_revokes_password_login(client: TestClient) -> None:
    payload = create_user_payload("deletion_user")
    headers = bearer_headers("admin", "dca_admin_mgr")
    client.post("/api/users", json=payload, headers=headers)

    response = client.delete("/api/users/deletion_user", headers=headers)
    login = client.post(
        "/api/login",
        json={"username": "deletion_user", "password": payload["password"]},
    )

    assert response.status_code == 200
    assert response.json()["deleted_by"] == "dca_admin_mgr"
    assert "deletion_user" not in web_app.ACCOUNT_REGISTRY
    assert login.status_code == 401


@pytest.mark.parametrize("action", ["reset", "delete"])
def test_superuser_remains_protected_from_account_mutations(
    client: TestClient, action: str
) -> None:
    before = copy.deepcopy(web_app.ACCOUNT_REGISTRY["dca_sys_root"])
    headers = bearer_headers("superuser", "dca_sys_root")

    if action == "reset":
        response = client.post(
            "/api/users/dca_sys_root/reset-password",
            json={"new_password": "forbidden-superuser-value"},
            headers=headers,
        )
    else:
        response = client.delete("/api/users/dca_sys_root", headers=headers)

    assert response.status_code == 403
    assert web_app.ACCOUNT_REGISTRY["dca_sys_root"] == before
