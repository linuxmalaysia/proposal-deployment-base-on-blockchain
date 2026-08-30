"""Unit tests for the web application's PostgreSQL and Markdown helpers."""

from __future__ import annotations

import builtins
import os
import sys
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException

# The application deliberately fails closed when imported without a JWT secret.
os.environ.setdefault("INVESTOR_JWT_SECRET", "test_rcf_dac_jwt_secret_key_2026")

from dca_service import web_app


class FakeCursor:
    def __init__(self, rows: list[tuple[str]] | None = None, error: Exception | None = None):
        self.rows = rows or []
        self.error = error
        self.statements: list[str] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *args: Any) -> None:
        return None

    def execute(self, statement: str) -> None:
        self.statements.append(statement)
        if self.error:
            raise self.error

    def fetchall(self) -> list[tuple[str]]:
        return self.rows


class FakeConnection:
    def __init__(self, cursor: FakeCursor):
        self.fake_cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closes = 0

    def cursor(self) -> FakeCursor:
        return self.fake_cursor

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closes += 1


class FakeHttpResponse:
    def __init__(self, status: int):
        self.status = status

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: Any) -> None:
        return None


@pytest.fixture(autouse=True)
def clean_database_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep database tests independent of developer and CI configuration."""
    for key in (
        "DATABASE_URL",
        "SUPABASE_URL",
        "SUPABASE_PUBLISHABLE_KEY",
        "SUPABASE_SECRET_KEY",
        "SUPABASE_JWKS_URL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_load_secrets_parses_env_file_without_overwriting_existing_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        """# ignored comment
EXISTING=from-file
QUOTED = 'quoted value'
DOUBLE_QUOTED=\"double quoted\"
VALUE_WITH_EQUALS=left=right
MALFORMED_LINE
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(web_app, "BASE_DIR", tmp_path)
    monkeypatch.setenv("EXISTING", "from-environment")
    monkeypatch.delenv("QUOTED", raising=False)
    monkeypatch.delenv("DOUBLE_QUOTED", raising=False)
    monkeypatch.delenv("VALUE_WITH_EQUALS", raising=False)

    web_app.load_secrets_from_env_files()

    assert os.environ["EXISTING"] == "from-environment"
    assert os.environ["QUOTED"] == "quoted value"
    assert os.environ["DOUBLE_QUOTED"] == "double quoted"
    assert os.environ["VALUE_WITH_EQUALS"] == "left=right"
    assert "MALFORMED_LINE" not in os.environ


def test_get_postgresql_connection_uses_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_connection = object()
    calls: list[tuple[str, int]] = []
    monkeypatch.setenv("DATABASE_URL", "postgresql://database.example/application")

    def connect(url: str, *, connect_timeout: int) -> object:
        calls.append((url, connect_timeout))
        return expected_connection

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=connect))

    connection, message = web_app.get_postgresql_connection()

    assert connection is expected_connection
    assert message == "Connected to PostgreSQL"
    assert calls == [("postgresql://database.example/application", 4)]


def test_get_postgresql_connection_builds_project_pooler_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    monkeypatch.setenv("SUPABASE_URL", "https://tqudolprdioisrgqfyna.supabase.co")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "database-password")
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(
            connect=lambda url, **kwargs: captured.update(url=url, **kwargs) or object()
        ),
    )

    connection, message = web_app.get_postgresql_connection()

    assert connection is not None
    assert message == "Connected to PostgreSQL"
    assert captured == {
        "url": (
            "postgresql://postgres.tqudolprdioisrgqfyna:database-password@"
            "aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
        ),
        "connect_timeout": 4,
    }


def test_get_postgresql_connection_reports_missing_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=lambda *args: object()))
    assert web_app.get_postgresql_connection() == (None, "DATABASE_URL not configured")


def test_get_postgresql_connection_reports_driver_import_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_import = builtins.__import__

    def import_without_psycopg(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "psycopg":
            raise ImportError("driver unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_psycopg)

    assert web_app.get_postgresql_connection() == (None, "psycopg driver not installed")


def test_get_postgresql_connection_returns_sanitised_failure_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://database.example/application")
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(
            connect=lambda *args, **kwargs: (_ for _ in ()).throw(
                OSError("host unreachable")
            )
        ),
    )

    connection, message = web_app.get_postgresql_connection()

    assert connection is None
    assert message == "PostgreSQL connection error: host unreachable"


def test_initialize_database_schema_executes_script_and_commits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    schema_dir = tmp_path / "docs"
    schema_dir.mkdir()
    schema_file = schema_dir / "schema.sql"
    schema_file.write_text("CREATE TABLE example (id INT);", encoding="utf-8")
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(web_app, "BASE_DIR", tmp_path)
    monkeypatch.setattr(
        web_app, "get_postgresql_connection", lambda: (connection, "Connected")
    )

    result = web_app.initialize_database_schema()

    assert result["success"] is True
    assert "Successfully executed DDL schema" in result["message"]
    assert cursor.statements == ["CREATE TABLE example (id INT);"]
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closes == 1


def test_initialize_database_schema_rolls_back_and_closes_on_sql_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    schema_dir = tmp_path / "docs"
    schema_dir.mkdir()
    (schema_dir / "schema.sql").write_text("INVALID SQL", encoding="utf-8")
    connection = FakeConnection(FakeCursor(error=RuntimeError("syntax error")))
    monkeypatch.setattr(web_app, "BASE_DIR", tmp_path)
    monkeypatch.setattr(
        web_app, "get_postgresql_connection", lambda: (connection, "Connected")
    )

    result = web_app.initialize_database_schema()

    assert result == {"success": False, "message": "Failed to execute schema DDL: syntax error"}
    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closes == 1


def test_initialize_database_schema_handles_missing_file_and_connection(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(web_app, "BASE_DIR", tmp_path)
    assert web_app.initialize_database_schema() == {
        "success": False,
        "message": "docs/schema.sql file missing",
    }

    schema_dir = tmp_path / "docs"
    schema_dir.mkdir()
    (schema_dir / "schema.sql").write_text("SELECT 1;", encoding="utf-8")
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (None, "DATABASE_URL not configured"),
    )
    assert web_app.initialize_database_schema() == {
        "success": False,
        "message": "DATABASE_URL not configured",
    }


def test_database_status_uses_read_only_discovery_and_marks_each_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = FakeCursor(rows=[("users",), ("blockchain_transactions",)])
    connection = FakeConnection(cursor)
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-secret-value")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "must-not-be-returned")
    monkeypatch.setenv("SUPABASE_JWKS_URL", "")
    monkeypatch.setattr(
        web_app, "get_postgresql_connection", lambda: (connection, "Connected")
    )
    clock = iter((100.0, 100.125))
    monkeypatch.setattr(web_app.time, "time", lambda: next(clock))

    result = web_app.check_database_connection()

    assert result["status"] == "SUCCESSFULLY CONNECTED"
    assert result["is_connected"] is True
    assert result["http_api_connected"] is False
    assert result["latency_ms"] == 125.0
    assert cursor.statements == [
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
    ]
    assert connection.closes == 1
    statuses = {item["table_name"]: item["status"] for item in result["schema_tables"]}
    assert statuses["users"] == "VERIFIED IN POSTGRESQL DB"
    assert statuses["blockchain_transactions"] == "VERIFIED IN POSTGRESQL DB"
    assert statuses["assets"] == "MISSING IN DATABASE"
    assert result["environment"] == {
        "SUPABASE_URL": "https://tqudolprdioisrgqfyna.supabase.co",
        "SUPABASE_PUBLISHABLE_KEY": "publ...alue",
        "SUPABASE_SECRET_KEY_CONFIGURED": True,
        "SUPABASE_JWKS_URL": "NOT CONFIGURED",
        "DATABASE_URL_CONFIGURED": True,
    }
    assert "must-not-be-returned" not in str(result)


def test_database_status_distinguishes_http_only_connectivity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SUPABASE_JWKS_URL", "https://supabase.example/jwks.json")
    monkeypatch.setattr(
        web_app,
        "get_postgresql_connection",
        lambda: (None, "DATABASE_URL not configured"),
    )
    requests: list[tuple[str, int, str]] = []

    def urlopen(request: urllib.request.Request, timeout: int) -> FakeHttpResponse:
        requests.append((request.full_url, timeout, request.get_header("User-agent")))
        return FakeHttpResponse(200)

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)

    result = web_app.check_database_connection()

    assert result["status"] == "HTTP API OPERATIONAL (DB DISCONNECTED)"
    assert result["db_connected"] is False
    assert result["http_api_connected"] is True
    assert "Supabase Auth API Operational" in result["status_detail"]
    assert {item["status"] for item in result["schema_tables"]} == {
        "VERIFIED DDL SCHEMA FILE"
    }
    assert requests == [
        (
            "https://supabase.example/jwks.json",
            5,
            "RCF-DAC-DB-Status-Check/1.0",
        )
    ]


def test_database_status_closes_connection_after_read_only_query_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(FakeCursor(error=RuntimeError("permission denied")))
    monkeypatch.setenv("SUPABASE_JWKS_URL", "")
    monkeypatch.setattr(
        web_app, "get_postgresql_connection", lambda: (connection, "Connected")
    )

    result = web_app.check_database_connection()

    assert result["status"] == "SUCCESSFULLY CONNECTED"
    assert "PostgreSQL query error: permission denied" in result["status_detail"]
    assert connection.closes == 1
    assert {item["status"] for item in result["schema_tables"]} == {
        "MISSING IN DATABASE"
    }


def test_init_db_endpoint_requires_and_verifies_bearer_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(HTTPException) as missing:
        web_app.init_db_endpoint(None)
    assert missing.value.status_code == 401
    assert missing.value.headers == {"WWW-Authenticate": "Bearer"}

    with pytest.raises(HTTPException) as malformed:
        web_app.init_db_endpoint("Basic credentials")
    assert malformed.value.status_code == 401

    verified: list[str] = []
    monkeypatch.setattr(
        web_app, "verify_investor_bearer_token", lambda token: verified.append(token)
    )
    monkeypatch.setattr(
        web_app,
        "initialize_database_schema",
        lambda: {"success": True, "message": "initialised"},
    )

    result = web_app.init_db_endpoint("Bearer signed-token")

    assert verified == ["signed-token"]
    assert result == {"success": True, "message": "initialised"}


def test_db_status_api_and_dashboard_delegate_to_status_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_result = {
        "status": "SUCCESSFULLY CONNECTED",
        "is_connected": True,
        "db_connected": True,
        "http_api_connected": False,
        "latency_ms": 1.25,
        "status_detail": "PostgreSQL Database Connection Established",
        "timestamp": "2026-08-30T00:00:00Z",
        "environment": {"DATABASE_URL_CONFIGURED": True},
        "schema_tables": [
            {
                "table_name": "users",
                "description": "Institutional users",
                "status": "VERIFIED IN POSTGRESQL DB",
            }
        ],
        "schema_file": "docs/schema.sql",
    }
    monkeypatch.setattr(web_app, "check_database_connection", lambda: status_result)

    assert web_app.get_db_status_api() is status_result
    response = web_app.serve_db_status_page()
    body = response.body.decode()
    assert "🟢 SUCCESSFULLY CONNECTED" in body
    assert "PostgreSQL Database Connection Established" in body
    assert "<code>users</code>" in body
    assert "VERIFIED IN POSTGRESQL DB" in body


def test_markdown_renderer_converts_supported_elements_and_closes_lists() -> None:
    markdown = """{::options parse_block_html=\"true\" /}
# Heading
## Section
### Detail
---
**Important** [guide](/docs/guide)
- first
- second
Paragraph
- final
"""

    rendered = web_app.render_markdown_to_html(markdown)

    assert "{::options" not in rendered
    assert "<h1>Heading</h1>" in rendered
    assert "<h2>Section</h2>" in rendered
    assert "<h3>Detail</h3>" in rendered
    assert "<hr>" in rendered
    assert '<strong>Important</strong> <a href="/docs/guide">guide</a>' in rendered
    assert "<ul>\n  <li>first</li>\n  <li>second</li>\n</ul>\nParagraph" in rendered
    assert rendered.endswith("<ul>\n  <li>final</li>\n</ul>")


def test_serve_docs_rejects_traversal_and_missing_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    monkeypatch.setattr(web_app, "DOCS_DIR", docs_dir)

    for requested_path in ("../../README", "missing"):
        with pytest.raises(HTTPException) as error:
            web_app.serve_docs(requested_path)
        assert error.value.status_code == 404
        assert error.value.detail == "Documentation page not found"


@pytest.mark.parametrize("suffix", ["guide", "guide.md", "guide.html"])
def test_serve_docs_supports_route_suffixes_and_removes_frontmatter(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, suffix: str
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "guide.md").write_text(
        "---\ntitle: Hidden metadata\n---\n# Visible title\n", encoding="utf-8"
    )
    monkeypatch.setattr(web_app, "DOCS_DIR", docs_dir)

    response = web_app.serve_docs(suffix)
    body = response.body.decode()

    assert response.status_code == 200
    assert "<h1>Visible title</h1>" in body
    assert "Hidden metadata" not in body
