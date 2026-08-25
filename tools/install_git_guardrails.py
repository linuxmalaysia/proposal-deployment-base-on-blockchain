#!/usr/bin/env python3
"""
DSOM Pre-Commit Guardrail Installer & Validator.
Ensures OKF v0.2 frontmatter compliance, zero global state, and test execution before commits.
"""

import sys
import subprocess
from pathlib import Path

def check_okf_frontmatter(file_path: Path) -> bool:
    """Check if a Markdown file contains valid OKF v0.2 frontmatter."""
    if not file_path.name.endswith(".md"):
        return True

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        print(f"❌ Guardrail violation: {file_path} missing leading '---' YAML frontmatter delimiter.")
        return False

    closing_index = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing_index = idx
            break

    if closing_index == -1:
        print(f"❌ Guardrail violation: {file_path} missing closing '---' YAML frontmatter delimiter.")
        return False

    frontmatter_block = "\n".join(lines[1:closing_index])
    if 'okf_version: "0.2"' not in frontmatter_block and "okf_version: '0.2'" not in frontmatter_block and "okf_version: 0.2" not in frontmatter_block:
        print(f"❌ Guardrail violation: {file_path} frontmatter missing exact okf_version '0.2'.")
        return False

    return True

def run_pre_commit_checks() -> int:
    """Execute DSOM pre-commit guardrail checks."""
    print("🛡️ Running DSOM Pre-Commit Guardrails...")

    repo_root = Path(__file__).parent.parent
    md_files = list(repo_root.glob("**/*.md"))

    failed = False
    for md_file in md_files:
        if any(ignored in md_file.parts for ignored in [".venv", ".git", ".pytest_cache"]):
            continue
        if not check_okf_frontmatter(md_file):
            failed = True

    if failed:
        print("❌ Pre-commit guardrails failed. Please fix OKF frontmatter issues.")
        return 1

    # Run tests via pytest
    print("🧪 Running Pytest test suite...")
    test_result = subprocess.run(["uv", "run", "pytest"], cwd=repo_root)
    if test_result.returncode != 0:
        print("❌ Pre-commit guardrails failed: Pytest run failed.")
        return test_result.returncode

    print("✅ All DSOM Pre-Commit Guardrails passed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(run_pre_commit_checks())
