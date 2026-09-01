"""Tests for Google Antigravity-compatible Agent Skills suite in .agents/skills/."""

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"

MANDATORY_OKF_V02_FIELDS = [
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
]

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def _frontmatter_block(content: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    assert match, "Expected file to start with a '---' delimited YAML frontmatter block"
    return match.group(1)

def test_skills_directory_exists_and_not_empty():
    assert SKILLS_DIR.is_dir()
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    assert len(skill_dirs) >= 38

def test_all_skills_have_valid_skill_md():
    skill_dirs = [d for d in SKILLS_DIR.iterdir() if d.is_dir()]
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.is_file(), f"Missing SKILL.md in {skill_dir}"
        content = _read(skill_file)
        frontmatter = _frontmatter_block(content)

        # Verify all mandatory OKF v0.2 fields exist
        for field in MANDATORY_OKF_V02_FIELDS:
            assert re.search(rf"(?m)^{field}:", frontmatter), (
                f"Missing mandatory OKF v0.2 field '{field}:' in {skill_file}"
            )

        # Verify Antigravity name field
        assert re.search(r"(?m)^name:", frontmatter), f"Missing 'name:' in {skill_file}"

        # Verify DSOM footer presence
        assert "Deep State of Mind (DSOM) AI Protocol Compliance" in content
