"""Tests for the documentation rendering and Supabase guide added by this PR."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ``web_app`` deliberately fails closed during import when this secret is absent.
os.environ.setdefault("INVESTOR_JWT_SECRET", "test_rcf_dac_jwt_secret_key_2026")

from dca_service import web_app


REPO_ROOT = Path(__file__).resolve().parent.parent
SUPABASE_GUIDE = REPO_ROOT / "docs" / "how-to" / "connect-supabase-postgresql-on-render.md"
DEPLOYMENT_GUIDE = REPO_ROOT / "docs" / "how-to" / "deploy-rcf-dac-web-app-on-render.md"
SUMMARY = REPO_ROOT / "SUMMARY.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
HISTORY = REPO_ROOT / "HISTORY.md"

MANDATORY_OKF_FIELDS = (
    "okf_version",
    "type",
    "title",
    "timestamp",
    "topics",
    "description",
    "resource",
    "sources",
    "generated",
    "verified",
    "status",
    "stale_after",
    "language",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frontmatter(content: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    assert match, "expected an OKF frontmatter block at the start of the document"
    return match.group(1)


class TestMarkdownRenderer:
    def test_converts_supported_block_and_inline_markdown(self):
        markdown = """{::options parse_block_html="true" /}
# Main heading
## Section heading
### Detail heading
---
Use **strong text** and [the guide](docs/how-to/guide.html).
"""

        rendered = web_app.render_markdown_to_html(markdown)

        assert "{::options" not in rendered
        assert "<h1>Main heading</h1>" in rendered
        assert "<h2>Section heading</h2>" in rendered
        assert "<h3>Detail heading</h3>" in rendered
        assert "<hr>" in rendered
        assert "<strong>strong text</strong>" in rendered
        assert '<a href="docs/how-to/guide.html">the guide</a>' in rendered

    def test_groups_consecutive_bullets_and_closes_a_list_at_end_of_input(self):
        markdown = """Before
- First **item**
- [Second](second.html)
After
- Final item"""

        rendered = web_app.render_markdown_to_html(markdown)

        assert rendered.count("<ul>") == 2
        assert rendered.count("</ul>") == 2
        assert "  <li>First <strong>item</strong></li>" in rendered
        assert '  <li><a href="second.html">Second</a></li>' in rendered
        assert rendered.endswith("  <li>Final item</li>\n</ul>")
        assert rendered.index("</ul>") < rendered.index("After")

    @pytest.mark.parametrize(
        "markdown", ["", "Plain text", "#### Unsupported heading", "* Asterisk bullet"]
    )
    def test_preserves_content_outside_the_supported_markdown_subset(self, markdown):
        assert web_app.render_markdown_to_html(markdown) == markdown


@pytest.fixture
def isolated_docs_dir(tmp_path, monkeypatch):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    guide = docs_dir / "guide.md"
    guide.write_text(
        """---
okf_version: "0.2"
title: "Temporary Guide"
---
# Rendered Guide

- **Secure** setting
- Read the [reference](reference.html)
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(web_app, "DOCS_DIR", docs_dir)
    return docs_dir


class TestDocumentationRoute:
    @pytest.mark.parametrize("suffix", ["", ".md", ".html"])
    def test_serves_extensionless_markdown_and_html_paths(self, isolated_docs_dir, suffix):
        response = TestClient(web_app.app).get(f"/docs/guide{suffix}")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert response.text.startswith("<!DOCTYPE html>")
        assert '<html lang="en-GB">' in response.text
        assert '<link rel="stylesheet" href="/assets/css/style.css">' in response.text
        assert '<script src="/assets/js/rcf-dac-app.js" defer></script>' in response.text
        assert "<h1>Rendered Guide</h1>" in response.text
        assert "<li><strong>Secure</strong> setting</li>" in response.text
        assert '<a href="reference.html">reference</a>' in response.text
        assert "okf_version" not in response.text
        assert "Temporary Guide" not in response.text

    def test_missing_document_and_directory_are_not_served(self, isolated_docs_dir):
        (isolated_docs_dir / "directory.md").mkdir()
        client = TestClient(web_app.app)

        missing = client.get("/docs/missing.html")
        directory = client.get("/docs/directory.md")

        assert missing.status_code == 404
        assert missing.json() == {"detail": "Documentation page not found"}
        assert directory.status_code == 404

    @pytest.mark.parametrize("file_path", ["../outside", "nested/../../outside", "/etc/passwd"])
    def test_rejects_paths_that_resolve_outside_docs_directory(
        self, isolated_docs_dir, file_path
    ):
        with pytest.raises(HTTPException) as exc_info:
            web_app.serve_docs(file_path)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Documentation page not found"

    def test_homepage_uses_renderer_for_markdown_navigation(self):
        response = TestClient(web_app.app).get("/")

        assert response.status_code == 200
        assert "<h1>🏛️ Research Commercialisation Fund" in response.text
        assert "<strong>University Research Commercialisation Fund (RCF)</strong>" in response.text
        assert '<a href="docs/tutorials/web-application-user-guide.html">' in response.text
        assert "{::options" not in response.text


class TestSupabaseConnectionGuide:
    def test_has_complete_approved_okf_frontmatter(self):
        content = _read(SUPABASE_GUIDE)
        frontmatter = _frontmatter(content)

        for field in MANDATORY_OKF_FIELDS:
            assert re.search(rf"(?m)^{field}:", frontmatter), f"missing {field!r}"
        assert 'okf_version: "0.2"' in frontmatter
        assert 'type: "howto"' in frontmatter
        assert 'status: "approved"' in frontmatter
        assert 'language: "en-GB"' in frontmatter
        assert (
            'resource: "file:///docs/how-to/connect-supabase-postgresql-on-render.md"'
            in frontmatter
        )

    def test_documents_all_three_connection_modes_with_certificate_verification(self):
        content = _read(SUPABASE_GUIDE)
        overview = content[
            content.index("## 🎯 Architectural Overview") : content.index("## 🛠️ Step 1")
        ]
        connection_uris = re.findall(r"`(postgresql://[^`]+)`", overview)

        assert len(connection_uris) == 3
        assert "@db.<PROJECT_REF>.supabase.co:5432/postgres" in connection_uris[0]
        assert "@aws-<REGION>.pooler.supabase.com:5432/postgres" in connection_uris[1]
        assert "@aws-<REGION>.pooler.supabase.com:6543/postgres" in connection_uris[2]
        assert all("sslmode=verify-full" in uri for uri in connection_uris)
        assert all("sslrootcert=/path/to/prod-supabase-ca.crt" in uri for uri in connection_uris)

    def test_warns_about_reserved_password_characters_and_transaction_pooling_limits(self):
        content = _read(SUPABASE_GUIDE)

        assert "MUST be percent-encoded (URL-encoded)" in content
        for reserved_character in ("@", ":", "/", "?", "#", "%", "&", "+"):
            assert f"`{reserved_character}`" in content
        for unsupported_feature in (
            "prepared statements",
            "`LISTEN`/`NOTIFY`",
            "advisory locks",
            "temporary tables",
        ):
            assert unsupported_feature in content

    def test_keeps_render_and_supabase_credentials_out_of_version_control(self):
        content = _read(SUPABASE_GUIDE)

        assert "Never commit database passwords, API keys, or access tokens" in content
        assert "Render Environment Variables" in content
        for variable in (
            "DATABASE_URL",
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_ACCESS_TOKEN",
            "SUPABASE_DB_PASSWORD",
        ):
            assert f"`{variable}`" in content
        assert "<PASSWORD>" in content
        assert "<PROJECT_REF>" in content
        assert "<REGION>" in content

    def test_documents_non_interactive_cli_authentication_linking_and_migrations(self):
        content = _read(SUPABASE_GUIDE)

        assert "read -s SUPABASE_ACCESS_TOKEN" in content
        assert "supabase init" in content
        assert 'export SUPABASE_DB_PASSWORD="your-db-password"' in content
        assert (
            'supabase link --project-ref <PROJECT_REF> --password "$SUPABASE_DB_PASSWORD"'
            in content
        )
        assert 'supabase db push --password "$SUPABASE_DB_PASSWORD"' in content


class TestChangedDocumentationIntegration:
    def test_deployment_guide_links_to_database_guide_and_documents_manual_secret_setup(self):
        content = _read(DEPLOYMENT_GUIDE)

        assert '"docs/how-to/connect-supabase-postgresql-on-render.md"' in _frontmatter(content)
        assert "[Connecting Supabase PostgreSQL Database Securely on Render.com]" in content
        assert "(connect-supabase-postgresql-on-render.md)" in content
        assert "### Method 2: Manual Web Service Setup on Render (Free Tier Compatible)" in content
        assert "### 5. Missing Required Environment Variables (`INVESTOR_JWT_SECRET`)" in content
        assert "openssl rand -hex 32" in content

    def test_new_guide_is_discoverable_from_summary_and_both_ledgers(self):
        summary = _read(SUMMARY)
        changelog = _read(CHANGELOG)
        history = _read(HISTORY)

        expected_entry = (
            "* [Connecting Supabase PostgreSQL Database Securely on Render.com]"
            "(docs/how-to/connect-supabase-postgresql-on-render.md)"
        )
        assert expected_entry in summary
        assert "connect-supabase-postgresql-on-render.md" in changelog
        assert "connect-supabase-postgresql-on-render.md" in history
