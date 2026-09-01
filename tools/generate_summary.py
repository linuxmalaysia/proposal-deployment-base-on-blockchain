#!/usr/bin/env python3
"""
DSOM Documentation Index Generator (`generate_summary.py`).
Scans all documentation Markdown files under docs/ and root-level ledgers,
generating/updating SUMMARY.md with OKF v0.2 frontmatter.
"""

from datetime import UTC, datetime
from pathlib import Path

def get_markdown_title(file_path: Path) -> str:
    """Extract title from OKF frontmatter or first Markdown heading."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return file_path.stem.replace("-", " ").title()

    lines = content.splitlines()

    # Check for OKF YAML frontmatter title
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                break
            if ":" in lines[i]:
                key, val = lines[i].split(":", 1)
                if key.strip() == "title":
                    clean_val = val.strip().strip("'\"")
                    if clean_val:
                        return clean_val

    # Fallback to first H1 header
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()

    return file_path.stem.replace("-", " ").title()

def generate_summary(gen_datetime: datetime | None = None) -> None:
    """Generate SUMMARY.md index file with OKF v0.2 YAML frontmatter."""
    if gen_datetime is None:
        gen_datetime = datetime.now(UTC)

    timestamp_str = gen_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        stale_dt = gen_datetime.replace(year=gen_datetime.year + 1)
    except ValueError:
        stale_dt = gen_datetime.replace(year=gen_datetime.year + 1, day=28)
    stale_after_str = stale_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    repo_root = Path(__file__).parent.parent
    summary_path = repo_root / "SUMMARY.md"

    # Root ledgers
    root_files = [
        ("README.md", "Overview & Architecture"),
        ("CHANGELOG.md", "Changelog"),
        ("HISTORY.md", "Project History Ledger"),
    ]

    summary_lines = [
        "---",
        'okf_version: "0.2"',
        'type: "summary"',
        'title: "Documentation Index & Navigation Summary"',
        f'timestamp: "{timestamp_str}"',
        "topics:",
        '  - "summary"',
        '  - "index"',
        '  - "navigation"',
        '  - "docs"',
        'description: "Dynamically generated repository documentation index and navigation map."',
        'resource: "file:///SUMMARY.md"',
        "sources:",
        '  - "README.md"',
        'generated: "generate_summary.py"',
        "verified: true",
        'status: "approved"',
        f'stale_after: "{stale_after_str}"',
        'language: "en-GB"',
        "---",
        "",
        "# Documentation Index",
        "",
        "## Core Ledgers",
        "",
    ]

    for file_name, fallback_title in root_files:
        file_path = repo_root / file_name
        if file_path.exists():
            title = get_markdown_title(file_path) or fallback_title
            summary_lines.append(f"* [{title}]({file_name})")

    summary_lines.append("")
    summary_lines.append("## Documentation Sections")
    summary_lines.append("")

    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        subdirs = sorted([d for d in docs_dir.iterdir() if d.is_dir()])
        for subdir in subdirs:
            subdir_name = subdir.name.replace("-", " ").title()
            summary_lines.append(f"### {subdir_name}")
            summary_lines.append("")

            md_files = sorted(list(subdir.glob("**/*.md")))
            for md_file in md_files:
                rel_path = md_file.relative_to(repo_root).as_posix()
                title = get_markdown_title(md_file)
                summary_lines.append(f"* [{title}]({rel_path})")
            summary_lines.append("")

        loose_files = sorted([f for f in docs_dir.glob("*.md") if f.is_file()])
        if loose_files:
            summary_lines.append("### General Documentation")
            summary_lines.append("")
            for md_file in loose_files:
                rel_path = md_file.relative_to(repo_root).as_posix()
                title = get_markdown_title(md_file)
                summary_lines.append(f"* [{title}]({rel_path})")
            summary_lines.append("")

    content = "\n".join(summary_lines).strip() + "\n"
    summary_path.write_text(content, encoding="utf-8")
    print(f"✅ Generated {summary_path.relative_to(repo_root)}")

if __name__ == "__main__":
    generate_summary()
