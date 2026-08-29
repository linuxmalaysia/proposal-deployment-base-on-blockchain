---
okf_version: '0.2'
type: howto
title: GitHub Pages Automated Deployment & 404 Troubleshooting Guide
timestamp: '2026-08-25T00:00:00Z'
topics:
- github-pages
- jekyll
- deployment
- troubleshooting
- ci-cd
description: Step-by-step guide for configuring Jekyll GitHub Pages deployment and
  resolving subpath 404 assets.
resource: file:///docs/github-pages-setup.md
sources:
- _config.yml
- .github/workflows/jekyll-gh-pages.yml
generated: jules
verified: true
status: approved
stale_after: '2027-08-25T00:00:00Z'
language: en-GB
---
# 🚀 GitHub Pages Automated Deployment & Troubleshooting Guide

This guide details how to configure GitHub Pages for automatic build and deployment using the official GitHub Actions Jekyll workflow (`jekyll-gh-pages.yml`), and how to resolve common 404 File Not Found errors.

---

## 🛠️ Step 1: Configuring GitHub Pages Repository Settings

To ensure GitHub Pages builds and deploys automatically on every push to `main`:

1. Open your GitHub repository in your web browser.
2. Click on **Settings** in the top repository menu bar.
3. In the left sidebar, select **Pages** under the *Code and automation* section.
4. Under **Build and deployment**:
   - Locate the **Source** dropdown menu.
   - Change the selection from **Deploy from a branch** to **GitHub Actions**.
5. Save your settings.

Once set to **GitHub Actions**, GitHub will automatically execute `.github/workflows/jekyll-gh-pages.yml` whenever changes are pushed to `main`.

---

## ❓ Why the 404 Error Occurred & How It Is Solved

### Root Causes of 404 Errors:
1. **Repository Subpath `baseurl` Misconfiguration:** When hosted under a repository subpath (e.g. `https://linuxmalaysia.github.io/proposal-deployment-base-on-blockchain/`), an empty `baseurl: ""` setting in `_config.yml` causes assets (`style.css`, `theme-toggle.js`, `favicon.ico`) to be fetched from the domain root (`https://linuxmalaysia.github.io/assets/...`) instead of the repository subpath, triggering 404 Not Found errors.
2. **Missing Root `index.md` / `index.html`:** GitHub Pages default web server looks for an `index.html` or `index.md` file at the repository root. Without one, accessing the root URL produces a 404 response.
3. **Pages Source Misconfiguration:** If the Pages source is set to a legacy branch (e.g., `gh-pages` or `main / (root)`) without GitHub Actions enabled, GitHub does not execute custom build workflows or pre-install dependencies.
4. **Missing `_config.yml` Includes:** Standard Jekyll excludes non-standard root files. Custom root ledgers (`README.md`, `CHANGELOG.md`, `SUMMARY.md`, `HISTORY.md`, `favicon.ico`) must be explicitly declared in `_config.yml`.

### Solved Implementation:

- Configured `baseurl: "/proposal-deployment-base-on-blockchain"` and `url: "https://linuxmalaysia.github.io"` in `_config.yml`.
- Updated `_layouts/default.html` and `index.md` to use Liquid `{{ 'path' | relative_url }}` filter for CSS, JS scripts, favicons, and navigation links.
- Created root `favicon.ico` and `assets/favicon.ico` to eliminate favicon 404 console errors.
- Created root `index.md` with laboratory template layout.
- Added `_config.yml` explicitly instructing Jekyll to process `docs/` and root ledgers.
- Updated `.github/workflows/jekyll-gh-pages.yml` to automatically run `python tools/generate_summary.py` before Jekyll compilation.

---

## 🔄 Automatic Markdown Indexing

When you add new `.md` files under `docs/` or at the root level:
- The `tools/generate_summary.py` script automatically scans the repository and updates `SUMMARY.md`.
- DSOM pre-commit guardrails (`tools/install_git_guardrails.py`) verify frontmatter and update the summary before every git commit.
- Jekyll Liquid template automatically renders all discovered Markdown pages into static HTML with full laboratory navigation headers and sidebars.
