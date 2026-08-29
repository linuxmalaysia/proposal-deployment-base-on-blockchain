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
    """Read file content from given path with UTF-8 encoding."""
    return path.read_text(encoding="utf-8")


class TestRcfDacJsAppEngine:
    def test_file_exists(self):
        """Verify JavaScript application engine file exists."""
        assert JS_APP.is_file()

    def test_handles_raw_amount_parsing_with_zero_support(self):
        """Verify JavaScript app validates numeric amounts and handles zero values."""
        content = _read(JS_APP)
        assert "Number.isFinite(rawAmount)" in content
        assert "rawAmount < 0" in content

    def test_uses_web_crypto_sha256_digest(self):
        """Verify JavaScript app utilises Web Crypto API for SHA-256 hashing."""
        content = _read(JS_APP)
        assert "crypto.subtle.digest('SHA-256'" in content

    def test_handles_local_storage_failure_gracefully(self):
        """Verify JavaScript app handles localStorage operations with error handling."""
        content = _read(JS_APP)
        assert "localStorage.setItem" in content
        assert "savedSuccessfully" in content

    def test_enforces_strict_cloverleaf_score_threshold(self):
        """Verify JavaScript app enforces 180-point Cloverleaf investment threshold."""
        content = _read(JS_APP)
        assert "if (total > 180)" in content


class TestRcfDacUserGuideDoc:
    def test_user_guide_file_exists(self):
        """Verify user guide documentation file exists."""
        assert USER_GUIDE_DOC.is_file()

    def test_okf_v02_frontmatter_present(self):
        """Verify user guide contains valid OKF v0.2 frontmatter with tutorial type."""
        content = _read(USER_GUIDE_DOC)
        assert content.startswith("---")
        assert 'okf_version: "0.2"' in content
        assert 'type: "tutorial"' in content
        assert 'language: "en-GB"' in content

    def test_documents_strict_score_threshold(self):
        """Verify user guide documents the 180-point investment qualification threshold."""
        content = _read(USER_GUIDE_DOC)
        assert "strictly exceeds **180 / 260 points**" in content or "scores > 180" in content


class TestRcfDacIndexMarkdown:
    def test_index_md_file_exists(self):
        """Verify index markdown homepage file exists."""
        assert INDEX_MD.is_file()

    def test_includes_file_upload_input(self):
        """Verify index page includes file upload input element for asset registration."""
        content = _read(INDEX_MD)
        assert '<input type="file" id="asset-file" required>' in content

    def test_includes_parse_block_html_options(self):
        """Verify index page includes markdown HTML parsing configuration directive."""
        content = _read(INDEX_MD)
        assert '{::options parse_block_html="true" /}' in content
