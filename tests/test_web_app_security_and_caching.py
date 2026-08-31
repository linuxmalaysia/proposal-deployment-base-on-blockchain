"""Focused regression tests for web session security, RBAC, caching, and metrics."""

from __future__ import annotations

import copy
import os
from http.cookies import SimpleCookie
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

os.environ.setdefault("INVESTOR_JWT_SECRET", "test_rcf_dac_jwt_secret_key_2026")

from dca_service import web_app


@pytest.fixture(autouse=True)
def isolate_web_app_state(monkeypatch: pytest.MonkeyPatch):
    """Keep mutable registries, caches, metrics, and environment isolated per test."""
    accounts = copy.deepcopy(web_app.ACCOUNT_REGISTRY)
    assets = copy.deepcopy(web_app.ASSET_REGISTRY)
    cache_state = (
        web_app._DB_STATUS_CACHE,
        web_app._DB_STATUS_CACHE_TIMESTAMP,
        web_app._INVESTOR_ASSETS_CACHE,
        web_app._INVESTOR_ASSETS_CACHE_TIMESTAMP,
    )

    for key in (
        "COOKIE_SECURE",
        "DATABASE_URL",
        "SUPABASE_DB_HOST",
        "SUPABASE_DB_PASSWORD",
        "SUPABASE_JWKS_URL",
        "SUPABASE_POOLER_HOST",
        "SUPABASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)

    web_app._DB_STATUS_CACHE = None
    web_app._DB_STATUS_CACHE_TIMESTAMP = 0.0
    web_app._INVESTOR_ASSETS_CACHE = None
    web_app._INVESTOR_ASSETS_CACHE_TIMESTAMP = 0.0
    monkeypatch.setattr(web_app, "DB_POOL_METRICS", web_app.ConnectionPoolMetrics())

    yield

    web_app.ACCOUNT_REGISTRY.clear()
    web_app.ACCOUNT_REGISTRY.update(accounts)
    web_app.ASSET_REGISTRY.clear()
    web_app.ASSET_REGISTRY.update(assets)
    (
        web_app._DB_STATUS_CACHE,
        web_app._DB_STATUS_CACHE_TIMESTAMP,
        web_app._INVESTOR_ASSETS_CACHE,
        web_app._INVESTOR_ASSETS_CACHE_TIMESTAMP,
    ) = cache_state


@pytest.fixture
def client() -> TestClient:
    """Provide a cookie-isolated client for each test."""
    with TestClient(web_app.app) as test_client:
        yield test_client


def auth_header(role: str, username: str | None = None) -> dict[str, str]:
    """Build an Authorization header for a signed system-role token."""
    token = web_app.create_system_jwt(username or f"test_{role}", role)
    return {"Authorization": f"Bearer {token}"}


def user_payload(username: str = "new_operator", role: str = "operator") -> dict[str, str]:
    """Return a valid user-management request body."""
    return {
        "username": username,
        "password": "InitialPassword123!",
        "name": "Test Operator",
        "role": role,
        "dept": "Operations",
        "email": f"{username}@example.edu.my",
    }


@pytest.mark.parametrize("secure, expected", [(False, False), (True, True)])
def test_login_cookie_has_all_required_security_attributes(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    secure: bool,
    expected: bool,
) -> None:
    """Login must emit a scoped HttpOnly, SameSite cookie with configurable Secure."""
    monkeypatch.setenv("COOKIE_SECURE", str(secure).lower())
    web_app.ACCOUNT_REGISTRY["dca_admin_mgr"]["password_hash"] = web_app.hash_password(
        "ValidAdminPassword123!"
    )

    response = client.post(
        "/api/login",
        json={"username": "dca_admin_mgr", "password": "ValidAdminPassword123!"},
    )

    assert response.status_code == 200
    cookies = SimpleCookie()
    cookies.load(response.headers["set-cookie"])
    session = cookies["rcf_dac_jwt"]
    assert session.value == response.json()["access_token"]
    assert bool(session["httponly"]) is True
    assert bool(session["secure"]) is expected
    assert session["samesite"].lower() == "lax"
    assert session["max-age"] == "3600"
    assert session["path"] == "/"


def test_cookie_session_round_trip_and_logout_deletes_cookie(client: TestClient) -> None:
    """A browser cookie authenticates requests and is expired by logout."""
    web_app.ACCOUNT_REGISTRY["dca_admin_mgr"]["password_hash"] = web_app.hash_password(
        "ValidAdminPassword123!"
    )
    login = client.post(
        "/api/login",
        json={"username": "dca_admin_mgr", "password": "ValidAdminPassword123!"},
    )
    assert login.status_code == 200

    users = client.get("/api/users")
    assert users.status_code == 200
    assert users.json()["requested_by"] == "dca_admin_mgr"

    logout = client.post("/api/logout")
    assert logout.status_code == 200
    deleted = SimpleCookie()
    deleted.load(logout.headers["set-cookie"])
    assert deleted["rcf_dac_jwt"]["max-age"] == "0"
    assert client.cookies.get("rcf_dac_jwt") is None
    assert client.get("/api/users").status_code == 401


def test_authorization_header_takes_precedence_over_admin_cookie(client: TestClient) -> None:
    """An unrelated cookie must not override an explicitly supplied bearer identity."""
    web_app.ACCOUNT_REGISTRY["dca_admin_mgr"]["password_hash"] = web_app.hash_password(
        "ValidAdminPassword123!"
    )
    login = client.post(
        "/api/login",
        json={"username": "dca_admin_mgr", "password": "ValidAdminPassword123!"},
    )
    assert login.status_code == 200

    response = client.get("/api/users", headers=auth_header("investor"))

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_extract_current_user_payload_falls_back_to_request_cookie() -> None:
    """The authentication helper supports callers that pass only a Starlette request."""
    token = web_app.create_system_jwt("cookie_admin", "admin")
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/users",
            "headers": [(b"cookie", f"rcf_dac_jwt={token}".encode())],
        }
    )

    payload = web_app.extract_current_user_payload(request=request)

    assert payload["sub"] == "cookie_admin"
    assert payload["role"] == "admin"


def test_user_listing_never_exposes_password_hashes(client: TestClient) -> None:
    """Administrative listings return public fields and mark the protected account."""
    response = client.get("/api/users", headers=auth_header("admin"))

    assert response.status_code == 200
    users = response.json()["users"]
    assert users
    assert all("password_hash" not in account for account in users)
    superuser = next(account for account in users if account["role"] == "superuser")
    assert superuser["superuser_protected"] is True


@pytest.mark.parametrize(
    "method, path, body",
    [
        ("post", "/api/users", user_payload(),),
        (
            "post",
            "/api/users/dca_operator_01/reset-password",
            {"new_password": "ReplacementPassword123!"},
        ),
        ("delete", "/api/users/dca_operator_01", None),
    ],
)
def test_non_administrators_cannot_mutate_accounts(
    client: TestClient,
    method: str,
    path: str,
    body: dict[str, str] | None,
) -> None:
    """Operator tokens cannot create, reset, or delete accounts."""
    before = copy.deepcopy(web_app.ACCOUNT_REGISTRY)

    response = client.request(method, path, json=body, headers=auth_header("operator"))

    assert response.status_code == 403
    assert web_app.ACCOUNT_REGISTRY == before


@pytest.mark.parametrize(
    "payload, expected_status",
    [
        (user_payload("dca_operator_01"), 409),
        (user_payload("forbidden_root", "superuser"), 403),
    ],
)
def test_create_user_rejects_duplicate_and_superuser_accounts_without_mutation(
    client: TestClient,
    payload: dict[str, str],
    expected_status: int,
) -> None:
    """The API cannot overwrite an account or establish a new superuser."""
    before = copy.deepcopy(web_app.ACCOUNT_REGISTRY)

    response = client.post("/api/users", json=payload, headers=auth_header("admin"))

    assert response.status_code == expected_status
    assert web_app.ACCOUNT_REGISTRY == before


@pytest.mark.parametrize(
    "method, path, body, expected_status",
    [
        (
            "post",
            "/api/users/missing-user/reset-password",
            {"new_password": "ReplacementPassword123!"},
            404,
        ),
        ("delete", "/api/users/missing-user", None, 404),
        (
            "post",
            "/api/users/dca_sys_root/reset-password",
            {"new_password": "ReplacementPassword123!"},
            403,
        ),
        ("delete", "/api/users/dca_sys_root", None, 403),
    ],
)
def test_account_mutations_preserve_missing_and_superuser_accounts(
    client: TestClient,
    method: str,
    path: str,
    body: dict[str, str] | None,
    expected_status: int,
) -> None:
    """Missing targets are reported and the protected superuser remains unchanged."""
    before = copy.deepcopy(web_app.ACCOUNT_REGISTRY)

    response = client.request(method, path, json=body, headers=auth_header("admin"))

    assert response.status_code == expected_status
    assert web_app.ACCOUNT_REGISTRY == before


def test_connection_pool_metrics_cover_success_failure_queries_and_utilisation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Metrics summarise configured bounds, attempts, latency, and query volume."""
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "8")
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "2")
    metrics = web_app.ConnectionPoolMetrics()
    metrics.active_connections = 3
    metrics.record_connection_attempt(10.0, True)
    metrics.record_connection_attempt(90.0, False)
    metrics.record_connection_attempt(20.0, True)
    metrics.record_query()
    metrics.record_query()

    result = metrics.to_dict()

    assert result["max_pool_size"] == 8
    assert result["min_pool_size"] == 2
    assert result["total_connections_acquired"] == 3
    assert result["failed_connection_attempts"] == 1
    assert result["avg_checkout_latency_ms"] == 10.0
    assert result["total_queries_executed"] == 2
    assert result["pool_utilization_percent"] == 37.5
    assert result["timestamp"].endswith("Z")


def test_connection_pool_metrics_handle_empty_and_zero_sized_pool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty metrics avoid division errors even when the configured maximum is zero."""
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "0")
    metrics = web_app.ConnectionPoolMetrics()
    metrics.active_connections = 1

    result = metrics.to_dict()

    assert result["avg_checkout_latency_ms"] == 0.0
    assert result["pool_utilization_percent"] == 0.0


def test_database_diagnostic_records_query_and_includes_metric_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fresh status probe records its catalogue query before serialising metrics."""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = [("users",)]
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        MagicMock(return_value=(connection, "Connected to PostgreSQL")),
    )

    result = web_app.check_database_connection(bypass_cache=True)

    assert result["cached"] is False
    assert result["pool_metrics"]["total_queries_executed"] == 1
    assert web_app.DB_POOL_METRICS.total_queries == 1


@pytest.mark.parametrize("query", ["bypass_cache=true", "force=true"])
def test_database_status_query_parameters_force_a_fresh_probe(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    query: str,
) -> None:
    """Both documented query aliases bypass the database status cache."""
    check = MagicMock(return_value={"cached": False})
    monkeypatch.setattr(web_app, "check_database_connection", check)

    response = client.get(f"/api/db-status?{query}")

    assert response.status_code == 200
    check.assert_called_once_with(bypass_cache=True)


def test_investor_asset_cache_supports_hits_bypass_and_expiry(client: TestClient) -> None:
    """Investor listings refresh when bypassed or when their TTL has elapsed."""
    headers = auth_header("investor")

    fresh = client.get("/api/investor-assets", headers=headers)
    cached = client.get("/api/investor-assets", headers=headers)
    bypassed = client.get("/api/investor-assets?bypass_cache=true", headers=headers)
    web_app._INVESTOR_ASSETS_CACHE_TIMESTAMP -= web_app.INVESTOR_ASSETS_CACHE_TTL + 0.01
    expired = client.get("/api/investor-assets", headers=headers)

    assert fresh.json()["cached"] is False
    assert cached.json()["cached"] is True
    assert bypassed.json()["cached"] is False
    assert expired.json()["cached"] is False


def test_cached_investor_assets_are_authorised_before_cache_lookup(client: TestClient) -> None:
    """A populated cache must not let a non-investor role read investor listings."""
    assert client.get(
        "/api/investor-assets", headers=auth_header("investor")
    ).status_code == 200

    response = client.get("/api/investor-assets", headers=auth_header("admin"))

    assert response.status_code == 403
    assert "investor role required" in response.json()["detail"].lower()
