"""Unit tests for RCF/DAC Web Application Portal engine, assets, and user guide documentation."""

from pathlib import Path
import re

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

JS_APP = REPO_ROOT / "assets" / "js" / "rcf-dac-app.js"
CSS_STYLE = REPO_ROOT / "assets" / "css" / "style.css"
INDEX_MD = REPO_ROOT / "index.md"
DEFAULT_LAYOUT = REPO_ROOT / "_layouts" / "default.html"
SUMMARY_DOC = REPO_ROOT / "SUMMARY.md"
GITIGNORE = REPO_ROOT / ".gitignore"
USER_GUIDE_DOC = REPO_ROOT / "docs" / "tutorials" / "web-application-user-guide.md"
PROPOSAL_DOC = REPO_ROOT / "docs" / "explanation" / "research-commercialisation-fund-dac-proposal.md"
CONNECT_SUPABASE_DOC = REPO_ROOT / "docs" / "how-to" / "connect-supabase-postgresql-on-render.md"
OWASP_AUTH_DOC = REPO_ROOT / "docs" / "explanation" / "owasp-authorization-framework.md"
SUPERUSER_RESET_DOC = REPO_ROOT / "docs" / "how-to" / "reset-superuser-password-and-manage-users.md"


def _read(path: Path) -> str:
    """Read a UTF-8-encoded text file.

    Parameters:
        path (Path): Path to the file to read

    Returns:
        str: The file contents
    """
    return path.read_text(encoding="utf-8")


def _extract_frontmatter_dict(content: str) -> dict[str, str]:
    """
    Extract key-value pairs from a document's YAML-style frontmatter.

    Parameters:
        content (str): Document content beginning and ending with `---` frontmatter delimiters.

    Returns:
        dict[str, str]: Parsed frontmatter keys and values.

    Raises:
        AssertionError: If the content is empty or lacks the required frontmatter delimiters.
    """
    lines = content.splitlines()
    assert lines, "Expected non-empty lines"
    assert lines[0].strip() == "---", "Expected opening '---' frontmatter delimiter"
    closing_idx = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing_idx = idx
            break
    assert closing_idx != -1, "Expected closing '---' frontmatter delimiter"

    frontmatter = {}
    for line in lines[1:closing_idx]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and ":" in stripped:
            k, v = stripped.split(":", 1)
            frontmatter[k.strip()] = v.strip().strip("'\"")
    return frontmatter


class TestRcfDacJsAppEngine:
    def test_file_exists(self):
        assert JS_APP.is_file()

    def test_handles_raw_amount_parsing_with_zero_support(self):
        content = _read(JS_APP)
        assert "Number.isFinite(rawAmount)" in content
        assert "rawAmount < 0" in content

    def test_uses_web_crypto_sha256_digest(self):
        content = _read(JS_APP)
        assert "crypto.subtle.digest('SHA-256'" in content

    def test_handles_local_storage_failure_gracefully(self):
        content = _read(JS_APP)
        assert "localStorage.setItem" in content
        assert "savedSuccessfully" in content

    def test_enforces_strict_cloverleaf_score_threshold(self):
        content = _read(JS_APP)
        assert "if (total > 180)" in content


class TestRcfDacUserGuideDoc:
    def test_user_guide_file_exists(self):
        assert USER_GUIDE_DOC.is_file()

    def test_okf_v02_frontmatter_present(self):
        content = _read(USER_GUIDE_DOC)
        assert content.startswith("---")
        assert 'okf_version: "0.2"' in content
        assert 'type: "tutorial"' in content
        assert 'language: "en-GB"' in content

    def test_documents_strict_score_threshold(self):
        content = _read(USER_GUIDE_DOC)
        assert "strictly exceeds **180 / 260 points**" in content or "scores > 180" in content

    @pytest.mark.parametrize("route", ["/login", "/user-management"])
    def test_documents_authentication_navigation_routes(self, route):
        content = _read(USER_GUIDE_DOC)
        assert f"]({route})" in content

    def test_documents_authenticated_user_management_workflow(self):
        content = _read(USER_GUIDE_DOC)
        assert "dca_sys_root" in content
        assert "dca_admin_mgr" in content
        assert "Authorization: Bearer <token>" in content
        assert "create new administrator or operator accounts" in content

    def test_links_to_superuser_reset_guide_and_documents_api_restriction(self):
        content = _read(USER_GUIDE_DOC)
        assert "../how-to/reset-superuser-password-and-manage-users.html" in content
        assert "password resets are restricted" in content
        assert "SUPERUSER_INITIAL_PASSWORD" in content


class TestRcfDacIndexMarkdown:
    def test_index_md_file_exists(self):
        assert INDEX_MD.is_file()

    def test_includes_file_upload_input(self):
        content = _read(INDEX_MD)
        pattern = r'<input\b[^>]*type=["\']file["\'][^>]*id=["\']asset-file["\']|<input\b[^>]*id=["\']asset-file["\'][^>]*type=["\']file["\']'
        assert re.search(pattern, content) is not None

    def test_includes_parse_block_html_options(self):
        content = _read(INDEX_MD)
        assert '{::options parse_block_html="true" /}' in content

    @pytest.mark.parametrize(
        ("route", "label"),
        [
            ("/login", "System Login"),
            ("/user-management", "User Management"),
        ],
    )
    def test_includes_authentication_links_in_banner_and_documentation(self, route, label):
        content = _read(INDEX_MD)
        assert f'href="{route}"' in content and 'class="role-select-btn"' in content
        assert f"**[{label}" in content
        assert f"]({route})" in content


class TestRcfDacGuestVisibilityAndLinks:
    def test_guest_notice_card_in_index_md(self):
        content = _read(INDEX_MD)
        assert 'id="guestNoticeCard"' in content
        assert "Authentication Required for Operational Modules" in content

    def test_js_app_updates_guest_notice_visibility(self):
        content = _read(JS_APP)
        assert "document.getElementById('guestNoticeCard')" in content
        assert "guestNotice.style.display = 'block'" in content
        assert "guestNotice.style.display = 'none'" in content

    def test_js_app_applies_my_role_visibility_during_initialisation(self):
        content = _read(JS_APP)
        assert "const initialRole = activeBtn ? activeBtn.getAttribute('data-role') : 'my-role'" in content
        assert "updateModuleViews(initialRole || 'my-role');" in content
        assert 'class="role-select-btn active" data-role="my-role"' in _read(INDEX_MD)

    def test_all_links_in_index_md_return_http_200(self, monkeypatch):
        import secrets
        monkeypatch.setenv("INVESTOR_JWT_SECRET", secrets.token_hex(32))

        from fastapi.testclient import TestClient
        from dca_service.web_app import app

        client = TestClient(app)
        res = client.get("/")
        assert res.status_code == 200

        hrefs = re.findall(r'href=[\"\'](.*?)[\"\']', res.text)
        assert len(hrefs) > 0, "Expected href links on index page"

        for href in hrefs:
            if href.startswith("http") or href.startswith("#"):
                continue
            r = client.get(href)
            assert r.status_code == 200, f"Link {href} returned HTTP {r.status_code}"

    @pytest.mark.parametrize(
        "liquid_link",
        [
            "{{ '/SUMMARY.html' | relative_url }}",
            '{{ "/docs/tutorials/web-application-user-guide.html" | relative_url }}',
            "{{'/docs/explanation/architecture-overview.html'|relative_url}}",
        ],
    )
    def test_markdown_renderer_resolves_relative_url_liquid_links(self, liquid_link):
        from dca_service.web_app import render_markdown_to_html

        expected_path = re.search(r"['\"]([^'\"]+)['\"]", liquid_link).group(1)

        rendered = render_markdown_to_html(f"[Documentation]({liquid_link})")

        assert rendered == f'<a href="{expected_path}">Documentation</a>'
        assert "{{" not in rendered

    def test_document_renderer_removes_frontmatter_and_wraps_content(self, tmp_path):
        from dca_service.web_app import _render_doc_file

        document = tmp_path / "guide.md"
        document.write_text(
            '---\ntitle: "Hidden metadata"\n---\n\n# Visible heading\n',
            encoding="utf-8",
        )

        response = _render_doc_file(document)
        rendered = response.body.decode("utf-8")

        assert response.status_code == 200
        assert "Hidden metadata" not in rendered
        assert "<h1>Visible heading</h1>" in rendered
        assert '<a href="/">&larr; Return to RCF & DAC Interactive Portal Homepage</a>' in rendered

    @pytest.mark.parametrize("document_name", ["SUMMARY", "README", "CHANGELOG", "HISTORY"])
    def test_allowlisted_root_document_routes_render_successfully(
        self, document_name, monkeypatch
    ):
        import secrets

        monkeypatch.setenv("INVESTOR_JWT_SECRET", secrets.token_hex(32))

        from fastapi.testclient import TestClient
        from dca_service.web_app import app

        response = TestClient(app).get(f"/{document_name}.html")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "Return to RCF & DAC Interactive Portal Homepage" in response.text

    @pytest.mark.parametrize("document_name", ["AGENTS", "pyproject", "not-present"])
    def test_root_document_route_rejects_non_allowlisted_files(
        self, document_name, monkeypatch
    ):
        import secrets

        monkeypatch.setenv("INVESTOR_JWT_SECRET", secrets.token_hex(32))

        from fastapi.testclient import TestClient
        from dca_service.web_app import app

        response = TestClient(app).get(f"/{document_name}.html")

        assert response.status_code == 404
        assert response.json() == {"detail": "Documentation page not found"}

    def test_docs_route_rejects_path_traversal_to_root_document(self):
        from fastapi import HTTPException
        from dca_service.web_app import serve_docs

        with pytest.raises(HTTPException) as exc_info:
            serve_docs("../README.html")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Documentation page not found"


class TestDefaultLayoutAuthenticationNavigation:
    @pytest.mark.parametrize(
        ("route", "top_label", "sidebar_label"),
        [
            ("/login", "[2] 🔐 Login", "🔐 System Login"),
            ("/user-management", "[3] 👥 User Mgmt", "👥 User Management"),
        ],
    )
    def test_authentication_routes_use_relative_url_in_both_navigation_areas(
        self, route, top_label, sidebar_label
    ):
        content = _read(DEFAULT_LAYOUT)
        liquid_href = f'href="{{{{ \'{route}\' | relative_url }}}}"'
        assert f"{liquid_href} {{% if page.url == \"{route}\" %}}class=\"active\"" in content
        assert f">{top_label}</a>" in content
        assert f"{liquid_href}>{sidebar_label}</a>" in content

    def test_top_navigation_numbers_remain_unique_and_sequential(self):
        content = _read(DEFAULT_LAYOUT)
        top_nav = re.search(
            r'<nav class="top-nav">(.*?)</nav>', content, flags=re.DOTALL
        )
        assert top_nav, "Expected a top navigation block"
        numbers = [int(value) for value in re.findall(r">\[(\d+)\]", top_nav.group(1))]
        assert numbers == list(range(1, 11))

    def test_login_precedes_user_management_in_top_navigation(self):
        content = _read(DEFAULT_LAYOUT)
        login_position = content.index("[2] 🔐 Login")
        user_management_position = content.index("[3] 👥 User Mgmt")
        proposal_position = content.index("[4] RCF Proposal")
        assert login_position < user_management_position < proposal_position


class TestOWASPAuthorizationFrameworkDoc:
    def test_file_exists(self):
        assert OWASP_AUTH_DOC.is_file()

    def test_okf_v02_frontmatter_present(self):
        content = _read(OWASP_AUTH_DOC)
        frontmatter = _extract_frontmatter_dict(content)
        assert frontmatter.get("okf_version") == "0.2"
        assert frontmatter.get("type") == "explanation"
        assert frontmatter.get("language") == "en-GB"

    def test_documents_owasp_recommendations(self):
        content = _read(OWASP_AUTH_DOC)
        assert "Enforce Least Privileges" in content
        assert "Deny by Default" in content
        assert "Superuser Startup Seeding & SQL-Only Password Reset Restriction" in content

    def test_adoption_matrix_contains_each_recommendation_exactly_once(self):
        content = _read(OWASP_AUTH_DOC)
        recommendation_numbers = re.findall(
            r"^\| \*\*(\d+)\*\* \|", content, flags=re.MULTILINE
        )
        assert recommendation_numbers == [str(number) for number in range(1, 12)]

    @pytest.mark.parametrize("claim", ["`exp`", "`iss`", "`aud`", "`role`"])
    def test_documents_required_jwt_claim_validation(self, claim):
        content = _read(OWASP_AUTH_DOC)
        assert claim in content

    def test_documents_constant_time_signature_verification(self):
        content = _read(OWASP_AUTH_DOC)
        assert "hmac.compare_digest(sig_b64, expected_sig)" in content
        assert "Invalid or forged token signature" in content

    def test_distinguishes_startup_seeding_from_runtime_password_reset(self):
        content = _read(OWASP_AUTH_DOC)
        assert "used exclusively for startup initialization" in content
        assert "seed_initial_accounts()" in content
        assert "/api/users/{username}/reset-password" in content
        assert "rejected with HTTP 403 Forbidden" in content


class TestSuperuserResetHowToDoc:
    def test_file_exists(self):
        assert SUPERUSER_RESET_DOC.is_file()

    def test_okf_v02_frontmatter_present(self):
        content = _read(SUPERUSER_RESET_DOC)
        frontmatter = _extract_frontmatter_dict(content)
        assert frontmatter.get("okf_version") == "0.2"
        assert frontmatter.get("type") == "how-to"
        assert frontmatter.get("language") == "en-GB"

    def test_contains_superuser_reset_sql_and_env_instructions(self):
        content = _read(SUPERUSER_RESET_DOC)
        assert "SUPERUSER_INITIAL_PASSWORD" in content
        assert "dca_sys_root" in content
        assert "get_or_create_initial_password" in content
        assert "POST /api/users" in content

    def test_documents_complete_environment_reseeding_sequence(self):
        content = _read(SUPERUSER_RESET_DOC)
        expected_steps = [
            "Add or update the environment variable `SUPERUSER_INITIAL_PASSWORD`",
            "Restart or redeploy the Web Service",
            'get_or_create_initial_password("superuser")',
            "seed_initial_accounts()",
            "SELECT username, role, email FROM users WHERE username = 'dca_sys_root'",
        ]
        positions = [content.index(step) for step in expected_steps]
        assert positions == sorted(positions)

    def test_explicitly_forbids_api_and_web_superuser_password_resets(self):
        content = _read(SUPERUSER_RESET_DOC)
        assert "password **CANNOT** be reset via public API endpoints or web interfaces" in content
        assert "HTTP 403 Forbidden" in content
        assert "No (API Blocked / Env Only)" in content

    def test_admin_creation_example_includes_authentication_and_expected_response(self):
        content = _read(SUPERUSER_RESET_DOC)
        assert '-H "Authorization: Bearer <your_superuser_jwt_token>"' in content
        assert '"username": "dca_admin_mgr"' in content
        assert '"role": "admin"' in content
        assert "HTTP 201 Created" in content

    @pytest.mark.parametrize(
        ("role", "username"),
        [
            ("superuser", "dca_sys_root"),
            ("admin", "dca_admin_mgr"),
            ("auditor", "dca_auditor_01"),
            ("operator", "dca_operator_01"),
            ("investor", "dca_investor_01"),
        ],
    )
    def test_role_capability_table_lists_each_default_account(self, role, username):
        content = _read(SUPERUSER_RESET_DOC)
        assert re.search(
            rf"^\| `{re.escape(role)}` \| `{re.escape(username)}` \|",
            content,
            flags=re.MULTILINE,
        )


class TestDocumentationIndexAndIgnoreRules:
    @pytest.mark.parametrize(
        ("title", "path"),
        [
            (
                "OWASP Authorization Framework Adoption & Access Control Architecture",
                "docs/explanation/owasp-authorization-framework.md",
            ),
            (
                "How to Reset Superuser Password via Environment Configuration & Create Initial Admin Users",
                "docs/how-to/reset-superuser-password-and-manage-users.md",
            ),
        ],
    )
    def test_summary_links_each_new_document_once(self, title, path):
        content = _read(SUMMARY_DOC)
        assert content.count(f"* [{title}]({path})") == 1

    def test_mypy_cache_is_ignored(self):
        entries = {
            line.strip()
            for line in _read(GITIGNORE).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        assert ".mypy_cache/" in entries


class TestConnectSupabaseOnRenderDoc:
    def test_file_exists(self):
        assert CONNECT_SUPABASE_DOC.is_file()

    def test_okf_v02_frontmatter_present(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert content.startswith("---")
        assert 'okf_version: "0.2"' in content
        assert 'type: "howto"' in content
        assert 'language: "en-GB"' in content

    def test_contains_direct_and_pooler_connection_strings(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "db.[YOUR-SUPABASE-PROJECT-REF].supabase.co:5432" in content
        assert "aws-0-ap-southeast-1.pooler.supabase.com:6543" in content
        assert "aws-0-ap-southeast-1.pooler.supabase.com:5432" in content

    def test_contains_supabase_cli_commands(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "tqudolprdioisrgqfyna" not in content
        assert "supabase login" in content
        assert "supabase init" in content
        assert "supabase link --project-ref [YOUR-SUPABASE-PROJECT-REF]" in content

    def test_contains_supabase_server_backend(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "sb_publishable_sLCOhqUPC4FPdaoTOemeTQ_3TVrRURv" not in content
        assert "npm install @supabase/server" in content
        assert "SUPABASE_URL=https://[YOUR-SUPABASE-PROJECT-REF].supabase.co" in content
        assert "SUPABASE_PUBLISHABLE_KEY=[YOUR-SUPABASE-PUBLISHABLE-KEY]" in content

    def test_contains_ssr_and_client_sdk(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "npm install @supabase/supabase-js @supabase/ssr" in content
        assert "createServerClient" in content
        assert "createBrowserClient" in content

    def test_contains_prisma_orm(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "npm install prisma --save-dev" in content
        assert "npx prisma init" in content
        assert "DATABASE_URL=" in content
        assert "DIRECT_URL=" in content

    def test_contains_mcp_gemini_setup(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "gemini mcp add -t http supabase" in content
        assert "/mcp auth supabase" in content

    def test_contains_agent_skills(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "npx skills add supabase/agent-skills" in content

    def test_contains_render_env_vars_and_secret_files(self):
        content = _read(CONNECT_SUPABASE_DOC)
        assert "Render Environment Variables" in content
        assert "Render Secret Files" in content
        assert "/etc/secrets/" in content

    def test_render_variable_table_documents_singular_and_plural_key_names(self):
        content = _read(CONNECT_SUPABASE_DOC)
        expected_rows = (
            (
                "`SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_PUBLISHABLE_KEYS`",
                "`sb_publishable_...`",
            ),
            (
                "`SUPABASE_SECRET_KEY` / `SUPABASE_SECRET_KEYS`",
                "`sb_secret_...`",
            ),
        )

        for key_names, example in expected_rows:
            row_pattern = rf"^\| {re.escape(key_names)} \| .* \| {re.escape(example)} \|$"
            assert re.search(row_pattern, content, flags=re.MULTILINE), (
                f"Render variable table is missing the documented aliases {key_names}"
            )

    def test_runtime_environment_example_includes_every_key_alias(self):
        content = _read(CONNECT_SUPABASE_DOC)
        expected_assignments = {
            "SUPABASE_PUBLISHABLE_KEY": "[YOUR-SUPABASE-PUBLISHABLE-KEY]",
            "SUPABASE_PUBLISHABLE_KEYS": "[YOUR-SUPABASE-PUBLISHABLE-KEY]",
            "SUPABASE_SECRET_KEY": "[YOUR-SUPABASE-SECRET-KEY]",
            "SUPABASE_SECRET_KEYS": "[YOUR-SUPABASE-SECRET-KEY]",
        }

        for variable, placeholder in expected_assignments.items():
            assignment = rf"^{variable}={re.escape(placeholder)}$"
            assert re.search(assignment, content, flags=re.MULTILINE), (
                f"Runtime environment example is missing {variable}"
            )

    def test_runtime_key_aliases_never_contain_live_credential_examples(self):
        content = _read(CONNECT_SUPABASE_DOC)
        live_credential_assignment = (
            r"^SUPABASE_(?:PUBLISHABLE|SECRET)_KEYS?="
            r"sb_(?:publishable|secret)_[^\s]+$"
        )

        assert not re.search(live_credential_assignment, content, flags=re.MULTILINE)
