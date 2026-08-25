"""Tests for tools/generate_summary.py (DSOM Documentation Index Generator)."""

import importlib.util
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parent.parent / "tools" / "generate_summary.py"


def _load_module():
    """Load tools/generate_summary.py as a fresh, isolated module instance.

    The module is not part of an importable package (no ``tools/__init__.py``),
    so it is loaded directly from its file path. Loading a fresh copy per test
    also makes it safe to monkeypatch ``__file__`` without affecting other tests.
    """
    spec = importlib.util.spec_from_file_location("generate_summary", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def gs_module():
    return _load_module()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestGetMarkdownTitle:
    def test_extracts_title_from_double_quoted_frontmatter(self, gs_module, tmp_path):
        file_path = tmp_path / "doc.md"
        _write(file_path, '---\nokf_version: "0.2"\ntitle: "My Document Title"\n---\n\n# Ignored Heading\n')
        assert gs_module.get_markdown_title(file_path) == "My Document Title"

    def test_extracts_title_from_single_quoted_frontmatter(self, gs_module, tmp_path):
        file_path = tmp_path / "doc.md"
        _write(file_path, "---\ntitle: 'Single Quoted Title'\n---\n\n# Ignored Heading\n")
        assert gs_module.get_markdown_title(file_path) == "Single Quoted Title"

    def test_title_value_with_embedded_colon_is_preserved(self, gs_module, tmp_path):
        file_path = tmp_path / "doc.md"
        _write(file_path, '---\ntitle: "DCA Service: Architecture"\n---\n\n# Ignored\n')
        assert gs_module.get_markdown_title(file_path) == "DCA Service: Architecture"

    def test_falls_back_to_first_h1_when_no_title_key_in_frontmatter(self, gs_module, tmp_path):
        file_path = tmp_path / "doc.md"
        _write(file_path, '---\nokf_version: "0.2"\n---\n\n# Fallback Heading\n\nBody text.\n')
        assert gs_module.get_markdown_title(file_path) == "Fallback Heading"

    def test_falls_back_to_first_h1_when_title_value_is_empty(self, gs_module, tmp_path):
        file_path = tmp_path / "doc.md"
        _write(file_path, '---\ntitle: ""\n---\n\n# Real Heading\n')
        assert gs_module.get_markdown_title(file_path) == "Real Heading"

    def test_extracts_title_from_h1_without_any_frontmatter(self, gs_module, tmp_path):
        file_path = tmp_path / "plain-doc.md"
        _write(file_path, "# A Plain Heading\n\nSome content.\n")
        assert gs_module.get_markdown_title(file_path) == "A Plain Heading"

    def test_falls_back_to_filename_when_no_frontmatter_or_heading(self, gs_module, tmp_path):
        file_path = tmp_path / "no-heading-doc.md"
        _write(file_path, "Just some body text with no heading at all.\n")
        assert gs_module.get_markdown_title(file_path) == "No Heading Doc"

    def test_falls_back_to_filename_when_file_cannot_be_read(self, gs_module, tmp_path):
        missing_path = tmp_path / "does-not-exist.md"
        assert gs_module.get_markdown_title(missing_path) == "Does Not Exist"

    def test_missing_closing_delimiter_still_finds_heading_fallback(self, gs_module, tmp_path):
        # No closing '---' delimiter and no 'title:' key anywhere in the file;
        # the function should still recover via the H1 fallback scan.
        file_path = tmp_path / "doc.md"
        _write(file_path, '---\nokf_version: "0.2"\n\n# Recovered Heading\n')
        assert gs_module.get_markdown_title(file_path) == "Recovered Heading"


class TestGenerateSummary:
    def test_generates_summary_with_root_ledgers_and_docs_sections(self, gs_module, tmp_path, monkeypatch, capsys):
        # Point the module's notion of "repo root" at an isolated tmp_path so this
        # test never touches the real repository's SUMMARY.md or other files.
        monkeypatch.setattr(gs_module, "__file__", str(tmp_path / "tools" / "generate_summary.py"))

        _write(tmp_path / "README.md", '---\ntitle: "Overview Doc"\n---\n\n# Ignored\n')
        _write(tmp_path / "CHANGELOG.md", "# Changelog Heading\n")
        # HISTORY.md intentionally omitted to verify it is skipped when absent.

        _write(
            tmp_path / "docs" / "explanation" / "architecture-overview.md",
            '---\ntitle: "Architecture Overview"\n---\n\n# Ignored\n',
        )
        _write(tmp_path / "docs" / "loose-guide.md", "# Loose Guide Heading\n")

        gs_module.generate_summary()

        summary_path = tmp_path / "SUMMARY.md"
        assert summary_path.exists()
        content = summary_path.read_text(encoding="utf-8")

        # SUMMARY.md's own OKF frontmatter header
        assert content.startswith("---\n")
        assert 'okf_version: "0.2"' in content
        assert 'title: "Documentation Index & Navigation Summary"' in content

        # Root ledgers section
        assert "## Core Ledgers" in content
        assert "* [Overview Doc](README.md)" in content
        assert "* [Changelog Heading](CHANGELOG.md)" in content
        assert "HISTORY.md" not in content

        # Documentation sections, generated from docs/ subdirectories and loose files
        assert "## Documentation Sections" in content
        assert "### Explanation" in content
        assert "* [Architecture Overview](docs/explanation/architecture-overview.md)" in content
        assert "### General Documentation" in content
        assert "* [Loose Guide Heading](docs/loose-guide.md)" in content

        captured = capsys.readouterr()
        assert "Generated SUMMARY.md" in captured.out

    def test_generate_summary_with_no_docs_dir_or_ledgers(self, gs_module, tmp_path, monkeypatch):
        monkeypatch.setattr(gs_module, "__file__", str(tmp_path / "tools" / "generate_summary.py"))

        gs_module.generate_summary()

        content = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
        lines = content.splitlines()

        assert "## Core Ledgers" in lines
        assert "## Documentation Sections" in lines

        core_idx = lines.index("## Core Ledgers")
        docs_idx = lines.index("## Documentation Sections")
        between = lines[core_idx + 1:docs_idx]
        # No ledger bullets since no README/CHANGELOG/HISTORY files exist.
        assert all(not line.strip() for line in between)
        # Documentation Sections header is the last content line (no docs/ dir present).
        assert lines[-1] == "## Documentation Sections"

    def test_generate_summary_overwrites_existing_summary_file(self, gs_module, tmp_path, monkeypatch):
        monkeypatch.setattr(gs_module, "__file__", str(tmp_path / "tools" / "generate_summary.py"))
        summary_path = tmp_path / "SUMMARY.md"
        summary_path.write_text("STALE CONTENT THAT SHOULD BE REPLACED", encoding="utf-8")

        gs_module.generate_summary()

        content = summary_path.read_text(encoding="utf-8")
        assert "STALE CONTENT" not in content
        assert "# Documentation Index" in content

    def test_generate_summary_skips_docs_subdir_with_no_markdown_files(self, gs_module, tmp_path, monkeypatch):
        monkeypatch.setattr(gs_module, "__file__", str(tmp_path / "tools" / "generate_summary.py"))
        # An empty subdirectory under docs/ should still get a header, but with no bullets.
        (tmp_path / "docs" / "empty-section").mkdir(parents=True)

        gs_module.generate_summary()

        content = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
        assert "### Empty Section" in content