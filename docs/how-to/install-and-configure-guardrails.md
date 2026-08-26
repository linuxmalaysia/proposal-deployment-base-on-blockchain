---
okf_version: "0.2"
type: "howto"
title: "How-To: Install and Configure Repository Guardrails and Documentation Tools"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---

# How-To: Install and Configure Repository Guardrails and Documentation Tools

This guide outlines step-by-step instructions for installing, configuring, and executing automated code guardrails and documentation index tools within the DCA/DAC repository.

---

## Prerequisites

- Python 3.12+ managed via `uv`.
- Git repository workspace checked out locally.

---

## 1. Running Pre-Commit Guardrails Manually

The repository provides `tools/install_git_guardrails.py` to enforce OKF v0.2 frontmatter validation, verify Markdown formatting, auto-regenerate `SUMMARY.md`, and execute the full pytest suite.

To run pre-commit guardrails manually:

```bash
uv run python tools/install_git_guardrails.py
```

### What Guardrails Validate:
1. **OKF v0.2 YAML Frontmatter:** Checks all Markdown files for valid `---` block containing exact `okf_version: "0.2"`.
2. **Documentation Index:** Automatically calls `tools/generate_summary.py` to keep `SUMMARY.md` in sync.
3. **Pytest Suite:** Runs `uv run pytest` to ensure zero broken domain tests or doc test regressions.

---

## 2. Generating the Documentation Index (`SUMMARY.md`)

When adding new Markdown documentation under `docs/` or updating root ledgers, update `SUMMARY.md` by executing:

```bash
uv run python tools/generate_summary.py
```

### Output:
```text
✅ Generated SUMMARY.md
```

`SUMMARY.md` dynamically groups documents into:
- **Core Ledgers** (`README.md`, `CHANGELOG.md`, `HISTORY.md`)
- **Documentation Sections** categorized by subdirectories (`docs/explanation/`, `docs/how-to/`, `docs/reference/`, `docs/tutorials/`)
- **General Documentation** for root-level files in `docs/`

---

## 3. Installing Git Pre-Commit Hooks

To install guardrails as an automated `.git/hooks/pre-commit` script so checks run automatically on every `git commit`:

1. Open or create `.git/hooks/pre-commit`:
   ```bash
   cat << 'EOF' > .git/hooks/pre-commit
   #!/bin/bash
   exec uv run python tools/install_git_guardrails.py
   EOF
   ```

2. Make the hook script executable:
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. Test the git hook:
   ```bash
   git status
   ```

---

## 4. Troubleshooting Guardrail Failures

### Issue: Missing `okf_version: "0.2"`
**Error:** `❌ Guardrail violation: docs/path/to/file.md frontmatter missing exact okf_version '0.2'.`
**Solution:** Ensure the top of the file contains valid YAML frontmatter:
```yaml
---
okf_version: "0.2"
type: "howto"
title: "Document Title"
created: "2026-08-25"
status: "verified"
language: "en-GB"
---
```

### Issue: Pytest Failures in Documentation Verification
**Error:** `❌ Pre-commit guardrails failed: Pytest run failed.`
**Solution:** Run `uv run pytest` directly to isolate failing assertion tests, fix the target text or code, and re-run guardrails.
