"""Tests for Google Antigravity-compatible Agent Skills suite in .agents/skills/."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
GENERATOR_SCRIPT = REPO_ROOT / "tools" / "create_antigravity_skills.py"

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

def test_all_skills_have_valid_skill_md_and_match_catalogue():
    # Import SKILLS catalogue from generator script
    import importlib.util
    spec = importlib.util.spec_from_file_location("create_antigravity_skills", GENERATOR_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    catalogue = mod.SKILLS

    expected_skill_names = sorted([s["dir"] for s in catalogue])
    actual_skill_dirs = sorted([d.name for d in SKILLS_DIR.iterdir() if d.is_dir()])

    assert actual_skill_dirs == expected_skill_names

    for skill in catalogue:
        skill_dir = SKILLS_DIR / skill["dir"]
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.is_file(), f"Missing SKILL.md in {skill_dir}"

        content = _read(skill_file)
        frontmatter = _frontmatter_block(content)

        # Validate mandatory OKF v0.2 fields
        for field in MANDATORY_OKF_V02_FIELDS:
            match = re.search(rf"(?m)^{field}:\s*(.+)$", frontmatter)
            assert match is not None, f"Missing mandatory field '{field}:' in {skill_file}"
            value = match.group(1).strip().strip("'\"")
            assert len(value) > 0, f"Empty value for mandatory field '{field}:' in {skill_file}"

        # Validate okf_version exact value
        okf_match = re.search(r"(?m)^okf_version:\s*['\"]?(0\.2)['\"]?$", frontmatter)
        assert okf_match is not None, f"Expected okf_version '0.2' in {skill_file}"

        # Validate Antigravity name field matches directory name
        name_match = re.search(r"(?m)^name:\s*['\"]?(.+?)['\"]?$", frontmatter)
        assert name_match is not None, f"Missing name field in {skill_file}"
        assert name_match.group(1).strip() == skill_dir.name, f"Name mismatch in {skill_file}"

        # Validate DSOM compliance footer
        expected_footer = (
            "---\n\n"
            "### Deep State of Mind (DSOM) AI Protocol Compliance\n\n"
            "* **Protocol Standard:** DSOM AI Protocol v2.4 & OKF v0.2 Specification\n"
            "* **Linguistic Standard:** UK English (`initialise`, `prioritise`, `segregated`)\n"
            "* **Execution Boundary:** Google Antigravity & Google Jules Synchronised Knowledge Matrix\n\n"
            "---"
        )
        assert expected_footer in content, f"DSOM footer missing or non-compliant in {skill_file}"
