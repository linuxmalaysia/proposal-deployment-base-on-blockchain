"""Focused tests for PostgreSQL diagnostics and secret-safe status output."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("INVESTOR_JWT_SECRET", "test_rcf_dac_jwt_secret_key_2026")

from dca_service import web_app


DATABASE_ENV_KEYS = (
    "DATABASE_URL",
    "SUPABASE_DB_HOST",
    "SUPABASE_DB_PASSWORD",
    "SUPABASE_JWKS_URL",
    "SUPABASE_POOLER_HOST",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_SSLROOTCERT",
    "SUPABASE_URL",
)


@pytest.fixture(autouse=True)
def isolate_database_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep database tests independent from workstation configuration."""
    for key in DATABASE_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def install_fake_psycopg(
    monkeypatch: pytest.MonkeyPatch, connect: MagicMock
) -> None:
    """Install a minimal psycopg substitute for connection unit tests."""
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connect))


def make_connection(rows: list[tuple[str]] | None = None) -> tuple[MagicMock, MagicMock]:
    """Build a connection and its context-managed cursor."""
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = rows or []
    return connection, cursor


def test_load_secrets_parses_env_file_without_overwriting_existing_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    local_env = tmp_path / ".env"
    local_env.write_text(
        """
        # Render-compatible environment file
        PLAIN_SETTING=value
        SINGLE_QUOTED='single quoted value'
        DOUBLE_QUOTED="double quoted value"
        EXISTING_SETTING=from-file
        MALFORMED_LINE
        =missing-key
        """,
        encoding="utf-8",
    )
    missing_render_env = tmp_path / "missing-render.env"
    monkeypatch.setattr(web_app, "BASE_DIR", tmp_path)
    monkeypatch.setattr(web_app, "Path", lambda _value: missing_render_env)
    for key in ("PLAIN_SETTING", "SINGLE_QUOTED", "DOUBLE_QUOTED", "MALFORMED_LINE"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("EXISTING_SETTING", "from-environment")

    web_app.load_secrets_from_env_files()

    assert os.environ["PLAIN_SETTING"] == "value"
    assert os.environ["SINGLE_QUOTED"] == "single quoted value"
    assert os.environ["DOUBLE_QUOTED"] == "double quoted value"
    assert os.environ["EXISTING_SETTING"] == "from-environment"
    assert "MALFORMED_LINE" not in os.environ


@pytest.mark.parametrize("host_key", ["SUPABASE_POOLER_HOST", "SUPABASE_DB_HOST"])
def test_get_postgresql_connection_builds_dynamic_ssl_verified_pooler_url(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, host_key: str
) -> None:
    certificate = tmp_path / "supabase-ca.crt"
    certificate.write_text("test certificate", encoding="utf-8")
    connect = MagicMock(return_value=MagicMock())
    install_fake_psycopg(monkeypatch, connect)
    monkeypatch.setenv(host_key, "pooler.example.supabase.com")
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "p@ss word/+")
    monkeypatch.setenv("SUPABASE_SSLROOTCERT", str(certificate))

    connection, message = web_app.get_postgresql_connection()

    assert connection is connect.return_value
    assert message == "Connected to PostgreSQL"
    connect.assert_called_once_with(
        "postgresql://postgres.project-ref:p%40ss+word%2F%2B@"
        f"pooler.example.supabase.com:6543/postgres?sslmode=verify-full&sslrootcert={certificate}",
        connect_timeout=4,
    )


def test_get_postgresql_connection_prefers_explicit_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = MagicMock()
    connect = MagicMock(return_value=connection)
    install_fake_psycopg(monkeypatch, connect)
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured.example/app")
    monkeypatch.setenv("SUPABASE_POOLER_HOST", "ignored.example")
    monkeypatch.setenv("SUPABASE_URL", "https://ignored.supabase.co")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "ignored-password")

    result, message = web_app.get_postgresql_connection()

    assert result is connection
    assert message == "Connected to PostgreSQL"
    connect.assert_called_once_with(
        "postgresql://configured.example/app", connect_timeout=4
    )


def test_get_postgresql_connection_fails_closed_when_ca_certificate_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    connect = MagicMock()
    install_fake_psycopg(monkeypatch, connect)
    monkeypatch.setenv("SUPABASE_POOLER_HOST", "pooler.example.supabase.com")
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "database-password")
    monkeypatch.setenv("SUPABASE_SSLROOTCERT", str(tmp_path / "missing-ca.crt"))

    connection, message = web_app.get_postgresql_connection()

    assert connection is None
    assert "CA certificate missing" in message
    assert "failing closed" in message
    connect.assert_not_called()


def test_get_postgresql_connection_reports_connection_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect = MagicMock(side_effect=RuntimeError("network unavailable"))
    install_fake_psycopg(monkeypatch, connect)
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured.example/app")

    connection, message = web_app.get_postgresql_connection()

    assert connection is None
    assert message == "PostgreSQL connection error: network unavailable"


def test_check_database_connection_verifies_present_and_missing_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection, cursor = make_connection([("users",), ("assets",)])
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (connection, "Connected to PostgreSQL"),
    )
    urlopen = MagicMock()
    monkeypatch.setattr(urllib.request, "urlopen", urlopen)

    result = web_app.check_database_connection()

    assert result["status"] == "SUCCESSFULLY CONNECTED"
    assert result["is_connected"] is True
    assert result["db_connected"] is True
    assert result["http_api_connected"] is False
    statuses = {table["table_name"]: table["status"] for table in result["schema_tables"]}
    assert statuses["users"] == "VERIFIED IN POSTGRESQL DB"
    assert statuses["assets"] == "VERIFIED IN POSTGRESQL DB"
    assert statuses["cloverleaf_scores"] == "MISSING IN DATABASE"
    assert statuses["revenue_splits"] == "MISSING IN DATABASE"
    assert statuses["blockchain_transactions"] == "MISSING IN DATABASE"
    cursor.execute.assert_called_once_with(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
    )
    connection.close.assert_called_once_with()
    urlopen.assert_not_called()


def test_check_database_connection_marks_table_status_unknown_after_query_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection, cursor = make_connection()
    cursor.execute.side_effect = RuntimeError("catalog unavailable")
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (connection, "Connected to PostgreSQL"),
    )

    result = web_app.check_database_connection()

    assert result["status"] == "SUCCESSFULLY CONNECTED"
    assert "PostgreSQL query error: catalog unavailable" in result["status_detail"]
    assert {table["status"] for table in result["schema_tables"]} == {
        "UNKNOWN (QUERY FAILED)"
    }
    connection.close.assert_called_once_with()


def test_check_database_connection_uses_derived_jwks_url_when_only_http_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://project-ref.supabase.co")
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (None, "Database configuration unavailable"),
    )
    response_context = MagicMock()
    response_context.__enter__.return_value.status = 200
    urlopen = MagicMock(return_value=response_context)
    monkeypatch.setattr(urllib.request, "urlopen", urlopen)

    result = web_app.check_database_connection()

    assert result["status"] == "HTTP API OPERATIONAL (DB DISCONNECTED)"
    assert result["db_connected"] is False
    assert result["http_api_connected"] is True
    assert {table["status"] for table in result["schema_tables"]} == {
        "VERIFIED DDL SCHEMA FILE"
    }
    request = urlopen.call_args.args[0]
    assert request.full_url == (
        "https://project-ref.supabase.co/auth/v1/.well-known/jwks.json"
    )
    assert request.get_header("User-agent") == "RCF-DAC-DB-Status-Check/1.0"
    assert urlopen.call_args.kwargs == {"timeout": 5}


def test_status_endpoints_do_not_expose_configured_secret_names_or_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sensitive_settings = {
        "DATABASE_URL": "postgresql://secret-user:secret-password@private-db.example/app",
        "SUPABASE_JWKS_URL": "https://private-auth.example/secret-jwks",
        "SUPABASE_PUBLISHABLE_KEY": "publishable-value-that-must-not-leak",
        "SUPABASE_SECRET_KEY": "service-role-value-that-must-not-leak",
        "SUPABASE_URL": "https://private-project.supabase.co",
    }
    for key, value in sensitive_settings.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (None, "Database connection unavailable"),
    )
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        MagicMock(side_effect=OSError("HTTP endpoint unavailable")),
    )
    client = TestClient(web_app.app)

    api_response = client.get("/api/db-status")
    page_response = client.get("/db-status")

    assert api_response.status_code == 200
    assert page_response.status_code == 200
    api_data = api_response.json()
    assert "environment" not in api_data
    rendered_outputs = (json.dumps(api_data), page_response.text)
    for output in rendered_outputs:
        for key, value in sensitive_settings.items():
            assert key not in output
            assert value not in output
        assert "Environment Secret Variables" not in output


def test_auto_check_and_build_schema_builds_missing_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify auto_check_and_build_schema executes DDL schema initialisation when missing tables exist."""
    connection, cursor = make_connection([("users",)])
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (connection, "Connected to PostgreSQL"),
    )
    mock_init = MagicMock(return_value={"success": True, "message": "Schema executed"})
    monkeypatch.setattr(web_app, "initialize_database_schema", mock_init)

    res = web_app.auto_check_and_build_schema()

    assert res["success"] is True
    assert res["db_connected"] is True
    assert set(res["tables_created"]) == {
        "assets",
        "cloverleaf_scores",
        "revenue_splits",
        "blockchain_transactions",
    }
    mock_init.assert_called_once()
    connection.close.assert_called_once()


def test_auto_check_and_build_schema_skips_when_all_tables_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify auto_check_and_build_schema skips DDL schema initialisation when all required tables exist."""
    connection, cursor = make_connection(
        [
            ("users",),
            ("assets",),
            ("cloverleaf_scores",),
            ("revenue_splits",),
            ("blockchain_transactions",),
        ]
    )
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (connection, "Connected to PostgreSQL"),
    )
    mock_init = MagicMock()
    monkeypatch.setattr(web_app, "initialize_database_schema", mock_init)

    res = web_app.auto_check_and_build_schema()

    assert res["success"] is True
    assert res["db_connected"] is True
    assert res["tables_created"] == []
    mock_init.assert_not_called()
    connection.close.assert_called_once()


def test_auto_check_and_build_schema_handles_connection_failure_failsafely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify auto_check_and_build_schema handles database connection errors fail-safely without raising."""
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (None, "PostgreSQL connection error: network unavailable"),
    )

    res = web_app.auto_check_and_build_schema()

    assert res["success"] is False
    assert res["db_connected"] is False
    assert "skipped" in res["message"]


def test_lifespan_startup_triggers_auto_check_and_build_schema_failsafely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify FastAPI lifespan startup context manager triggers schema auto-check fail-safely on app boot."""
    mock_auto = MagicMock(side_effect=RuntimeError("Database temporarily unreachable"))
    monkeypatch.setattr(web_app, "auto_check_and_build_schema", mock_auto)

    # Lifespan context startup should execute auto_check_and_build_schema without failing app creation
    with TestClient(web_app.app) as client:
        response = client.get("/health")
        assert response.status_code == 200

    mock_auto.assert_called()
