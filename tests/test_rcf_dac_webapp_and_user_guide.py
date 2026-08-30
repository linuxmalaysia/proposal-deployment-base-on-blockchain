"""Unit tests for RCF/DAC Web Application Portal engine, assets, and user guide documentation."""

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent

JS_APP = REPO_ROOT / "assets" / "js" / "rcf-dac-app.js"
CSS_STYLE = REPO_ROOT / "assets" / "css" / "style.css"
INDEX_MD = REPO_ROOT / "index.md"
USER_GUIDE_DOC = REPO_ROOT / "docs" / "tutorials" / "web-application-user-guide.md"
PROPOSAL_DOC = REPO_ROOT / "docs" / "explanation" / "research-commercialisation-fund-dac-proposal.md"
CONNECT_SUPABASE_DOC = REPO_ROOT / "docs" / "how-to" / "connect-supabase-postgresql-on-render.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


class TestRcfDacIndexMarkdown:
    def test_index_md_file_exists(self):
        assert INDEX_MD.is_file()

    def test_includes_file_upload_input(self):
        content = _read(INDEX_MD)
        assert '<input type="file" id="asset-file" required>' in content

    def test_includes_parse_block_html_options(self):
        content = _read(INDEX_MD)
        assert '{::options parse_block_html="true" /}' in content


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
        assert "supabase login" in content
        assert "supabase init" in content
        assert "supabase link --project-ref [YOUR-SUPABASE-PROJECT-REF]" in content

    def test_contains_supabase_server_backend(self):
        content = _read(CONNECT_SUPABASE_DOC)
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
