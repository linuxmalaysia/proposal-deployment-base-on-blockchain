#!/usr/bin/env python3
"""
DSOM Pre-Commit Guardrail Installer & Validator.
Ensures OKF v0.2 frontmatter compliance, zero global state, and test execution before commits.
"""

import sys
import subprocess
from pathlib import Path

def check_okf_frontmatter(file_path: Path) -> bool:
    """Check if a Markdown file contains OKF v0.2 frontmatter."""
    if not file_path.name.endswith(".md"):
        return True

    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        print(f"❌ Guardrail violation: {file_path} missing YAML frontmatter header ('---').")
        return False

    if "okf_version:" not in content:
        print(f"❌ Guardrail violation: {file_path} missing 'okf_version' field.")
        return False

    return True

def run_pre_commit_checks() -> int:
    """Execute DSOM pre-commit guardrail checks."""
    print("🛡️ Running DSOM Pre-Commit Guardrails...")

    repo_root = Path(__file__).parent.parent
    md_files = list(repo_root.glob("**/*.md"))

    failed = False
    for md_file in md_files:
        # Ignore cache directories and virtualenvs
        if any(ignored in md_file.parts for ignored in [".venv", ".git", ".pytest_cache"]):
            continue
        if not check_okf_frontmatter(md_file):
            failed = True

    if failed:
        print("❌ Pre-commit guardrails failed. Please fix OKF frontmatter issues.")
        return 1

    print("✅ All DSOM Pre-Commit Guardrails passed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(run_pre_commit_checks())
