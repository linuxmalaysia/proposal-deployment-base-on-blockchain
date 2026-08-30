---
okf_version: "0.2"
type: "howto"
title: "Multi-Platform Documentation Deployment Guide"
timestamp: "2026-08-25T00:00:00Z"
topics:
  - "hosting"
  - "gitlab-pages"
  - "gitbook"
  - "readthedocs"
  - "deployment"
description: "Deployment instructions for hosting documentation across GitLab Pages"
resource: "file:///docs/multi-platform-hosting.md"
sources:
  - ".gitlab-ci.yml"
  - ".gitbook.yaml"
  - ".readthedocs.yaml"
generated: "jules"
verified: true
status: "approved"
stale_after: "2027-08-25T00:00:00Z"
language: "en-GB"
---

# 🌐 Multi-Platform Documentation Deployment Guide

This project is configured to support seamless automated builds and deployments across all major documentation hosting platforms: **GitHub Pages**, **GitLab Pages**, **GitBook**, and **Read The Docs**.

---

## 🚀 1. GitHub Pages
- **Configuration:** `.github/workflows/jekyll-gh-pages.yml` and `_config.yml`.
- **Engine:** Jekyll 4 static site builder.
- **Trigger:** Automatic on push to `main` branch when Pages Source is set to **GitHub Actions** under repository settings.

## 🦊 2. GitLab Pages
- **Configuration:** `.gitlab-ci.yml`.
- **Engine:** Ruby 3.2 Jekyll runner building to `public/` directory.
- **Trigger:** Executes automatically in GitLab CI/CD pipelines targeting `main`.

## 📖 3. GitBook
- **Configuration:** `.gitbook.yaml`.
- **Structure:** Binds `README.md` as primary landing page and `SUMMARY.md` as the table of contents navigation tree.
- **Integration:** Import repository directly into GitBook Cloud space.

## 📚 4. Read The Docs (readthedocs.io)
- **Configuration:** `.readthedocs.yaml` (v2 spec) and `mkdocs.yml`.
- **Engine:** Python 3.12 with MkDocs & Material theme.
- **Trigger:** Webhook automated build on commit to default branch.

---

## 📑 Automated Summary Synchronization
All platforms leverage `tools/generate_summary.py` to auto-index Markdown files, ensuring newly created documents in `docs/` or root are automatically rendered in navigation trees without manual editing.
