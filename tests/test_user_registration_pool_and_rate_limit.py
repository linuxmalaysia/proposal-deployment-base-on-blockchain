"""Focused tests for the user-management, async-pool, and rate-limit PR changes."""

from __future__ import annotations

import asyncio
import concurrent.futures
import os
import sys
from types import SimpleNamespace
from typing import Any, Callable
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("INVESTOR_JWT_SECRET", "test_rcf_dac_jwt_secret_key_2026")

from dca_service import web_app


ASYNC_DATABASE_ENV_KEYS = (
    "DATABASE_URL",
    "SUPABASE_DB_HOST",
    "SUPABASE_DB_PASSWORD",
    "SUPABASE_POOLER_HOST",
    "SUPABASE_URL",
)


def _authorisation_header(username: str, role: str) -> dict[str, str]:
    """Build an API authorisation header using the application's JWT issuer."""
    token = web_app.create_system_jwt(username=username, role=role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def isolate_changed_global_state(monkeypatch: pytest.MonkeyPatch):
    """Keep changed in-memory service state independent between tests."""
    original_pool = web_app.ASYNC_DB_POOL
    original_assets = dict(web_app.ASSET_REGISTRY)
    web_app.ASYNC_DB_POOL = None
    web_app.RATE_LIMIT_BUCKETS.clear()
    monkeypatch.setattr(web_app, "_INVESTOR_ASSETS_CACHE", None)
    monkeypatch.setattr(web_app, "_INVESTOR_ASSETS_CACHE_TIMESTAMP", 0.0)
    for key in ASYNC_DATABASE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    yield

    web_app.ASYNC_DB_POOL = original_pool
    web_app.RATE_LIMIT_BUCKETS.clear()
    web_app.ASSET_REGISTRY.clear()
    web_app.ASSET_REGISTRY.update(original_assets)


def install_fake_async_pool(
    monkeypatch: pytest.MonkeyPatch, pool_factory: MagicMock
) -> None:
    """Install a minimal psycopg-pool substitute for lifecycle unit tests."""
    monkeypatch.setitem(
        sys.modules,
        "psycopg_pool",
        SimpleNamespace(AsyncConnectionPool=pool_factory),
    )


def run_in_thread(coro_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Execute an async coroutine function in an isolated background thread."""
    def runner() -> Any:
        return asyncio.run(coro_fn(*args, **kwargs))
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(runner).result()


def test_init_async_pool_opens_explicit_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit DATABASE_URL should be used without Supabase URL rewriting."""
    pool = SimpleNamespace(open=AsyncMock(), close=AsyncMock())
    pool_factory = MagicMock(return_value=pool)
    install_fake_async_pool(monkeypatch, pool_factory)
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured.example/app?sslmode=verify-full")
    monkeypatch.setenv("SUPABASE_POOLER_HOST", "ignored.example")
    monkeypatch.setattr(web_app.DB_POOL_METRICS, "max_pool_size", 7)

    result = run_in_thread(web_app.init_async_connection_pool)

    assert result is pool
    assert web_app.ASYNC_DB_POOL is pool
    pool_factory.assert_called_once_with(
        conninfo="postgresql://configured.example/app?sslmode=verify-full",
        min_size=1,
        max_size=7,
        open=False,
    )
    pool.open.assert_awaited_once_with()


@pytest.mark.parametrize("host_key", ["SUPABASE_POOLER_HOST", "SUPABASE_DB_HOST"])
def test_init_async_pool_builds_url_from_supabase_configuration(
    monkeypatch: pytest.MonkeyPatch, host_key: str, tmp_path: Path
) -> None:
    """Either supported Supabase host variable should enable pool initialisation."""
    ca_file = tmp_path / "prod-supabase-ca.crt"
    ca_file.write_bytes(b"PEM CA CERT")
    pool = SimpleNamespace(open=AsyncMock(), close=AsyncMock())
    pool_factory = MagicMock(return_value=pool)
    install_fake_async_pool(monkeypatch, pool_factory)
    monkeypatch.setenv(host_key, "pooler.example.supabase.com")
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "p@ss word/+")
    monkeypatch.setenv("SUPABASE_SSLROOTCERT", str(ca_file))

    result = run_in_thread(web_app.init_async_connection_pool)

    assert result is pool
    assert "sslmode=verify-full" in pool_factory.call_args.kwargs["conninfo"]
    pool.open.assert_awaited_once_with()


@pytest.mark.parametrize(
    ("configured_values",),
    [
        ({},),
        ({"SUPABASE_POOLER_HOST": "pooler.example.supabase.com"},),
        (
            {
                "SUPABASE_POOLER_HOST": "pooler.example.supabase.com",
                "SUPABASE_URL": "https://project-ref.supabase.co",
            },
        ),
    ],
)
def test_init_async_pool_skips_missing_or_partial_configuration(
    monkeypatch: pytest.MonkeyPatch, configured_values: dict[str, str]
) -> None:
    """No pool should be constructed until all derived-URL settings exist."""
    pool_factory = MagicMock()
    install_fake_async_pool(monkeypatch, pool_factory)
    for key, value in configured_values.items():
        monkeypatch.setenv(key, value)

    result = run_in_thread(web_app.init_async_connection_pool)

    assert result is None
    assert web_app.ASYNC_DB_POOL is None
    pool_factory.assert_not_called()


def test_init_async_pool_fails_safely_when_opening_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed pool open must not leave a stale pool available to the app."""
    pool = SimpleNamespace(
        open=AsyncMock(side_effect=RuntimeError("database unavailable")),
        close=AsyncMock(),
    )
    pool_factory = MagicMock(return_value=pool)
    install_fake_async_pool(monkeypatch, pool_factory)
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured.example/app?sslmode=verify-full")
    web_app.ASYNC_DB_POOL = object()

    result = run_in_thread(web_app.init_async_connection_pool)

    assert result is None
    assert web_app.ASYNC_DB_POOL is None
    pool.open.assert_awaited_once_with()


@pytest.mark.parametrize("close_error", [None, RuntimeError("shutdown failed")])
def test_close_async_pool_always_clears_global_reference(close_error: Exception | None) -> None:
    """Successful and failed shutdowns must both make the closed pool unreachable."""
    pool = SimpleNamespace(close=AsyncMock(side_effect=close_error))
    web_app.ASYNC_DB_POOL = pool

    run_in_thread(web_app.close_async_connection_pool)

    pool.close.assert_awaited_once_with()
    assert web_app.ASYNC_DB_POOL is None


def test_connection_pool_metrics_report_success_failure_query_and_utilisation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Metrics should expose accurate counters, rounded latency, and utilisation."""
    monkeypatch.setenv("DB_POOL_MAX_SIZE", "8")
    monkeypatch.setenv("DB_POOL_MIN_SIZE", "2")
    metrics = web_app.ConnectionPoolMetrics()
    metrics.active_connections = 3

    metrics.record_connection_attempt(10.125, True)
    metrics.record_connection_attempt(20.125, True)
    metrics.record_connection_attempt(99.0, False)
    metrics.record_query()
    metrics.record_query()

    result = metrics.to_dict()

    assert result == {
        "max_pool_size": 8,
        "min_pool_size": 2,
        "total_connections_acquired": 2,
        "failed_connection_attempts": 1,
        "avg_checkout_latency_ms": 15.12,
        "total_queries_executed": 2,
        "pool_utilization_percent": 37.5,
        "timestamp": result["timestamp"],
    }
    assert result["timestamp"].endswith("Z")


@pytest.mark.parametrize("close_error", [None, RuntimeError("close failed")])
@pytest.mark.parametrize("initial_active", [0, 1])
def test_close_postgresql_connection_never_leaves_negative_active_count(
    monkeypatch: pytest.MonkeyPatch,
    close_error: Exception | None,
    initial_active: int,
) -> None:
    """Connection accounting must be released once and never fall below zero."""
    metrics = web_app.ConnectionPoolMetrics()
    metrics.active_connections = initial_active
    monkeypatch.setattr(web_app, "DB_POOL_METRICS", metrics)
    monkeypatch.setattr("dca_service.adapters.database_api.DB_POOL_METRICS", metrics)
    monkeypatch.setattr("dca_service.adapters.database_api.SYNC_DB_POOL", None)
    connection = MagicMock()
    connection.close.side_effect = close_error

    web_app.close_postgresql_connection(connection)

    connection.close.assert_called_once_with()
    assert metrics.active_connections == max(0, initial_active - 1)


def test_lifespan_initialises_and_closes_pool_around_application_use(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The FastAPI lifespan should own both ends of the async pool lifecycle."""
    events: list[str] = []

    async def initialise() -> object:
        events.append("initialise")
        return object()

    async def close() -> None:
        events.append("close")

    monkeypatch.setattr(web_app, "init_async_connection_pool", initialise)
    monkeypatch.setattr(web_app, "close_async_connection_pool", close)
    monkeypatch.setattr(
        web_app, "_safe_auto_check_and_build_schema", lambda: {"success": True}
    )

    async def exercise_lifespan() -> None:
        async with web_app.lifespan(web_app.app):
            events.append("serve")

    run_in_thread(exercise_lifespan)

    assert events == ["initialise", "serve", "close"]


def test_rate_limit_allows_exact_limit_then_blocks_next_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The configured request count is allowed; only the following request is blocked."""
    monkeypatch.setattr(web_app.time, "time", lambda: 100.0)

    decisions = [
        web_app.is_rate_limited("client-a", max_requests=3, window_seconds=60.0)
        for _ in range(4)
    ]

    assert decisions == [False, False, False, True]
    assert web_app.RATE_LIMIT_BUCKETS["client-a"] == [100.0, 100.0, 100.0]


def test_rate_limit_expires_timestamp_at_exact_window_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A timestamp exactly one window old must not consume current capacity."""
    web_app.RATE_LIMIT_BUCKETS["client-a"] = [40.0, 40.001]
    monkeypatch.setattr(web_app.time, "time", lambda: 100.0)

    limited = web_app.is_rate_limited(
        "client-a", max_requests=2, window_seconds=60.0
    )

    assert limited is False
    assert web_app.RATE_LIMIT_BUCKETS["client-a"] == [40.001, 100.0]


def test_rate_limit_buckets_are_isolated_by_client_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One saturated client key must not block an independent client key."""
    monkeypatch.setattr(web_app.time, "time", lambda: 100.0)

    assert web_app.is_rate_limited("client-a", max_requests=1) is False
    assert web_app.is_rate_limited("client-a", max_requests=1) is True
    assert web_app.is_rate_limited("client-b", max_requests=1) is False


def test_rate_limit_middleware_scopes_buckets_by_endpoint_and_ignores_health() -> None:
    """Login saturation must not block user-management or non-protected endpoints."""
    client = TestClient(web_app.app)

    for _ in range(10):
        response = client.post("/api/login", json={})
        assert response.status_code == 422

    blocked = client.post("/api/login", json={})
    separate_endpoint = client.get("/api/users")
    health = client.get("/health")

    assert blocked.status_code == 429
    assert blocked.json() == {
        "detail": "Too many requests. Rate limit exceeded. Please try again later."
    }
    assert separate_endpoint.status_code == 401
    assert health.status_code == 200


@pytest.mark.parametrize(
    ("secure_setting", "expects_secure"),
    [(None, True), ("false", False)],
)
def test_login_cookie_security_attributes_and_explicit_local_opt_out(
    monkeypatch: pytest.MonkeyPatch,
    secure_setting: str | None,
    expects_secure: bool,
) -> None:
    """Login cookies should be protected by default with one explicit local opt-out."""
    password = "CookieContract_admin_2026!"
    monkeypatch.setitem(
        web_app.ACCOUNT_REGISTRY["dca_admin_mgr"],
        "password_hash",
        web_app.hash_password(password),
    )
    if secure_setting is None:
        monkeypatch.delenv("COOKIE_SECURE", raising=False)
    else:
        monkeypatch.setenv("COOKIE_SECURE", secure_setting)

    response = TestClient(web_app.app, base_url="https://testserver").post(
        "/api/login",
        json={"username": "dca_admin_mgr", "password": password},
    )

    assert response.status_code == 200
    cookie_parts = {
        part.strip().lower() for part in response.headers["set-cookie"].split(";")
    }
    assert "httponly" in cookie_parts
    assert "samesite=lax" in cookie_parts
    assert "max-age=3600" in cookie_parts
    assert "path=/" in cookie_parts
    assert ("secure" in cookie_parts) is expects_secure


def test_cookie_logout_rejects_missing_csrf_and_untrusted_origin_then_clears_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cookie-authenticated logout must enforce CSRF checks before deleting the cookie."""
    password = "LogoutContract_admin_2026!"
    monkeypatch.setitem(
        web_app.ACCOUNT_REGISTRY["dca_admin_mgr"],
        "password_hash",
        web_app.hash_password(password),
    )
    monkeypatch.setenv("ALLOWED_ORIGIN", "https://portal.example.test")
    client = TestClient(web_app.app, base_url="https://portal.example.test")
    login = client.post(
        "/api/login",
        json={"username": "dca_admin_mgr", "password": password},
    )
    assert login.status_code == 200

    missing_csrf = client.post("/api/logout")
    untrusted_origin = client.post(
        "/api/logout",
        headers={
            "Origin": "https://attacker.example.test",
            "X-CSRF-Token": "present",
        },
    )
    logout = client.post(
        "/api/logout",
        headers={
            "Origin": "https://portal.example.test",
            "X-CSRF-Token": "present",
        },
    )

    assert missing_csrf.status_code == 403
    assert "csrf" in missing_csrf.json()["detail"].lower()
    assert untrusted_origin.status_code == 403
    assert "origin" in untrusted_origin.json()["detail"].lower()
    assert logout.status_code == 200
    assert "rcf_dac_jwt" not in client.cookies
    deletion_header = logout.headers["set-cookie"].lower()
    assert "rcf_dac_jwt=" in deletion_header
    assert "max-age=0" in deletion_header


def test_invalid_bearer_header_takes_precedence_over_valid_admin_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A bad explicit credential must not silently fall back to a valid cookie."""
    password = "HeaderPrecedence_admin_2026!"
    monkeypatch.setitem(
        web_app.ACCOUNT_REGISTRY["dca_admin_mgr"],
        "password_hash",
        web_app.hash_password(password),
    )
    client = TestClient(web_app.app, base_url="https://testserver")
    assert client.post(
        "/api/login",
        json={"username": "dca_admin_mgr", "password": password},
    ).status_code == 200

    response = client.get(
        "/api/users", headers={"Authorization": "Bearer invalid.explicit.token"}
    )

    assert response.status_code == 403


def test_investor_assets_cache_honours_ttl_boundary_and_bypass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache hits stop at the exact TTL boundary and bypass requests stay fresh."""
    headers = _authorisation_header("dca_investor_01", "investor")
    clock = [web_app.time.time()]
    monkeypatch.setattr(web_app.time, "time", lambda: clock[0])
    client = TestClient(web_app.app)

    fresh = client.get("/api/investor-assets", headers=headers)
    clock[0] += web_app.INVESTOR_ASSETS_CACHE_TTL - 0.001
    cached = client.get("/api/investor-assets", headers=headers)
    bypassed = client.get(
        "/api/investor-assets?bypass_cache=true", headers=headers
    )
    clock[0] += web_app.INVESTOR_ASSETS_CACHE_TTL
    expired = client.get("/api/investor-assets", headers=headers)

    assert fresh.status_code == cached.status_code == 200
    assert fresh.json()["cached"] is False
    assert cached.json()["cached"] is True
    assert bypassed.json()["cached"] is False
    assert expired.json()["cached"] is False


def test_did_registration_form_is_relocated_to_user_management_dashboard() -> None:
    """Guard against exposing the DID registration workflow on the public homepage."""
    client = TestClient(web_app.app)

    homepage = client.get("/")
    user_management = client.get("/user-management")

    assert homepage.status_code == 200
    assert 'id="user-reg-form"' not in homepage.text
    assert user_management.status_code == 200
    for element_id in (
        "user-reg-form",
        "reg-fullname",
        "reg-role",
        "reg-dept",
        "reg-email",
        "user-reg-output",
    ):
        assert f'id="{element_id}"' in user_management.text


def test_did_registration_script_persists_restores_and_escapes_records() -> None:
    """The relocated browser workflow should retain its persistence and XSS guards."""
    response = TestClient(web_app.app).get("/user-management")

    assert response.status_code == 200
    assert "localStorage.setItem('rcf_dac_user_registration'" in response.text
    assert "localStorage.getItem('rcf_dac_user_registration'" in response.text
    assert "Identity Generated (Persistence Unavailable)" in response.text
    for field in ("name", "role", "dept", "email", "did"):
        assert f"escapeHtml(userRecord.{field})" in response.text
