"""Focused tests for the user-management, async-pool, and rate-limit PR changes."""

from __future__ import annotations

import asyncio
import os
import sys
from types import SimpleNamespace
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


@pytest.fixture(autouse=True)
def isolate_changed_global_state(monkeypatch: pytest.MonkeyPatch):
    """Keep async-pool and rate-limit globals independent between tests."""
    original_pool = web_app.ASYNC_DB_POOL
    web_app.ASYNC_DB_POOL = None
    web_app.RATE_LIMIT_BUCKETS.clear()
    for key in ASYNC_DATABASE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    yield

    web_app.ASYNC_DB_POOL = original_pool
    web_app.RATE_LIMIT_BUCKETS.clear()


def install_fake_async_pool(
    monkeypatch: pytest.MonkeyPatch, pool_factory: MagicMock
) -> None:
    """Install a minimal psycopg-pool substitute for lifecycle unit tests."""
    monkeypatch.setitem(
        sys.modules,
        "psycopg_pool",
        SimpleNamespace(AsyncConnectionPool=pool_factory),
    )


def test_init_async_pool_opens_explicit_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An explicit DATABASE_URL should be used without Supabase URL rewriting."""
    pool = SimpleNamespace(open=AsyncMock(), close=AsyncMock())
    pool_factory = MagicMock(return_value=pool)
    install_fake_async_pool(monkeypatch, pool_factory)
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured.example/app")
    monkeypatch.setenv("SUPABASE_POOLER_HOST", "ignored.example")
    monkeypatch.setattr(web_app.DB_POOL_METRICS, "max_pool_size", 7)

    result = asyncio.run(web_app.init_async_connection_pool())

    assert result is pool
    assert web_app.ASYNC_DB_POOL is pool
    pool_factory.assert_called_once_with(
        conninfo="postgresql://configured.example/app",
        min_size=1,
        max_size=7,
        open=False,
    )
    pool.open.assert_awaited_once_with()


@pytest.mark.parametrize("host_key", ["SUPABASE_POOLER_HOST", "SUPABASE_DB_HOST"])
def test_init_async_pool_builds_url_from_supabase_configuration(
    monkeypatch: pytest.MonkeyPatch, host_key: str
) -> None:
    """Either supported Supabase host variable should enable pool initialisation."""
    pool = SimpleNamespace(open=AsyncMock(), close=AsyncMock())
    pool_factory = MagicMock(return_value=pool)
    install_fake_async_pool(monkeypatch, pool_factory)
    monkeypatch.setenv(host_key, "pooler.example.supabase.com")
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "p@ss word/+")

    result = asyncio.run(web_app.init_async_connection_pool())

    assert result is pool
    assert pool_factory.call_args.kwargs["conninfo"] == (
        "postgresql://postgres:p%40ss+word%2F%2B@"
        "pooler.example.supabase.com:5432/postgres?sslmode=require"
    )
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

    result = asyncio.run(web_app.init_async_connection_pool())

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
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured.example/app")
    web_app.ASYNC_DB_POOL = object()

    result = asyncio.run(web_app.init_async_connection_pool())

    assert result is None
    assert web_app.ASYNC_DB_POOL is None
    pool.open.assert_awaited_once_with()


@pytest.mark.parametrize("close_error", [None, RuntimeError("shutdown failed")])
def test_close_async_pool_always_clears_global_reference(close_error: Exception | None) -> None:
    """Successful and failed shutdowns must both make the closed pool unreachable."""
    pool = SimpleNamespace(close=AsyncMock(side_effect=close_error))
    web_app.ASYNC_DB_POOL = pool

    asyncio.run(web_app.close_async_connection_pool())

    pool.close.assert_awaited_once_with()
    assert web_app.ASYNC_DB_POOL is None


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

    asyncio.run(exercise_lifespan())

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
