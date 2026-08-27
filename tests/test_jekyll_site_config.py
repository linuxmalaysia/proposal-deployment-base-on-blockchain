"""Tests for the GitHub Pages / Jekyll subpath deployment fix.

Scope: this PR reconfigured the Jekyll site so it renders correctly when
served from a repository subpath (``https://linuxmalaysia.github.io/
proposal-deployment-base-on-blockchain/``) instead of a domain root. It:

- Set ``baseurl``/``url`` in ``_config.yml`` and added ``favicon.ico`` to the
  ``include`` list.
- Replaced hard-coded ``{{ site.baseurl }}/...`` link/script/href
  concatenation in ``_layouts/default.html`` and ``index.md`` with the
  Liquid ``relative_url`` filter, and added favicon ``<link>`` tags.
- Added root ``favicon.ico`` and ``assets/favicon.ico`` binary assets.
- Documented the root cause and fix in ``docs/github-pages-setup.md``.

These tests validate the *content* of the changed files rather than
executing a full Jekyll/Liquid build (no Ruby/Jekyll toolchain is available
in this Python-only test environment). No PyYAML dependency is available
either, so ``_config.yml`` is validated with targeted text assertions,
consistent with the text-based parsing style used elsewhere in this
project's test suite (see ``test_generate_summary.py``).
"""

import re
import struct
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

CONFIG_YML = REPO_ROOT / "_config.yml"
DEFAULT_LAYOUT = REPO_ROOT / "_layouts" / "default.html"
INDEX_MD = REPO_ROOT / "index.md"
GITHUB_PAGES_DOC = REPO_ROOT / "docs" / "github-pages-setup.md"
ROOT_FAVICON = REPO_ROOT / "favicon.ico"
ASSETS_FAVICON = REPO_ROOT / "assets" / "favicon.ico"

EXPECTED_BASEURL = "/proposal-deployment-base-on-blockchain"
EXPECTED_URL = "https://linuxmalaysia.github.io"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestConfigYml:
    def test_baseurl_set_to_repository_subpath(self):
        content = _read(CONFIG_YML)
        assert f'baseurl: "{EXPECTED_BASEURL}"' in content

    def test_url_set_to_pages_domain(self):
        content = _read(CONFIG_YML)
        assert f'url: "{EXPECTED_URL}"' in content

    def test_baseurl_is_no_longer_empty(self):
        # Regression guard: the 404 bug this PR fixes was caused by an
        # empty baseurl when the site is hosted under a repository subpath.
        content = _read(CONFIG_YML)
        assert 'baseurl: ""' not in content

    def test_url_is_no_longer_empty(self):
        content = _read(CONFIG_YML)
        assert 'url: ""' not in content

    def test_favicon_ico_declared_in_include_list(self):
        content = _read(CONFIG_YML)
        include_match = re.search(r"^include:\n((?:\s+-\s.*\n?)+)", content, re.MULTILINE)
        assert include_match, "Expected an 'include:' block in _config.yml"
        include_block = include_match.group(1)
        entries = [line.strip().lstrip("- ").strip() for line in include_block.splitlines() if line.strip()]
        assert "favicon.ico" in entries

    def test_include_list_retains_preexisting_root_ledgers(self):
        # Ensure adding favicon.ico did not clobber the other required includes.
        content = _read(CONFIG_YML)
        include_match = re.search(r"^include:\n((?:\s+-\s.*\n?)+)", content, re.MULTILINE)
        entries = [line.strip().lstrip("- ").strip() for line in include_match.group(1).splitlines() if line.strip()]
        for expected in ("README.md", "CHANGELOG.md", "SUMMARY.md", "HISTORY.md", "docs"):
            assert expected in entries


class TestDefaultLayoutTemplate:
    def test_no_stylesheet_reference_uses_raw_site_baseurl_concatenation(self):
        content = _read(DEFAULT_LAYOUT)
        assert '{{ site.baseurl }}/assets/css/style.css' not in content

    def test_no_script_reference_uses_raw_site_baseurl_concatenation(self):
        content = _read(DEFAULT_LAYOUT)
        assert '{{ site.baseurl }}/assets/js/theme-toggle.js' not in content

    def test_stylesheet_uses_relative_url_filter(self):
        content = _read(DEFAULT_LAYOUT)
        assert "{{ '/assets/css/style.css' | relative_url }}" in content

    def test_script_uses_relative_url_filter(self):
        content = _read(DEFAULT_LAYOUT)
        assert "{{ '/assets/js/theme-toggle.js' | relative_url }}" in content

    def test_favicon_icon_link_present(self):
        content = _read(DEFAULT_LAYOUT)
        assert '<link rel="icon" type="image/x-icon" href="{{ \'/favicon.ico\' | relative_url }}">' in content

    def test_favicon_shortcut_icon_link_present(self):
        content = _read(DEFAULT_LAYOUT)
        assert '<link rel="shortcut icon" type="image/x-icon" href="{{ \'/favicon.ico\' | relative_url }}">' in content

    @pytest.mark.parametrize(
        "expected_target",
        [
            "/",
            "/README.html",
            "/CHANGELOG.html",
            "/HISTORY.html",
            "/SUMMARY.html",
            "/docs/explanation/architecture-overview.html",
            "/docs/reference/implementation-patterns.html",
            "/docs/explanation/challenges-and-opportunities.html",
            "/docs/github-pages-setup.html",
            "/docs/multi-platform-hosting.html",
        ],
    )
    def test_navigation_link_uses_relative_url_filter(self, expected_target):
        content = _read(DEFAULT_LAYOUT)
        assert f"{{{{ '{expected_target}' | relative_url }}}}" in content

    def test_no_remaining_raw_site_baseurl_href_concatenation(self):
        # After the fix, every href/src in the layout should go through the
        # relative_url filter rather than manual `{{ site.baseurl }}/...` concatenation.
        content = _read(DEFAULT_LAYOUT)
        assert "site.baseurl" not in content

    def test_page_url_conditionals_still_reference_absolute_paths(self):
        # The active-nav-link comparisons compare against page.url (which Jekyll
        # always resolves without baseurl), so these should remain untouched.
        content = _read(DEFAULT_LAYOUT)
        assert 'page.url == "/"' in content
        assert 'page.url == "/README.html"' in content


class TestIndexMarkdown:
    @pytest.mark.parametrize(
        "expected_target",
        [
            "/docs/explanation/architecture-overview.html",
            "/docs/explanation/challenges-and-opportunities.html",
            "/docs/reference/implementation-patterns.html",
            "/SUMMARY.html",
        ],
    )
    def test_card_link_uses_relative_url_filter(self, expected_target):
        content = _read(INDEX_MD)
        assert f"{{{{ '{expected_target}' | relative_url }}}}" in content

    def test_no_remaining_raw_site_baseurl_reference(self):
        content = _read(INDEX_MD)
        assert "site.baseurl" not in content

    def test_frontmatter_declares_default_layout(self):
        content = _read(INDEX_MD)
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        assert frontmatter_match, "index.md must start with YAML frontmatter"
        assert "layout: default" in frontmatter_match.group(1) or 'layout: "default"' in frontmatter_match.group(1)


class TestFaviconAssets:
    @pytest.mark.parametrize("favicon_path", [ROOT_FAVICON, ASSETS_FAVICON])
    def test_favicon_file_exists(self, favicon_path):
        assert favicon_path.is_file(), f"{favicon_path} should exist"

    @pytest.mark.parametrize("favicon_path", [ROOT_FAVICON, ASSETS_FAVICON])
    def test_favicon_file_is_not_empty(self, favicon_path):
        assert favicon_path.stat().st_size > 0

    @pytest.mark.parametrize("favicon_path", [ROOT_FAVICON, ASSETS_FAVICON])
    def test_favicon_has_valid_ico_header(self, favicon_path):
        # ICO file format header: 2-byte reserved field (must be 0), followed
        # by a 2-byte image type field (1 == icon), per the ICO spec.
        header = favicon_path.read_bytes()[:6]
        assert len(header) == 6
        reserved, image_type, _image_count = struct.unpack("<HHH", header)
        assert reserved == 0
        assert image_type == 1

    def test_root_and_assets_favicon_are_identical(self):
        # Both copies are expected to serve the same icon regardless of
        # which relative_url-resolved path a page requests it from.
        assert ROOT_FAVICON.read_bytes() == ASSETS_FAVICON.read_bytes()


class TestGithubPagesSetupDoc:
    def test_documents_baseurl_subpath_root_cause(self):
        content = _read(GITHUB_PAGES_DOC)
        assert "baseurl" in content
        assert EXPECTED_URL in content or "linuxmalaysia.github.io" in content

    def test_documents_configured_baseurl_and_url_values_match_config_yml(self):
        # Guard against the documentation drifting out of sync with the
        # actual _config.yml values it describes.
        doc_content = _read(GITHUB_PAGES_DOC)
        config_content = _read(CONFIG_YML)
        assert f'baseurl: "{EXPECTED_BASEURL}"' in doc_content
        assert f'baseurl: "{EXPECTED_BASEURL}"' in config_content
        assert f'url: "{EXPECTED_URL}"' in doc_content
        assert f'url: "{EXPECTED_URL}"' in config_content

    def test_documents_relative_url_liquid_filter_fix(self):
        content = _read(GITHUB_PAGES_DOC)
        assert "relative_url" in content

    def test_documents_favicon_assets_creation(self):
        content = _read(GITHUB_PAGES_DOC)
        assert "favicon.ico" in content

    def test_frontmatter_declares_howto_type(self):
        content = _read(GITHUB_PAGES_DOC)
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        assert frontmatter_match, "docs/github-pages-setup.md must start with YAML frontmatter"
        assert "type: howto" in frontmatter_match.group(1) or 'type: "howto"' in frontmatter_match.group(1)
