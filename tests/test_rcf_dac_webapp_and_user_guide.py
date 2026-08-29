"""Unit tests for RCF/DAC Web Application Portal engine, assets, and user guide documentation."""

from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent

JS_APP = REPO_ROOT / "assets" / "js" / "rcf-dac-app.js"
CSS_STYLE = REPO_ROOT / "assets" / "css" / "style.css"
INDEX_MD = REPO_ROOT / "index.md"
USER_GUIDE_DOC = REPO_ROOT / "docs" / "tutorials" / "web-application-user-guide.md"
PROPOSAL_DOC = REPO_ROOT / "docs" / "explanation" / "research-commercialisation-fund-dac-proposal.md"


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
